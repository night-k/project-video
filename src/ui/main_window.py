import os
import sys
import shutil
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QTextCursor
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QProgressBar,
    QTextEdit,
    QButtonGroup,
    QRadioButton,
    QCheckBox,
    QScrollArea,
    QSizePolicy,
    QMessageBox,
    QSlider,
    QDoubleSpinBox,
)

from video_processor import VideoProcessor
from ui.widgets import Card, PathPicker, StrengthCard, SectionHeader


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AB 视频去重工具")
        self.setMinimumSize(640, 780)
        self.resize(680, 860)

        try:
            self.setWindowIcon(QIcon(":/logo.png"))
        except Exception:
            pass

        self.video_a_path = ""
        self.video_b_path = ""
        self.output_path = ""
        self.temp_dir = os.path.join(os.path.expanduser("~"), ".ab_video_dedup_temp")
        os.makedirs(self.temp_dir, exist_ok=True)

        self.processor = None
        self._build_ui()
        self._wire_signals()
        self._update_ready_state()
        sys.excepthook = self._except_hook

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.NoFrame)

        root = QWidget()
        root.setObjectName("root")
        scroll.setWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # —— 顶栏 ——
        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title = QLabel("AB 视频去重")
        title.setObjectName("app_title")
        subtitle = QLabel("高帧率抽帧混合 · 保留 A 音轨")
        subtitle.setObjectName("app_subtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()
        self.status_chip = QLabel("等待配置")
        self.status_chip.setObjectName("status_chip")
        self.status_chip.setProperty("status", "idle")
        header.addWidget(self.status_chip, alignment=Qt.AlignTop)
        layout.addLayout(header)

        # —— 输入文件 ——
        files_card = Card()
        files_card.add_widget(SectionHeader("输入与输出", "选择内容视频、素材视频及导出位置"))
        layout.addWidget(files_card)

        files_inner = QVBoxLayout()
        files_inner.setSpacing(14)

        self.picker_a = PathPicker(
            "A", "field_badge", "内容视频", "要发布的目标画面"
        )
        self.picker_b = PathPicker(
            "B", "field_badge_b", "素材视频", "无关视频，用于帧填充"
        )
        self.picker_out = PathPicker(
            "OUT", "field_badge_out", "输出文件", "处理完成后保存的路径"
        )
        files_inner.addWidget(self.picker_a)
        files_inner.addWidget(self.picker_b)
        files_inner.addWidget(self.picker_out)
        files_card.add_layout(files_inner)

        # —— 去重强度 ——
        strength_card = Card()
        strength_card.add_widget(
            SectionHeader("去重强度", "帧率越高，B 帧占比越大，处理耗时越长")
        )

        self.radio_60 = QRadioButton()
        self.radio_120 = QRadioButton()
        self.radio_240 = QRadioButton()
        self.radio_60.setChecked(True)

        group = QButtonGroup(self)
        for r in (self.radio_60, self.radio_120, self.radio_240):
            group.addButton(r)

        strength_row = QHBoxLayout()
        strength_row.setSpacing(10)
        self.card_60 = StrengthCard("50%", "60 fps", "DY + TK", self.radio_60)
        self.card_120 = StrengthCard("75%", "120 fps", "仅 TK", self.radio_120)
        self.card_240 = StrengthCard("87.5%", "240 fps", "仅 TK", self.radio_240)
        for c in (self.card_60, self.card_120, self.card_240):
            c.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            strength_row.addWidget(c, 1)
        strength_card.add_layout(strength_row)
        self.card_60.set_selected(True)
        layout.addWidget(strength_card)

        # —— TikTok 手机端专属 ——
        tk_card = Card()
        tk_col = QVBoxLayout()
        tk_col.setSpacing(4)
        self.tiktok_checkbox = QCheckBox("转换为 TikTok 手机端专属格式")
        self.tiktok_checkbox.setObjectName("gpu_check")
        self.tiktok_checkbox.setToolTip(
            "勾选后，输出视频仅 TikTok 手机端可正常解码播放。\n"
            "PC 端播放器将显示色彩异常/黑白画面且无音频。\n"
            "原理：HEVC 10bit + BT.2020 超广色域 + 剥离音频轨。"
        )
        tk_hint = QLabel(
            "效果：TikTok 移动端正常播放 · PC 端偏色/黑白 + 无声"
        )
        tk_hint.setObjectName("section_hint")
        tk_hint.setWordWrap(True)
        tk_col.addWidget(self.tiktok_checkbox)
        tk_col.addWidget(tk_hint)
        tk_card.add_layout(tk_col)
        layout.addWidget(tk_card)

        # —— 帧扰动 + 音频扰动 ——
        perturb_card = Card()
        perturb_col = QVBoxLayout()
        perturb_col.setSpacing(6)

        self.perturb_checkbox = QCheckBox("启用帧扰动（对抗平台压缩还原）")
        self.perturb_checkbox.setObjectName("gpu_check")
        self.perturb_checkbox.setChecked(True)
        self.perturb_checkbox.setToolTip(
            "对 A 帧做肉眼不可见的修改：微噪点 + 色温偏移 + 微缩放平移\n"
            "使平台即使降帧也无法还原原始 A 帧内容"
        )
        perturb_hint = QLabel(
            "原理：微噪点(2%) + 色温随机偏移 + 1.01x 微缩放 + A/B 帧混合"
        )
        perturb_hint.setObjectName("section_hint")
        perturb_hint.setWordWrap(True)
        perturb_col.addWidget(self.perturb_checkbox)
        perturb_col.addWidget(perturb_hint)

        # 混合比例
        blend_row = QHBoxLayout()
        blend_label = QLabel("A/B 混合比例 (A 权重)")
        blend_label.setObjectName("section_hint")
        self.blend_spin = QDoubleSpinBox()
        self.blend_spin.setRange(0.50, 0.95)
        self.blend_spin.setSingleStep(0.05)
        self.blend_spin.setValue(0.80)
        self.blend_spin.setSuffix("")
        self.blend_spin.setDecimals(2)
        blend_row.addWidget(blend_label)
        blend_row.addStretch()
        blend_row.addWidget(self.blend_spin)
        perturb_col.addLayout(blend_row)

        # 音频速度
        audio_row = QHBoxLayout()
        audio_label = QLabel("音频速度因子")
        audio_label.setObjectName("section_hint")
        self.audio_speed_spin = QDoubleSpinBox()
        self.audio_speed_spin.setRange(0.90, 1.10)
        self.audio_speed_spin.setSingleStep(0.01)
        self.audio_speed_spin.setValue(0.99)
        self.audio_speed_spin.setPrefix("x")
        audio_row.addWidget(audio_label)
        audio_row.addStretch()
        audio_row.addWidget(self.audio_speed_spin)
        perturb_col.addLayout(audio_row)

        perturb_card.add_layout(perturb_col)
        layout.addWidget(perturb_card)

        # —— 性能 ——
        perf_card = Card()
        perf_row = QHBoxLayout()
        perf_label = QLabel("性能")
        perf_label.setObjectName("section_title")
        self.gpu_checkbox = QCheckBox("启用 NVIDIA GPU 加速（NVENC）")
        self.gpu_checkbox.setObjectName("gpu_check")
        if sys.platform == 'darwin':
            self.gpu_checkbox.setEnabled(False)
            self.gpu_checkbox.setToolTip("macOS 无 NVIDIA 显卡，请使用 CPU 模式")
        perf_row.addWidget(perf_label)
        perf_row.addStretch()
        perf_row.addWidget(self.gpu_checkbox)
        perf_card.add_layout(perf_row)

        guard_col = QVBoxLayout()
        guard_col.setSpacing(4)
        self.guard_checkbox = QCheckBox("启用播放保护（模拟器限制 · 实验性）")
        self.guard_checkbox.setObjectName("gpu_check")
        self.guard_checkbox.setToolTip(
            "处理后追加 HEVC 硬解友好编码与保护元数据，\n"
            "提高真机硬解、降低模拟器/软解播放成功率。\n"
            "非 Widevine 商业 DRM；部分老旧手机可能不兼容 10-bit HEVC。"
        )
        guard_hint = QLabel(
            "原理：HEVC Main/Main10 + hvc1 标签 + 保护元数据，引导移动端硬件解码"
        )
        guard_hint.setObjectName("section_hint")
        guard_hint.setWordWrap(True)
        guard_col.addWidget(self.guard_checkbox)
        guard_col.addWidget(guard_hint)
        perf_card.add_layout(guard_col)
        layout.addWidget(perf_card)

        # —— 运行按钮 ——
        self.btn_run = QPushButton("开始处理")
        self.btn_run.setObjectName("primary_btn")
        self.btn_run.setEnabled(False)
        self.btn_run.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.btn_run)

        # —— 进度与日志 ——
        log_card = Card()
        progress_header = QHBoxLayout()
        progress_title = QLabel("处理进度")
        progress_title.setObjectName("section_title")
        self.label_progress_pct = QLabel("0%")
        self.label_progress_pct.setObjectName("progress_pct")
        progress_header.addWidget(progress_title)
        progress_header.addStretch()
        progress_header.addWidget(self.label_progress_pct)
        log_card.add_layout(progress_header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        log_card.add_widget(self.progress_bar)

        log_card.add_widget(SectionHeader("运行日志", ""))
        self.log_console = QTextEdit()
        self.log_console.setObjectName("log_console")
        self.log_console.setReadOnly(True)
        self.log_console.setMinimumHeight(200)
        self.log_console.setLineWrapMode(QTextEdit.WidgetWidth)
        log_card.add_widget(self.log_console)
        layout.addWidget(log_card)

        footer = QLabel("仅供技术研究 · 请遵守平台规则与版权法规")
        footer.setObjectName("section_hint")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

        layout.addStretch()

        self.setCentralWidget(scroll)

        mono = QFont("Menlo", 11)
        if not mono.exactMatch():
            mono = QFont("Consolas", 11)
        self.log_console.setFont(mono)

    def _wire_signals(self):
        self.picker_a.btn.clicked.connect(self._select_video_a)
        self.picker_b.btn.clicked.connect(self._select_video_b)
        self.picker_out.btn.clicked.connect(self._select_output)

        for card, radio in (
            (self.card_60, self.radio_60),
            (self.card_120, self.radio_120),
            (self.card_240, self.radio_240),
        ):
            radio.toggled.connect(
                lambda checked, c=card, r=radio: self._on_strength_changed(c, r, checked)
            )

        self.btn_run.clicked.connect(self._run_processing)

    def _on_strength_changed(self, card, radio, checked):
        if not checked:
            return
        for c in (self.card_60, self.card_120, self.card_240):
            c.set_selected(c is card)

    def _set_status(self, status: str, text: str):
        self.status_chip.setProperty("status", status)
        self.status_chip.setText(text)
        self.status_chip.style().unpolish(self.status_chip)
        self.status_chip.style().polish(self.status_chip)

    @staticmethod
    def _desktop_dir() -> str:
        home = os.path.expanduser("~")
        for name in ("Desktop", "桌面"):
            path = os.path.join(home, name)
            if os.path.isdir(path):
                return path
        return home

    @staticmethod
    def _timestamp_filename() -> str:
        return datetime.now().strftime("%Y%m%d%H%M%S") + ".mp4"

    def _select_video_a(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择内容视频 A",
            self._desktop_dir(),
            "视频 (*.mp4 *.avi *.mov *.mkv)",
        )
        if path:
            self.video_a_path = path
            self.picker_a.set_path(path)
            self._update_ready_state()

    def _select_video_b(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择素材视频 B",
            self._desktop_dir(),
            "视频 (*.mp4 *.avi *.mov *.mkv)",
        )
        if path:
            self.video_b_path = path
            self.picker_b.set_path(path)
            self._update_ready_state()

    def _select_output(self):
        default = os.path.join(self._desktop_dir(), self._timestamp_filename())
        path, _ = QFileDialog.getSaveFileName(
            self, "选择输出路径", default, "MP4 视频 (*.mp4)"
        )
        if path:
            if not path.lower().endswith('.mp4'):
                path += '.mp4'
            self.output_path = path
            self.picker_out.set_path(path)
            self._update_ready_state()

    def _update_ready_state(self):
        ready = bool(self.video_a_path and self.video_b_path and self.output_path)
        self.btn_run.setEnabled(ready)
        if ready:
            self._set_status("ready", "可以开始")
        else:
            self._set_status("idle", "等待配置")

    def _selected_fps(self) -> int:
        if self.radio_120.isChecked():
            return 120
        if self.radio_240.isChecked():
            return 240
        return 60

    def _set_controls_enabled(self, enabled: bool):
        self.picker_a.btn.setEnabled(enabled)
        self.picker_b.btn.setEnabled(enabled)
        self.picker_out.btn.setEnabled(enabled)
        self.radio_60.setEnabled(enabled)
        self.radio_120.setEnabled(enabled)
        self.radio_240.setEnabled(enabled)
        if sys.platform != 'darwin':
            self.gpu_checkbox.setEnabled(enabled)
        self.guard_checkbox.setEnabled(enabled)
        self.tiktok_checkbox.setEnabled(enabled)
        self.btn_run.setEnabled(
            enabled and bool(self.video_a_path and self.video_b_path and self.output_path)
        )

    def _append_log(self, text: str, level: str = "info"):
        colors = {
            "info": "#a1a1aa",
            "ok": "#6ee7b7",
            "warn": "#fcd34d",
            "err": "#f87171",
        }
        color = colors.get(level, colors["info"])
        safe = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        self.log_console.append(f'<span style="color:{color}">• {safe}</span>')
        cursor = self.log_console.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_console.setTextCursor(cursor)

    def _run_processing(self):
        fps = self._selected_fps()
        use_gpu = self.gpu_checkbox.isChecked()
        playback_guard = self.guard_checkbox.isChecked()
        tiktok_only = self.tiktok_checkbox.isChecked()
        enable_perturb = self.perturb_checkbox.isChecked()
        blend_alpha = self.blend_spin.value()
        audio_speed = self.audio_speed_spin.value()

        self._set_controls_enabled(False)
        self.progress_bar.setProperty("error", False)
        self.progress_bar.setValue(0)
        self.label_progress_pct.setText("0%")
        self.log_console.clear()
        self._set_status("busy", "处理中…")

        mode = "GPU (NVENC)" if use_gpu else "CPU"
        self._append_log(f"处理模式: {mode}", "info")
        self._append_log(f"去重强度: {fps} fps", "info")
        if enable_perturb:
            self._append_log(
                f"帧扰动: 已启用 (A/B 混合 {blend_alpha:.0%}, 音频速度 x{audio_speed:.2f})",
                "warn",
            )
        else:
            self._append_log("帧扰动: 未启用", "info")
        if playback_guard:
            self._append_log("播放保护: 已启用（HEVC 硬解 + 元数据）", "warn")
        else:
            self._append_log("播放保护: 未启用", "info")
        if tiktok_only:
            self._append_log("TikTok 专属: 已启用（10bit HEVC + BT.2020 · 仅移动端可播）", "warn")
        else:
            self._append_log("TikTok 专属: 未启用", "info")

        self.processor = VideoProcessor(
            self.video_a_path,
            self.video_b_path,
            self.output_path,
            fps,
            self.temp_dir,
            use_gpu,
            playback_guard,
            tiktok_only,
            enable_perturb,
            noise_intensity=0.02,
            blend_alpha=blend_alpha,
            audio_speed=audio_speed,
        )
        self.processor.progress.connect(self._on_progress)
        self.processor.status.connect(lambda t: self._append_log(t, "info"))
        self.processor.finished.connect(self._on_finished)
        self.processor.error.connect(self._on_error)
        self.processor.start()

    def _on_progress(self, value: int):
        self.progress_bar.setValue(value)
        self.label_progress_pct.setText(f"{value}%")

    def _on_finished(self):
        self._set_controls_enabled(True)
        self._set_status("done", "已完成")
        self._append_log(f"输出已保存: {self.output_path}", "ok")
        QMessageBox.information(
            self,
            "处理完成",
            f"视频已导出至:\n{self.output_path}",
        )

    def _on_error(self, message: str):
        self._set_controls_enabled(True)
        self._set_status("error", "失败")
        self.progress_bar.setProperty("error", True)
        self.progress_bar.style().unpolish(self.progress_bar)
        self.progress_bar.style().polish(self.progress_bar)
        self._append_log(message, "err")

    def closeEvent(self, event):
        if self.processor and self.processor.isRunning():
            reply = QMessageBox.question(
                self,
                "确认退出",
                "任务仍在进行，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return
            self.processor.terminate()
            self.processor.wait(3000)

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        super().closeEvent(event)

    def _except_hook(self, exc_type, exc_value, exc_traceback):
        import traceback
        msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        if hasattr(self, 'log_console'):
            self._on_error(f"未捕获异常:\n{msg}")
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
