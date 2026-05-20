"""应用全局样式（Qt 兼容子集，避免 box-shadow / transition 等无效属性）"""

APP_STYLESHEET = """
QMainWindow, QWidget#root {
    background-color: #0f1117;
}

QScrollArea {
    border: none;
    background: transparent;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}

/* —— 卡片 —— */
QFrame#card {
    background-color: #181b24;
    border: 1px solid #2a2f3d;
    border-radius: 12px;
}
QFrame#card_header {
    background: transparent;
    border: none;
    border-bottom: 1px solid #2a2f3d;
    border-radius: 0;
    padding: 0;
    margin: 0;
}

/* —— 文字 —— */
QLabel#app_title {
    font-size: 22px;
    font-weight: 700;
    color: #f4f4f5;
    background: transparent;
}
QLabel#app_subtitle {
    font-size: 12px;
    color: #8b92a8;
    background: transparent;
}
QLabel#section_title {
    font-size: 13px;
    font-weight: 600;
    color: #e4e4e7;
    background: transparent;
}
QLabel#section_hint {
    font-size: 11px;
    color: #6b7280;
    background: transparent;
}
QLabel#field_badge {
    font-size: 10px;
    font-weight: 600;
    color: #a5b4fc;
    background-color: #312e81;
    border-radius: 4px;
    padding: 2px 8px;
}
QLabel#field_badge_b {
    font-size: 10px;
    font-weight: 600;
    color: #6ee7b7;
    background-color: #064e3b;
    border-radius: 4px;
    padding: 2px 8px;
}
QLabel#field_badge_out {
    font-size: 10px;
    font-weight: 600;
    color: #fcd34d;
    background-color: #422006;
    border-radius: 4px;
    padding: 2px 8px;
}
QLabel#path_display {
    font-size: 12px;
    color: #a1a1aa;
    background-color: #12151c;
    border: 1px solid #2a2f3d;
    border-radius: 8px;
    padding: 10px 12px;
}
QLabel#path_display[pathSet="true"] {
    color: #e4e4e7;
}
QLabel#progress_pct {
    font-size: 12px;
    font-weight: 600;
    color: #818cf8;
    background: transparent;
}
QLabel#status_chip {
    font-size: 11px;
    font-weight: 600;
    color: #94a3b8;
    background-color: #1e293b;
    border-radius: 10px;
    padding: 4px 12px;
}
QLabel#status_chip[status="idle"] {
    color: #94a3b8;
    background-color: #1e293b;
}
QLabel#status_chip[status="ready"] {
    color: #6ee7b7;
    background-color: #064e3b;
}
QLabel#status_chip[status="busy"] {
    color: #fcd34d;
    background-color: #422006;
}
QLabel#status_chip[status="error"] {
    color: #fca5a5;
    background-color: #450a0a;
}
QLabel#status_chip[status="done"] {
    color: #93c5fd;
    background-color: #1e3a5f;
}

/* —— 按钮 —— */
QPushButton#ghost_btn {
    background-color: #252a36;
    color: #e4e4e7;
    border: 1px solid #3f4658;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
    min-width: 72px;
}
QPushButton#ghost_btn:hover {
    background-color: #2f3544;
    border-color: #6366f1;
    color: #ffffff;
}
QPushButton#ghost_btn:pressed {
    background-color: #1e2230;
}
QPushButton#ghost_btn:disabled {
    color: #52525b;
    border-color: #2a2f3d;
    background-color: #1a1d26;
}

QPushButton#primary_btn {
    background-color: #6366f1;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 14px 24px;
    font-size: 15px;
    font-weight: 600;
    min-height: 24px;
}
QPushButton#primary_btn:hover {
    background-color: #818cf8;
}
QPushButton#primary_btn:pressed {
    background-color: #4f46e5;
}
QPushButton#primary_btn:disabled {
    background-color: #3f3f46;
    color: #71717a;
}

/* —— 强度选项卡 —— */
QFrame#strength_card {
    background-color: #12151c;
    border: 2px solid #2a2f3d;
    border-radius: 10px;
}
QFrame#strength_card:hover {
    border-color: #4f46e5;
}
QFrame#strength_card[selected="true"] {
    border-color: #6366f1;
    background-color: #1e1b4b;
}
QLabel#strength_pct {
    font-size: 20px;
    font-weight: 700;
    color: #f4f4f5;
    background: transparent;
}
QLabel#strength_fps {
    font-size: 11px;
    color: #818cf8;
    background: transparent;
}
QLabel#strength_desc {
    font-size: 10px;
    color: #6b7280;
    background: transparent;
}

QRadioButton {
    spacing: 0;
    color: transparent;
    max-width: 0;
    max-height: 0;
    margin: 0;
    padding: 0;
}
QRadioButton::indicator {
    width: 0;
    height: 0;
    border: none;
}

QCheckBox#gpu_check {
    font-size: 13px;
    color: #d4d4d8;
    spacing: 10px;
}
QCheckBox#gpu_check::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #4f46e5;
    background: #12151c;
}
QCheckBox#gpu_check::indicator:checked {
    background: #6366f1;
    border-color: #6366f1;
}
QCheckBox#gpu_check:disabled {
    color: #52525b;
}

/* —— 进度条 —— */
QProgressBar {
    background-color: #12151c;
    border: 1px solid #2a2f3d;
    border-radius: 6px;
    text-align: center;
    font-size: 0px;
    color: transparent;
    min-height: 10px;
    max-height: 10px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366f1, stop:1 #8b5cf6);
    border-radius: 5px;
}
QProgressBar[error="true"]::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ef4444, stop:1 #dc2626);
}

/* —— 日志 —— */
QTextEdit#log_console {
    background-color: #0a0c10;
    border: 1px solid #2a2f3d;
    border-radius: 8px;
    font-family: "Menlo", "SF Mono", "Consolas", monospace;
    font-size: 11px;
    color: #a1a1aa;
    padding: 8px;
    selection-background-color: #312e81;
}
"""
