# 拼贴动画（gbro-collage-broll · MiniMax 国内直连版）

> **本分支说明**：这是 [pyang5166/gbro-collage-broll](https://github.com/pyang5166/gbro-collage-broll) 的改造分支（原作者：狗哥笔记，MIT License）。原版 Gate 3 视频生成依赖 Gemini Omni Flash，国内无法直连；本分支将视频链路替换为 **MiniMax H3（海螺 3.0）**，`api.minimaxi.com` 国内直连、纯 Python 标准库实现（无需任何第三方 SDK / venv），另保留即梦 Seedance 2.5（火山方舟）脚本备选。三闸门审批流程与拼贴美学规范与原版完全一致。
>
> 与原版差异：默认模型 `MiniMax-H3`（768P，可选 2K）；API Key 读取顺序为 `--api-key` 参数 → 环境变量 `MINIMAX_API_KEY` → skill 目录下 `.env` 文件（**请勿提交你的 .env**，已在 .gitignore 排除）；交付步骤会用 ffmpeg 去音轨并统一到 1080×1440（3:4）。

<p align="center">
  <img src="assets/demo-purple.gif" width="180" alt="深紫底：多人协作压出科幻胶片">
  <img src="assets/demo-yellow.gif" width="180" alt="芥末黄底：错误被印刷机批量放大">
  <img src="assets/demo-red.gif" width="180" alt="红底：导演之手摆放棋盘走位">
  <img src="assets/demo-teal.gif" width="180" alt="青绿底：剪刀裁开镜头轨道">
</p>

把一句约 5 秒的口播文稿，压成一个 sharp visual idea，再生成高级编辑风**半调纸拼贴（halftone paper-collage）组装动画** B-roll。

Turn a ~5s voiceover line into a premium editorial paper-collage assemble-from-empty B-roll clip, powered by Gemini Omni Flash first/last-frame video generation.

## 效果

- 强烈平坦的纯色纸面色场 + 黑白 halftone 照片剪贴 + 彩色卡纸点缀
- 元素从空场逐件滑入、卡位、组装（stop-motion 质感），不是淡入或慢 zoom
- 默认交付 3:4、5 秒、1080×1440、24fps、无声 MP4，可直接垫在口播下面

## 工作流：三闸门审批

这个 skill 的核心不是 prompt 模板，而是强制的三阶段审批，让你把注意力花在审美判断上，而不是烧生成费用：

1. **Gate 1 · 隐喻确认** — 只输出视觉隐喻方案（核心意思 / 关键物件 / 底色 / 组装顺序），不生成任何图片视频
2. **Gate 2 · 静帧确认** — 确认后才生成彩色拼贴静帧 + contact sheet，再次等你确认
3. **Gate 3 · 视频生成** — 静帧通过后自动用 `gemini-omni-flash-preview` 做首尾帧组装动画，附完整 QA（逐秒抽帧、首帧空场验证、尾帧对照）

批量模式下支持部分通过：只有确认过的条目进入下一阶段。

## 环境要求

首次触发时 skill 会自动运行 `scripts/check_setup.sh` 自检，并针对缺失项给出配置指引。需要：

| 依赖 | 说明 |
|------|------|
| 带图片生成能力的 agent 环境 | Gate 2 静帧生成依赖内置图片生成工具（Codex `image_gen` / WorkBuddy `ImageGen` 等） |
| `MINIMAX_API_KEY` | [MiniMax 开放平台](https://platform.minimaxi.com/user-center/basic-information/interface-key) 创建，视频生成按量计费（768P 条约几毛钱） |
| Python >= 3.10 | 视频生成脚本只用标准库，无需安装任何依赖 |
| ffmpeg / ffprobe | 首尾帧处理、去音轨、contact sheet |

视频生成脚本（`scripts/generate_video_minimax.py`）已随 skill 自带，国内直连，无需额外安装其他 skill。

## 安装

把整个目录放进你的 agent skills 目录（例如 `~/.workbuddy/skills/`、`~/.agents/skills/` 或 `~/.claude/skills/`）：

```bash
git clone <本仓库地址> ~/.workbuddy/skills/拼贴动画
```

然后在 skill 目录创建 `.env` 文件写入你的 key（该文件已被 .gitignore 排除，不会上传）：

```bash
echo 'MINIMAX_API_KEY=你的key' > ~/.workbuddy/skills/拼贴动画/.env
```

## 使用

对你的 agent 说：

```text
拼贴动画：很多人以为 AI 是来替你思考的，其实它更像一面镜子，会把你问题里的漏洞照出来。
```

触发词：`拼贴动画`、`collage b-roll`、`纸拼贴 b-roll`、`半调拼贴`、`拼贴风格配画面`、`gbro-collage-broll`。

然后按 Gate 1 → Gate 2 → Gate 3 逐步确认即可。批量给多句文稿也可以，每句一个隐喻一条成片。

## 目录结构

```text
拼贴动画/
├── SKILL.md                        # skill 主文档（三闸门协议 + prompt 模板 + QA 标准）
├── agents/openai.yaml              # Codex interface 配置
├── evals/evals.json                # 四条闸门行为评测
└── scripts/
    ├── check_setup.sh              # 首次使用环境自检
    ├── generate_video_minimax.py   # MiniMax H3 批量视频生成（默认，国内直连）
    ├── generate_video_seedance.py  # 即梦 Seedance 2.5 / 火山方舟（备选）
    ├── generate_video.py           # Gemini Omni Flash（原版链路，仅兼容保留）
    ├── upload_file.py              # Gemini Files API 上传辅助（仅兼容保留）
    └── generate_veo_first_last.py  # 旧 Veo 链路（仅兼容保留，默认不用）
```

## FAQ

**为什么强制两次人工确认？**
错误的隐喻或静帧直接进视频生成，浪费的是真金白银的 API 费用。Gate 1 改文字是免费的，Gate 2 重生一张图远比重跑一条视频便宜。

**成片首帧边缘露出一点纸片？**
轻微的可以接受；严格空场需求建议用可编辑时间线的动画工具补前段。

**能换视频模型吗？**
默认固定 `MiniMax-H3`；脚本同时支持 `--model` 覆盖。想走即梦 Seedance 2.5（火山方舟）可改用 `scripts/generate_video_seedance.py`（需 `ARK_API_KEY`）。
