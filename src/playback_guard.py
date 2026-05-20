"""
移动端播放保护（实验性）

无法在本地 MP4 中嵌入 Widevine / FairPlay 等商业 DRM。
本模块使用 HEVC 硬解友好编码 + 保护元数据，提高真机硬解概率，
使多数模拟器/桌面软解难以播放。不保证对所有环境生效。
"""

import json
import os
import subprocess
import sys


def _creation_flags():
    return subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0


def _ffmpeg_encoders() -> str:
    try:
        r = subprocess.run(
            ['ffmpeg', '-hide_banner', '-encoders'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            creationflags=_creation_flags(),
        )
        return r.stdout or ''
    except OSError:
        return ''


def _pick_hevc_encoder(use_gpu: bool) -> tuple[str, list[str]]:
    encoders = _ffmpeg_encoders()

    if use_gpu and sys.platform == 'win32' and 'hevc_nvenc' in encoders:
        return 'hevc_nvenc', [
            '-preset', 'p5',
            '-profile:v', 'main',
            '-tag:v', 'hvc1',
            '-pix_fmt', 'yuv420p',
        ]

    if sys.platform == 'darwin' and 'hevc_videotoolbox' in encoders:
        return 'hevc_videotoolbox', [
            '-b:v', '10M',
            '-profile:v', 'main',
            '-tag:v', 'hvc1',
            '-pix_fmt', 'yuv420p',
        ]

    if 'libx265' in encoders:
        return 'libx265', [
            '-preset', 'medium',
            '-crf', '22',
            '-profile:v', 'main10',
            '-pix_fmt', 'yuv420p10le',
            '-tag:v', 'hvc1',
            '-x265-params', 'level-idc=51:ref=4:bframes=3:keyint=240',
        ]

    return 'libx264', [
        '-preset', 'medium',
        '-crf', '22',
        '-profile:v', 'high',
        '-level:v', '5.1',
        '-pix_fmt', 'yuv420p',
    ]


def probe_planned_encoder(use_gpu: bool) -> str:
    return _pick_hevc_encoder(use_gpu)[0]


def guard_description(encoder: str) -> str:
    if '265' in encoder or 'hevc' in encoder:
        return f'HEVC 硬解优先（{encoder}）+ 保护元数据'
    return f'H.264 高规格回退（{encoder}）+ 保护元数据'


def apply_playback_guard(
    input_path: str,
    output_path: str,
    use_gpu: bool = False,
) -> None:
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f'找不到待保护文件: {input_path}')

    encoder, enc_args = _pick_hevc_encoder(use_gpu)
    guarded_path = output_path + '.guard.tmp.mp4'

    guard_meta = {
        'scheme': 'ab-playback-guard-v1',
        'hw_decode_required': True,
        'sw_decode_discouraged': True,
    }

    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-c:v', encoder,
        *enc_args,
        '-movflags', '+faststart',
        '-map_metadata', '-1',
        '-metadata', 'title=ProtectedContent',
        '-metadata', 'encoder=AB-PlaybackGuard',
        '-metadata', f'comment={json.dumps(guard_meta, ensure_ascii=False)}',
        '-c:a', 'copy',
        guarded_path,
    ]

    subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        encoding='utf-8',
        creationflags=_creation_flags(),
    )

    if not os.path.isfile(guarded_path):
        raise RuntimeError('播放保护转码未生成输出文件')

    os.replace(guarded_path, output_path)
