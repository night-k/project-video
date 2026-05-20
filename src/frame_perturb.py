"""
帧扰动模块 — 对抗平台压缩还原

核心思路：对 A 帧做肉眼几乎不可见的修改，
使平台即使降帧提取也无法还原原始 A 帧。

提供三种扰动方式：
1. 微噪点 — 随机像素噪声（强度可控）
2. 色温偏移 — 微调 RGB 通道（肉眼看不出）
3. 微缩放+平移 — 1-2 像素的偏移或 1.01 倍缩放
"""

import numpy as np
import cv2


def add_noise(frame: np.ndarray, intensity: float = 0.02) -> np.ndarray:
    """
    添加随机像素噪声。
    intensity: 噪声强度，0-1 范围，默认 0.02 (2%)
    """
    if intensity <= 0:
        return frame
    noise = np.random.randn(*frame.shape).astype(np.float32) * 255 * intensity
    return np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def shift_color(frame: np.ndarray, r_shift: float = 2.0,
                g_shift: float = -1.0, b_shift: float = 1.5) -> np.ndarray:
    """
    微调 RGB 通道偏移。
    偏移量单位是像素值 (0-255)，默认 ±2 以内，肉眼几乎看不出。
    """
    if r_shift == 0 and g_shift == 0 and b_shift == 0:
        return frame
    # frame 是 BGR 格式 (OpenCV)
    shifted = frame.astype(np.float32)
    shifted[:, :, 0] += b_shift  # B
    shifted[:, :, 1] += g_shift  # G
    shifted[:, :, 2] += r_shift  # R
    return np.clip(shifted, 0, 255).astype(np.uint8)


def micro_transform(frame: np.ndarray, scale: float = 1.01,
                    dx: int = 1, dy: int = 1) -> np.ndarray:
    """
    微缩放 + 平移。
    scale: 缩放比例，1.01 表示放大 1%
    dx/dy: 平移像素数
    """
    if scale == 1.0 and dx == 0 and dy == 0:
        return frame

    h, w = frame.shape[:2]

    # 先缩放
    if scale != 1.0:
        new_w = int(w * scale)
        new_h = int(h * scale)
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    else:
        resized = frame
        new_w, new_h = w, h

    # 再平移
    if dx != 0 or dy != 0:
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        translated = cv2.warpAffine(resized, M, (new_w, new_h),
                                    borderMode=cv2.BORDER_REPLICATE)
    else:
        translated = resized

    # 裁剪回原始尺寸
    if new_w != w or new_h != h:
        x_start = (new_w - w) // 2
        y_start = (new_h - h) // 2
        translated = translated[y_start:y_start+h, x_start:x_start+w]

    return translated


def perturb_frame(frame: np.ndarray,
                  noise_intensity: float = 0.02,
                  color_shift: bool = True,
                  do_micro_transform: bool = True) -> np.ndarray:
    """
    组合扰动：噪声 + 色温 + 微变换。
    这是主入口函数，调用方只需传入原始帧即可。
    """
    result = frame.copy()

    # 1. 微噪点
    result = add_noise(result, noise_intensity)

    # 2. 色温偏移（每帧随机微调，避免固定偏移被平台校准）
    if color_shift:
        r = np.random.uniform(-2, 2)
        g = np.random.uniform(-1.5, 1.5)
        b = np.random.uniform(-1.8, 1.8)
        result = shift_color(result, r, g, b)

    # 3. 微变换（每帧随机偏移方向，避免规律性）
    if do_micro_transform:
        scale = np.random.uniform(1.005, 1.015)
        dx = np.random.randint(-2, 3)
        dy = np.random.randint(-2, 3)
        result = micro_transform(result, scale, dx, dy)

    return result


def blend_frames(frame_a: np.ndarray, frame_b: np.ndarray,
                 alpha: float = 0.80) -> np.ndarray:
    """
    A 和 B 帧混合，而不是完全替换。
    alpha: A 帧权重，默认 0.80 (A 占 80%，B 占 20%)
    平台降帧后每一帧都是混合帧，无法还原纯 A。
    """
    return cv2.addWeighted(frame_a, alpha, frame_b, 1 - alpha, 0)
