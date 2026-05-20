import os
import sys
import time
import itertools
import subprocess

import cv2
import ffmpeg
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

from playback_guard import apply_playback_guard, guard_description, probe_planned_encoder
from tiktok_only import convert_tiktok_only, tiktok_only_description
from frame_perturb import perturb_frame, blend_frames
from audio_perturb import process_audio_simple


def get_video_info(video_path):
    try:
        probe = ffmpeg.probe(video_path, cmd='ffprobe')
        video_stream = next(
            (s for s in probe['streams'] if s['codec_type'] == 'video'), None
        )
        if not video_stream:
            raise ValueError("未找到视频流")
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        r_frame_rate = video_stream.get('r_frame_rate', '0/1')
        if '/' in r_frame_rate:
            num, den = map(int, r_frame_rate.split('/'))
            fps = num / den if den > 0 else 0
        else:
            fps = float(r_frame_rate)
        duration_str = video_stream.get('duration')
        if duration_str:
            duration = float(duration_str)
        else:
            duration = float(probe.get('format', {}).get('duration', 0))
        total_frames_str = video_stream.get('nb_frames', '0')
        if total_frames_str != '0' and total_frames_str.isdigit():
            total_frames = int(total_frames_str)
        else:
            if duration > 0 and fps > 0:
                total_frames = int(duration * fps)
            else:
                cap = cv2.VideoCapture(video_path)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.release()
        if fps == 0 or total_frames == 0 or duration == 0:
            raise ValueError("视频元数据不完整或无效")
        return width, height, fps, duration, total_frames
    except Exception as e:
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"无法打开视频文件: {video_path}")
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            cap.release()
            if fps == 0 or total_frames == 0:
                raise ValueError("OpenCV 无法获取有效的视频信息")
            return width, height, fps, duration, total_frames
        except Exception as cv_e:
            raise RuntimeError(
                f"无法获取视频信息 {video_path}: FFmpeg: {e}; OpenCV: {cv_e}"
            ) from cv_e


def resize_video(input_path, output_path, width, height, use_gpu=False):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"输入视频文件不存在: {input_path}")
    encoder = 'h264_nvenc' if use_gpu else 'libx264'
    quality_param = '-preset p6' if use_gpu else '-crf 23'
    cmd_list = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', (
            f'scale={width}:{height}:force_original_aspect_ratio=decrease,'
            f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2'
        ),
        '-c:v', encoder,
    ]
    cmd_list.extend(quality_param.split())
    cmd_list.extend(['-c:a', 'aac', '-b:a', '128k', output_path])
    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    subprocess.run(
        cmd_list,
        check=True,
        capture_output=True,
        text=True,
        encoding='utf-8',
        creationflags=creation_flags,
    )
    if not os.path.exists(output_path):
        raise RuntimeError(f"FFmpeg 未能创建输出文件: {output_path}")


def frame_reader(video_path, width, height):
    command = [
        'ffmpeg', '-i', video_path,
        '-f', 'image2pipe', '-pix_fmt', 'bgr24', '-vcodec', 'rawvideo', '-',
    ]
    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    pipe = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=width * height * 3 * 10,
        creationflags=creation_flags,
    )
    frame_size = width * height * 3
    try:
        while True:
            raw_frame = pipe.stdout.read(frame_size)
            if not raw_frame or len(raw_frame) != frame_size:
                break
            yield np.frombuffer(raw_frame, dtype='uint8').reshape((height, width, 3))
    finally:
        pipe.kill()
        pipe.wait()


def get_a_positions(fps, n_a, total_frames_c):
    """
    计算 A 帧在输出流中的位置。
    
    新策略：A 帧占绝大多数（85-92%），B 帧只占少数做扰动。
    这样平台降帧后，采样到的仍然是 A 的内容（只是被扰动过）。
    
    Args:
        fps: 目标输出帧率 (60/120/240)
        n_a: 视频 A 的总帧数
        total_frames_c: 输出流总帧数
    
    Returns:
        A 帧位置的集合
    """
    if n_a == 0:
        return set()
    
    # 目标 A 帧覆盖率
    target_coverage = {60: 0.85, 120: 0.88, 240: 0.92}.get(fps, 0.85)
    
    # 计算每个 A 帧应该覆盖多少个输出帧
    frames_per_a = total_frames_c / n_a
    
    # 使用模式法：每 N 个输出帧中，M 个是 A 帧
    # 例如：60fps 时，每 7 帧中 6 帧是 A，1 帧是 B → 85.7% 覆盖
    # 120fps 时，每 8 帧中 7 帧是 A，1 帧是 B → 87.5% 覆盖
    # 240fps 时，每 13 帧中 12 帧是 A，1 帧是 B → 92.3% 覆盖
    pattern_map = {
        60: (6, 7),    # 6 A frames per 7 total
        120: (7, 8),   # 7 A frames per 8 total
        240: (12, 13), # 12 A frames per 13 total
    }
    a_count, pattern_len = pattern_map.get(fps, (6, 7))
    
    # 计算需要多少个 A 帧位置
    total_a_positions = int(total_frames_c * target_coverage)
    
    positions = set()
    # 为每个 A 帧分配输出位置
    a_frame_idx = 0
    for pattern_start in range(0, total_frames_c, pattern_len):
        # 在这个模式中，前 a_count 个位置是 A 帧
        for j in range(a_count):
            pos = pattern_start + j
            if pos >= total_frames_c:
                break
            if len(positions) >= total_a_positions:
                break
            positions.add(pos)
            a_frame_idx += 1
        if len(positions) >= total_a_positions:
            break
    
    # 如果还有剩余的 A 帧位置，继续分配
    if len(positions) < total_a_positions:
        remaining_positions = [i for i in range(total_frames_c) if i not in positions]
        for pos in remaining_positions:
            if len(positions) >= total_a_positions:
                break
            positions.add(pos)
    
    return positions


class VideoProcessor(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(
        self,
        video_a_path,
        video_b_path,
        output_path,
        fps,
        temp_dir,
        use_gpu=False,
        playback_guard=False,
        tiktok_only=False,
        # 新增：扰动参数
        enable_perturb=True,
        noise_intensity=0.02,
        blend_alpha=0.80,
        audio_speed=0.99,
    ):
        super().__init__()
        self.video_a_path = video_a_path
        self.video_b_path = video_b_path
        self.output_path = output_path
        self.fps = fps
        self.temp_dir = temp_dir
        self.use_gpu = use_gpu
        self.playback_guard = playback_guard
        self.tiktok_only = tiktok_only
        # 扰动参数
        self.enable_perturb = enable_perturb
        self.noise_intensity = noise_intensity
        self.blend_alpha = blend_alpha
        self.audio_speed = audio_speed

    def run(self):
        start_time = time.time()
        writer_process = None
        temp_b_path = os.path.join(self.temp_dir, "resized_b.mp4")
        temp_output_path = os.path.join(self.temp_dir, "temp_output.mp4")
        path_b_to_process = self.video_b_path
        temp_files_to_clean = [temp_output_path]
        reader_a_gen = None
        reader_b_gen = None
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0

        try:
            os.makedirs(self.temp_dir, exist_ok=True)
            self.status.emit(f"开始处理，检查视频信息… ({time.time() - start_time:.1f}s)")
            self.progress.emit(5)

            width_a, height_a, fps_a, duration_a, total_frames_a = get_video_info(self.video_a_path)
            self.status.emit(
                f"视频 A: {width_a}×{height_a}, {fps_a:.2f} fps, {duration_a:.2f}s, {total_frames_a} 帧"
            )
            width_b, height_b, _, _, _ = get_video_info(self.video_b_path)
            self.status.emit(f"视频 B: {width_b}×{height_b}")

            if not duration_a or duration_a <= 0:
                raise ValueError("无法获取视频 A 的有效时长")

            if (width_a, height_a) != (width_b, height_b):
                self.status.emit(
                    f"调整 B 分辨率 {width_b}×{height_b} → {width_a}×{height_a}…"
                )
                resize_video(self.video_b_path, temp_b_path, width_a, height_a, self.use_gpu)
                path_b_to_process = temp_b_path
                temp_files_to_clean.append(temp_b_path)
            else:
                self.status.emit("分辨率一致，跳过缩放")

            self.progress.emit(10)
            total_frames_c = int(duration_a * self.fps)
            self.status.emit(
                f"目标输出: {self.fps} fps, 时长 {duration_a:.2f}s, 共 {total_frames_c} 帧"
            )

            positions_a = get_a_positions(self.fps, total_frames_a, total_frames_c)
            encoder = 'h264_nvenc' if self.use_gpu else 'libx264'
            quality_param = '-preset p6' if self.use_gpu else '-crf 23'
            writer_cmd = [
                'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
                '-pix_fmt', 'bgr24', '-s', f'{width_a}x{height_a}', '-r', str(self.fps),
                '-i', '-', '-c:v', encoder,
            ]
            writer_cmd.extend(quality_param.split())
            writer_cmd.extend(['-pix_fmt', 'yuv420p', temp_output_path])

            writer_process = subprocess.Popen(
                writer_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                creationflags=creation_flags,
            )

            self.status.emit("开始混合帧…")
            self.progress.emit(20)

            try:
                reader_a_gen = frame_reader(self.video_a_path, width_a, height_a)
                reader_b_gen = frame_reader(path_b_to_process, width_a, height_a)
                reader_b_cycled = itertools.cycle(reader_b_gen)
                a_frame_counter = 0

                for i in range(total_frames_c):
                    if i in positions_a and a_frame_counter < total_frames_a:
                        frame_a = next(reader_a_gen)
                        frame_b = next(reader_b_cycled)

                        if self.enable_perturb:
                            # 对 A 帧做扰动
                            frame_a = perturb_frame(
                                frame_a,
                                noise_intensity=self.noise_intensity,
                                color_shift=True,
                                do_micro_transform=True,
                            )
                            # A 和 B 帧混合（而不是完全替换）
                            frame_to_write = blend_frames(
                                frame_a, frame_b, alpha=self.blend_alpha
                            )
                        else:
                            frame_to_write = frame_a

                        a_frame_counter += 1
                    else:
                        frame_to_write = next(reader_b_cycled)
                    writer_process.stdin.write(frame_to_write.tobytes())

                    if (i + 1) % 50 == 0 or (i + 1) == total_frames_c:
                        progress = 20 + int(70 * (i + 1) / total_frames_c)
                        self.progress.emit(min(progress, 89))
                        self.status.emit(
                            f"混合进度 {i + 1} / {total_frames_c} ({time.time() - start_time:.1f}s)"
                        )
            finally:
                if reader_a_gen:
                    reader_a_gen.close()
                if reader_b_gen:
                    reader_b_gen.close()

            self.status.emit("编码视频流…")
            _, stderr_output = writer_process.communicate()
            if writer_process.returncode != 0:
                raise RuntimeError(
                    f"FFmpeg 写入失败: {stderr_output.decode('utf-8', errors='ignore')}"
                )

            self.progress.emit(90)
            self.status.emit("合并音频轨…")

            # 先提取原始音频
            temp_audio_path = os.path.join(self.temp_dir, "temp_audio.aac")
            extract_cmd = [
                'ffmpeg', '-y', '-i', self.video_a_path,
                '-vn', '-acodec', 'aac', '-b:a', '192k',
                '-ar', '44100', temp_audio_path,
            ]
            subprocess.run(
                extract_cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                creationflags=creation_flags,
            )

            # 音频扰动（微变速）
            if self.enable_perturb and self.audio_speed != 1.0:
                self.status.emit(f"音频扰动：速度因子 {self.audio_speed}…")
                temp_perturbed_audio = os.path.join(self.temp_dir, "temp_audio_perturbed.aac")
                process_audio_simple(
                    temp_audio_path, temp_perturbed_audio,
                    speed_factor=self.audio_speed,
                )
                audio_for_merge = temp_perturbed_audio
                temp_files_to_clean.append(temp_perturbed_audio)
            else:
                audio_for_merge = temp_audio_path

            # 合并：视频 + 扰动后的音频
            final_cmd = [
                'ffmpeg', '-y',
                '-i', temp_output_path,
                '-i', audio_for_merge,
                '-c:v', 'copy',
                '-c:a', 'aac', '-b:a', '192k',
                '-map', '0:v:0', '-map', '1:a:0',
                '-shortest',
                self.output_path,
            ]
            subprocess.run(
                final_cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                creationflags=creation_flags,
            )
            temp_files_to_clean.append(temp_audio_path)

            if self.playback_guard:
                enc = probe_planned_encoder(self.use_gpu)
                self.progress.emit(92)
                self.status.emit(
                    f"应用播放保护（模拟器限制）: {guard_description(enc)}…"
                )
                apply_playback_guard(self.output_path, self.output_path, self.use_gpu)
                self.status.emit(
                    "播放保护已写入：HEVC 硬解参数 + 保护元数据（非商业 Widevine DRM）"
                )

            if self.tiktok_only:
                enc = probe_planned_encoder(self.use_gpu)
                self.progress.emit(95)
                self.status.emit(
                    f"TikTok 专属转换: {tiktok_only_description(enc)}…"
                )
                convert_tiktok_only(self.output_path, self.output_path, self.use_gpu)
                self.status.emit(
                    "TikTok 专属转换完成：HEVC 10bit + BT.2020 · PC 端将显示偏色/黑白且无声"
                )

            self.progress.emit(100)
            self.status.emit(f"全部完成，耗时 {time.time() - start_time:.1f}s")
            self.finished.emit()

        except Exception as e:
            import traceback
            self.error.emit(f"{e}\n{traceback.format_exc()}")

        finally:
            if writer_process and writer_process.poll() is None:
                writer_process.kill()
                writer_process.wait()
            for f in temp_files_to_clean:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except OSError as err:
                        self.status.emit(f"无法删除临时文件 {f}: {err}")
