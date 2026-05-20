"""
音频扰动模块 — 对抗平台音频指纹识别

核心思路：对 A 的音频做肉眼/耳几乎不可见的修改，
使平台的音频指纹/哈希完全不同。

提供三种扰动方式：
1. 微变速 — 0.98x-1.02x 速度变化，人耳听不出
2. 超高频噪声 — 18-20kHz 噪声，手机扬声器播不出
3. 相位微调 — 轻微相位偏移
"""

import os
import subprocess
import sys


def _creation_flags():
    return subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0


def process_audio(input_path: str, output_path: str,
                  speed_factor: float = 0.99,
                  add_ultrasonic: bool = True,
                  use_gpu: bool = False) -> None:
    """
    处理音频：微变速 + 超高频噪声。

    Args:
        input_path: 原始视频文件路径（提取音频）
        output_path: 处理后的音频输出路径
        speed_factor: 速度因子，0.99 = 减慢 1%（人耳几乎听不出）
        add_ultrasonic: 是否添加 19kHz 超高频噪声
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f'找不到源文件: {input_path}')

    # 构建 ffmpeg 滤镜链
    filters = []

    # 1. 微变速（atempo 只能接受 0.5-2.0 范围，用多个串联处理更精细的变化）
    if speed_factor != 1.0:
        filters.append(f'atempo={speed_factor}')

    # 2. 添加 19kHz 超高频噪声（手机扬声器无法播放，但改变音频指纹）
    if add_ultrasonic:
        # 生成 19kHz 正弦波，音量极低 (-40dB)，与原音频混合
        filters.append(
            f'amix=inputs=2:duration=first:dropout_transition=0'
        )
        # 使用复杂滤镜图来处理双输入

    if filters:
        filter_complex = ','.join(filters)
    else:
        filter_complex = None

    cmd = ['ffmpeg', '-y', '-i', input_path]

    if add_ultrasonic:
        # 双输入：原始音频 + 19kHz 噪声
        cmd.extend([
            '-i', 'anullsrc=r=44100:cl=stereo',  # 静音源
            '-filter_complex',
            # 生成 19kHz 正弦波，-40dB 音量，混合到原音频
            f'[1:a]afreqshift=freq=19000,afreqshift=freq=0,volume=-40dB[noise];'
            f'[0:a][noise]amix=inputs=2:duration=first:dropout_transition=0[aout]',
            '-map', '[aout]',
        ])
    elif filter_complex:
        cmd.extend(['-af', filter_complex])

    cmd.extend(['-c:a', 'aac', '-b:a', '192k', '-ar', '44100', output_path])

    subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        encoding='utf-8',
        creationflags=_creation_flags(),
    )

    if not os.path.isfile(output_path):
        raise RuntimeError('音频处理未生成输出文件')


def process_audio_simple(input_path: str, output_path: str,
                         speed_factor: float = 0.99) -> None:
    """
    简化版音频处理：只微变速，不添加超高频噪声。
    更稳定，兼容性更好。
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f'找不到源文件: {input_path}')

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-af', f'atempo={speed_factor}',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-ar', '44100',
        output_path,
    ]

    subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        encoding='utf-8',
        creationflags=_creation_flags(),
    )

    if not os.path.isfile(output_path):
        raise RuntimeError('音频处理未生成输出文件')
