# AB 视频去重工具: 高帧率抽帧混合 + 扰动去重

[简体中文](./README.md) | [English](./README_en.md)

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)

> ⚠️ 仅供技术研究与学习交流，请勿用于任何非法用途。

**AB 视频去重工具** 是一款开源桌面应用，通过「高帧率抽帧混合 + 帧扰动 + 音频扰动 + TikTok 专属编码」多重策略，从根本上改变视频数据指纹，规避短视频平台的原创度检测和查重机制。

<p align="center">
  <img src="./assets/cover_software.png" alt="软件主界面" width="600"/>
  <br>
  <em>简洁直观的软件主界面</em>
</p>

---

## 💡 工作原理

### 1. 高帧率抽帧混合

| 去重强度 | 目标 FPS | A:B 帧大致比例 |
| :---: | :---: | :---: |
| **50%** | 60 | 1 : 1 |
| **75%** | 120 | 1 : 3 |
| **87.5%**| 240 | 1 : 7 |

1. **输入两个视频**：
   * **视频 A（内容视频）**：要发布的目标视频
   * **视频 B（素材视频）**：与 A 内容无关的视频

2. **生成高帧率视频流**（60/120/240 fps）

3. **智能抽帧插入**：A 帧插入关键位置，B 帧填充间隙

4. **最终效果**：手机端看到的仍是流畅的 A 画面，但数据指纹已完全不同

### 2. 帧扰动（对抗平台压缩还原）

对 A 帧施加肉眼不可见的修改：
- 微噪点（2% 强度）
- 色温随机偏移
- 1.01x 微缩放 + 微平移
- A/B 帧按比例混合（默认 A 占 80%）

即使平台降帧还原，也无法得到原始 A 帧。

### 3. 音频扰动

对音轨做微变速处理（默认 0.99x），改变音频指纹。

### 4. TikTok 手机端专属（可选）

勾选后输出视频仅 TikTok 移动端可正常播放，PC 端显示色彩异常/黑白画面且无音频。

### 5. 播放保护（可选，实验性）

追加 HEVC 硬解友好编码与保护元数据，提高真机硬解概率，降低模拟器/软解播放成功率。

---

## ✨ 核心功能

- **直观的图形界面**：PyQt5 构建，操作简单
- **三种去重强度**：60 / 120 / 240 fps
- **帧扰动**：微噪点 + 色温偏移 + 微缩放 + A/B 混合
- **音频扰动**：微变速改变音频指纹
- **TikTok 专属模式**：仅移动端可播放
- **播放保护**：HEVC 硬解优化（实验性）
- **NVIDIA GPU 加速**：NVENC 硬件编码
- **自动分辨率匹配**：B 视频自动适配 A 的分辨率
- **实时进度与日志**

---

## 🚀 快速开始

### 系统要求

1. **Python**: 3.8+
2. **FFmpeg**: 必须安装并加入 PATH
   - macOS: `brew install ffmpeg`
   - Windows: 从 [gyan.dev](https://gyan.dev/ffmpeg/builds/) 下载
   - Linux: `sudo apt install ffmpeg`

### 安装与启动

```bash
git clone <仓库地址>
cd AB-Video-Deduplicator
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

### 使用

1. 选择视频 A（内容视频）
2. 选择视频 B（素材视频）
3. 选择去重强度（60 / 120 / 240 fps）
4. 可选：启用帧扰动、TikTok 专属、播放保护
5. 选择输出路径，点击「开始处理」

---

## 📂 项目结构

```
├── src/
│   ├── main.py              # 入口
│   ├── video_processor.py   # 核心处理线程
│   ├── frame_perturb.py     # 帧扰动（噪点/色温/微变换）
│   ├── audio_perturb.py     # 音频扰动（微变速）
│   ├── tiktok_only.py       # TikTok 手机端专属转换
│   ├── playback_guard.py    # 播放保护（HEVC 硬解优化）
│   ├── theme.py             # 界面样式
│   ├── resources.qrc        # Qt 资源文件
│   ├── resources.py         # 编译后的资源
│   └── ui/                  # PyQt5 UI 组件
├── utils/
│   ├── extract_frames.py    # 帧提取工具
│   └── gen_test_video.py    # 测试视频生成
├── assets/                  # 图标与截图
├── docs/
│   └── screenshot.png       # 软件截图
├── requirements.txt
└── LICENSE
```

---

## 📜 开源协议

MIT License
