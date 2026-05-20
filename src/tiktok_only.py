"""
TikTok 手机端专属播放转换

核心思路：MJ2C (Motion JPEG 2000) 编码
======================================
使用 MJ2C 视频编码 + AVI 容器。
PC 播放器（VLC/PotPlayer）不支持 AVI 中的 MJ2C 视频流。
TikTok 移动端（Android/iOS）使用系统硬件解码器，支持 MJ2C。

实现原理：
1. 编码：MJ2C 视频 + AAC 音频（保留音频）
2. 容器：AVI（伪装为 .mp4）
3. PC 因不支持 MJ2C 而无法播放视频，TikTok 正常播放
"""

import json
import os
import subprocess
import sys


def _creation_flags():
    return subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0


def convert_tiktok_only(
    input_path: str,
    output_path: str,
    use_gpu: bool = False,
) -> None:
    """
    将输入视频转换为 TikTok 手机端专属格式。

    转换后：
    - TikTok 手机端：正常播放（画面+声音）
    - PC 播放器：无法播放（不支持 MJ2C）
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f'找不到待转换文件: {input_path}')

    tmp_path = input_path + '.tiktok.tmp.mp4'

    # 构建 TikTok 专属元数据
    tiktok_meta = {
        'scheme': 'ab-tiktok-mobile-v5',
        'mobile_only': True,
        'pc_block_video': True,
        'pc_method': 'mj2c_codec',
    }

    cmd = [
        'ffmpeg', '-y', '-i', input_path,

        # ===== 视频：MJ2C (Motion JPEG 2000) 编码 =====
        # PC 播放器不支持 AVI 中的 MJ2C 视频流
        '-c:v', 'jpeg2000',
        '-pix_fmt', 'yuv420p',

        # ===== 音频：保留 AAC 音频（TikTok 可播放） =====
        '-c:a', 'aac',

        # ===== 容器：AVI（伪装为 .mp4） =====
        '-f', 'avi',

        # ===== 元数据混淆 =====
        '-map_metadata', '-1',
        '-metadata', 'title=TikTokMobile',
        '-metadata', 'encoder=TikTok-Mobile-Only',
        '-metadata', f'comment={json.dumps(tiktok_meta, ensure_ascii=False)}',

        # ===== 输出 =====
        tmp_path,
    ]

    subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        encoding='utf-8',
        creationflags=_creation_flags(),
    )

    if not os.path.isfile(tmp_path):
        raise RuntimeError('TikTok 专属转换未生成输出文件')

    os.replace(tmp_path, output_path)


def tiktok_only_description(encoder: str) -> str:
    """返回人类可读的描述"""
    return f'MJ2C + AVI 容器 · 仅 TikTok 移动端可正常播放'
