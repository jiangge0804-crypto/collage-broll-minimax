---
name: collage-broll-minimax
description: 将约 5 秒口播文稿、观点句或抽象概念做成高级 editorial halftone paper-collage / 半调纸拼贴 B-roll。用户说“拼贴动画”“collage b-roll”“纸拼贴 b-roll”“半调拼贴”“拼贴风格配画面”“用这段文稿做拼贴动画”“gbro-collage-broll”“collage-broll-minimax”，或希望把一句文稿转成拼贴视觉隐喻时，必须使用此 skill。强制采用三阶段审批：先只提视觉隐喻，用户确认后才生成彩色拼贴静帧，静帧再次确认后才默认调用 MiniMax H3（海螺 3.0，platform.minimaxi.com 国内直连）生成首尾帧组装动画。默认视频模型固定为 MiniMax-H3；只有用户明确指定其他模型时才切换。
compatibility: Gate 2 依赖环境内置 image_gen 工具（WorkBuddy 用 ImageGen）。视频生成脚本已随本 skill 自带（scripts/generate_video_minimax.py，纯标准库、国内直连 MiniMax 开放平台），另需 Python >= 3.10、已配置的 MINIMAX_API_KEY，以及 ffmpeg / ffprobe。首次使用先按「首次使用：环境自检」完成配置。
---

# 拼贴动画（原 gbro Collage B-roll）

把一句约 5 秒的口播压成一个 sharp visual idea，再做成高级编辑风纸拼贴组装动画。

默认链路：

1. 只设计视觉隐喻，等待用户确认
2. 只生成最终静帧，等待用户确认
3. 自动调用 MiniMax H3（海螺 3.0）生成视频并完成 QA

这两个确认闸门是工作流的一部分。它们让用户把注意力放在审美和方向上，同时避免错误隐喻或错误静帧直接消耗视频生成成本。

## 首次使用：环境自检

每次触发本 skill 时，进入 Gate 1 之前先运行自检脚本：

```bash
bash <本skill目录>/scripts/check_setup.sh
```

全部通过则直接开始 Gate 1，不要向用户重复配置信息。任何一项失败时，视为首次使用：不进入 Gate 1，先向用户输出下面的配置指南（只列出缺失项），等用户确认配置完成后重新自检。

### 配置指南（按缺失项输出）

1. **MINIMAX_API_KEY 未设置**
   到 [MiniMax 开放平台 - 接口密钥](https://platform.minimaxi.com/user-center/basic-information/interface-key) 创建 API Key（国内直连），然后写入 shell 配置：

   ```bash
   echo 'export MINIMAX_API_KEY="你的key"' >> ~/.zshrc && source ~/.zshrc
   ```

   注意：视频生成按量计费，由这个 key 对应的 MiniMax 账号承担；首次使用 H3 需先在平台完成按量购买开通（见[定价页](https://platform.minimaxi.com/docs/guides/pricing-paygo)）。

   **强烈建议用环境变量而不是 skill 目录下的 `.env`**：部分宿主环境（如 WorkBuddy 的 brokered file sandbox）会把 `.env` 判定为敏感内容并弹授权；若用户没及时点允许，脚本会抛 `PermissionError: Sensitive content approval timed out`，视频生成直接失败。写入 shell 配置后 `generate_video_minimax.py` 优先读环境变量，永远不会去打开 `.env`：

   ```bash
   echo 'export MINIMAX_API_KEY="你的key"' >> ~/.zshrc && source ~/.zshrc
   ```

   bash 层的 `sed/grep` 读取 `.env` 同样会被拦截，不要试图用 shell 变量绕过；正确做法是让用户配好环境变量，或让用户在授权弹窗点"允许"后重跑。

2. **ffmpeg / ffprobe 缺失**
   macOS：`brew install ffmpeg`；Debian/Ubuntu：`sudo apt install ffmpeg`。

3. **Python 环境缺失或版本过旧**（需要 >= 3.10）
   macOS：`brew install python3`；或从 python.org 安装。

4. **没有内置 image_gen 工具**
   Gate 2 的静帧生成依赖环境内置的图片生成工具（WorkBuddy 用 ImageGen）。在没有等效工具的环境下运行时，向用户说明需要自行提供等效的图片生成方式（或手动提供静帧图片后从 Gate 2 确认继续）。

## 强制审批协议

### Gate 1：隐喻确认

收到文稿后，先提视觉隐喻，不生成图片、不生成视频、不调用任何视频模型。

向用户交付每条的：

- 核心意思
- 情绪
- 一句话视觉命题
- 3–6 个关键物件
- 建议底色与局部点色
- 预期组装顺序

然后明确停下，等待用户回复“可以”“通过”“全部通过”或给出逐条修改意见。

如果用户只确认部分编号，只让通过的条目进入 Gate 2；未通过条目继续修改隐喻。

### Gate 2：静帧确认

隐喻确认后，才写 visual spec 和 imagegen prompt，并用环境内置的图片生成工具（如 WorkBuddy 的 ImageGen）生成最终静帧。

把原图保存到项目目录，生成带编号的静帧 contact sheet，向用户展示并再次停下。此阶段仍然不调用 MiniMax H3，也不生成视频。

如果用户只确认部分静帧，只让通过的条目进入 Gate 3；需要修改的静帧先重生并重新确认。

### Gate 3：视频生成

静帧确认后，不再询问使用哪个视频模型，直接使用本 skill 自带的 `scripts/generate_video_minimax.py`，默认调用：

```text
MiniMax-H3
```

只有用户明确指定其他视频模型时，才覆盖这个默认值。不要把模型选择再抛给用户。

## 成功标准

- 一句话只表达一个清晰隐喻
- 同一批画面有统一设计语言，但不强制全部蓝底
- 背景是强烈、平坦、均匀的色场，可按语意变化
- 主体以黑白 halftone photographic cut-outs 为骨架
- 关键卡片、按钮、胶片、规则册等允许使用红、黄、青、橙、紫、奶油白等彩色纸张
- 所有纸片有清晰裁切边、奶油白 keyline、低透明度柔和阴影和纸张颗粒
- 动作是 assemble-from-empty，而不是轻微漂移、晃动或慢 zoom
- 无字幕、无口播全文、无 logo、无水印、无 UI
- 默认交付 3:4、5 秒、768×1024、24fps MP4；音轨规则：**要纸张拼贴拟音（剪纸、滑入、卡位声），禁 BGM 背景音乐**——模型出乐则去轨降级为无声

## 什么时候不要用

- 需要精确控制图层、遮挡、镜头穿越或可编辑时间线：改用分层动画工具（如 HyperFrames 类 HTML 渲染视频方案）
- 只需要视频提示词，不需要生成成片：直接写 prompt 即可，不用走本流程
- 需要真实人物产品广告或口播演员：不要走本拼贴流程
- 用户明确要可逐层修改的透明素材：本 skill 默认不拆透明图层

## 默认项目目录

使用北京时间 `Asia/Shanghai` 命名：

```text
~/hyperframes-projects/YYYY-MM-DD-collage-broll-标题/
```

批量项目推荐结构：

```text
<project>/
├── brief.md
├── visual-spec.json
├── imagegen-prompts.md
├── video-jobs.json
├── gate2-qa.md
├── gate3-qa.md
├── still-contact-sheet.jpg
├── video-contact-sheet-all.jpg
├── video-first-frame-all.jpg
├── end-frame-comparison-all.jpg
├── 01-概念名/
│   ├── video-prompt.txt
│   ├── frames/
│   │   ├── last-frame-original.png
│   │   ├── first-frame.png
│   │   └── last-frame.png
│   └── video/run-v01/
│       ├── final-5s.mp4
│       ├── final-5s-sfx.mp4
│       ├── final-5s-noaudio.mp4
│       ├── contact-sheet.jpg
│       ├── video-last-frame.jpg
│       └── end-frame-comparison.jpg
└── 02-概念名/...
```

## Phase 1：设计视觉隐喻

先把文稿压成一个视觉命题。

提取：

- 核心意思：观众最终要看懂什么
- 情绪：冷静、惊讶、紧迫、豁然开朗、荒诞、反讽
- 动作动词：打开、连接、漏掉、装订、归档、点亮、压缩、分叉、组装
- 可视化隐喻：机器、时钟、胶片、档案柜、控制台、规则册、漏斗、轨道、棋子

不要把文稿逐字放进画面。默认一条文稿只做一个隐喻，控制在 3–6 个关键物件；元素过多会让语意变弱，也会让首尾帧组装动画不稳定。

批量隐喻优先形成前后叙事：例如先表现手工消耗与经验流失，再表现规范沉淀与人机分工。

隐喻打磨三条实战经验（2026-10「搜索迁移」项目验证）：

- 对比类文稿（"A 更适合 X，B 更适合 Y"）优先画**决策瞬间**（岔路口二选一、转身、犹豫后迈步），而不是把两种遭遇并排对比——把"转变"这个动作本身画成画面主体，语义远比"两种结果对照"清晰。
- 文案主语必须在画面落实：说"大家"就要有群体证据（一群小人、右路上已有先行者剪影）。只画一个人会丢掉"多数人"的语感，用户会打回。
- 3:4 竖版的对照类构图优先上下分层或 Y 形分叉（路径自底部向上分叉），避免左右并排——并排在竖版会留大片死空间。

### Gate 1 输出示例

```text
1. 核心意思：经验每次都在重复消耗
   视觉隐喻：熟练剪辑师围着巨大的胶片时钟逐帧裁切，时钟走完一圈却只得到一小段成片
   关键物件：胶片时钟、剪辑师、剪刀、短胶片
   色彩：焦橙底，奶油白与浅青点色
   组装顺序：时钟 → 人物与剪刀 → 胶片 → 最终短输出
```

输出后停下等待确认。

## Phase 2：生成彩色拼贴静帧

隐喻确认后，先写自包含的 `visual-spec.json`，再写 imagegen prompt。

### Visual spec

```json
{
  "script_meaning": "",
  "visual_metaphor": "",
  "style_signature": "flat bold color field, mixed black-and-white halftone cut-outs and colored cardstock accents, crisp cut edges, cream keylines, soft paper shadows, editorial paper collage",
  "aspect_ratio": "3:4",
  "color_field": {
    "background_hex": "",
    "accent_colors": [],
    "paper_grain": "fine uncoated-paper fiber"
  },
  "elements": [
    {
      "what": "",
      "role": "",
      "motion": "",
      "placement": ""
    }
  ],
  "composition": {
    "layout": "",
    "negative_space": "",
    "final_frame": ""
  },
  "motion_plan": "structure first, subject or cards second, action and result last",
  "avoid": "typography, readable letters, numerals, logos, watermark, UI, subtitles, glossy 3D, photoreal environment"
}
```

### 色彩规则

不要把 cobalt blue 当成唯一默认值。根据语意挑选强色场，并在一批作品中保持“同设计语言、不同底色”：

- 焦橙 / 红：时间消耗、劳动、紧迫
- 芥末黄：工具、警示、经验漏失
- 墨绿：认知、审美、系统重置
- 深紫：规范、沉淀、长期记忆
- 青绿：判断、协作、自动执行

主体可以黑白半调为主，但局部彩色纸张必须服务信息层级，不要为了彩色而彩色。

### Imagegen prompt 模板

使用环境内置的图片生成工具（WorkBuddy 中为 ImageGen；如有本地 `imagegen` skill 则一并遵守）：

```text
Use case: ads-marketing
Asset type: final still frame for a 3:4 image-to-video B-roll clip
Primary request: Create a finished editorial paper-collage image expressing [一句话视觉命题].
Scene/backdrop: perfectly flat [颜色] paper field [hex] with subtle uncoated paper fiber.
Style/medium: premium editorial stop-motion paper collage; black-and-white halftone photographic cut-outs mixed with selective [点色] colored cardstock.
Composition/framing: vertical 3:4 locked poster frame; central subject within the middle 70 percent; generous clean color-field negative space; 3–6 large separable paper groups for later assemble-from-empty animation.
Materials/textures: visible printed halftone dots, crisp machine-cut edges, thin warm-cream paper keylines, soft low-opacity physical drop shadows.
Constraints: [本条隐喻必须一眼看懂的关系].
Avoid: no typography, no readable letters, no numerals, no logos, no watermark, no UI, no subtitles, no glossy 3D, no photoreal environment, no clutter.
```

### 静帧 QA

- 隐喻是否一眼看懂
- 主体是否集中
- 是否有假字、logo、水印或 UI
- 是否保留足够纯色场，方便从空场组装
- 是否是 3–6 个清晰大组，而不是满屏碎片
- 同一批是否统一质感但有色彩变化

将通过 QA 的原图复制到项目目录，生成带编号的静帧 contact sheet，展示给用户并停下等待 Gate 2 确认。静帧 QA 结论写入 `<project>/gate2-qa.md`。

如果用户要求重生部分静帧，重生后生成 `still-contact-sheet-v2.jpg`（后续轮次递增 v3、v4…），保留旧版 contact sheet 不覆盖，方便对比。

## Phase 3：用 MiniMax H3 生成视频

### 1. 准备首尾帧

保留 imagegen 原图，再统一尾帧：

```bash
ffmpeg -y -i <item>/frames/last-frame-original.png \
  -vf "scale=1080:1440:force_original_aspect_ratio=increase,crop=1080:1440" \
  <item>/frames/last-frame.png
```

首帧默认是与尾帧相同底色的纯色空纸面：

```bash
ffmpeg -y -f lavfi -i color=c=0x<HEX>:s=1080x1440 \
  -frames:v 1 <item>/frames/first-frame.png
```

如果用户明确要求不从完全空白开始，首帧才保留一个基础物件。

**末帧即终态（关键）**：首尾帧模式下视频结尾会严格收敛到 Image 2 的构图——结尾要出现的任何动作**结果**（人物已走到某处、手里已拿到某物、某物已消失）都必须直接画进末帧静帧，不能只写在 prompt 里。实测：末帧画"人停在岔路口犹豫"，无论 prompt 怎么写"然后走向门前拿到答案卡"，视频都会停在选择前一刻。要"完成动作"的闭环，就重画末帧把终态画进去，再重跑。

### 2. 写动画 prompt

动作顺序默认采用：

```text
基础结构 → 人物或关键卡片 → 连接件 → 动作 → 最终结果
```

Prompt 模板：

```text
Paper-collage stop-motion assembly, using Image 1 as the exact empty first frame and Image 2 as the exact completed last frame. In one continuous locked-off vertical shot, open on the empty flat [color] paper field.

Assemble the scene piece by piece with crisp physical stop-motion timing: [按顺序描述 3–6 个元素如何滑入、卡位、连接和完成动作]. End by holding the supplied completed composition.

Preserve the exact 3:4 framing, [hex] color field, colored cardstock accents, uncoated paper grain, halftone dots, cream keylines, crisp cut edges and soft shadows. Restrained tactile 2D paper craft only.

No scene cuts, no camera movement, no zoom, no morphing, no new objects, no text, no letters, no numbers, no logos, no watermark, no UI.

Sound design: diegetic paper-craft foley only, tightly synced to the assembly — crisp paper cutting, cardstock sliding in and snapping into place, light paper rustle. Strictly no music, no background music, no melody, no rhythm track, no ambience, no narration.
```

每条 prompt 都要明确 Image 1 是空首帧、Image 2 是确认过的完成帧。最终构图必须贴近 Image 2，不让模型自由改造尾帧。

### 3. 检查运行环境

`generate_video_minimax.py` 只依赖 Python 标准库（>= 3.10），不需要任何第三方 SDK 或 venv，直接用系统 `python3` 运行。

ffmpeg / ffprobe 注意：部分 agent 沙箱 shell 的 PATH 不含 `/opt/homebrew/bin`，`command -v ffmpeg` 会误报缺失。`check_setup.sh` 会自动探测常见安装目录并提示绝对路径；一旦它提示"不在 PATH"，后续所有 ffmpeg 命令都必须用绝对路径（如 `/opt/homebrew/bin/ffmpeg`），不要依赖裸命令。

确认 `MINIMAX_API_KEY` 已设置，但不要输出或记录密钥内容。

生成报 `HTTP 402 insufficient_balance_error (1008)` 时：让用户到 MiniMax 开放平台充值后原样重跑即可（prompt / 首尾帧 / jobs 全部保留，无需重建）。注意 H3 视频生成需在后台开通"按量付费"，钱包余额与视频按量额度是分开的；若后台显示余额充足仍报 1008，拿返回的 request_id 找客服。不要为绕过 402 换模型或改管线。

不要尝试用 WorkBuddy 内置 VideoGen 替代本管线：它虽支持 `last_image` 首尾帧插值，但 `aspect_ratio` 不支持 3:4（实测报 `14407 unsupported video aspect_ratio: 3:4, supported values: []`），无法产出竖版成片。

### 4. 批量调用 MiniMax H3

创建 `video-jobs.json`。每个 job 使用两张图片做首尾帧插值：

```json
{
  "prompt": "<动画 prompt>",
  "image": [
    "<item>/frames/first-frame.png",
    "<item>/frames/last-frame.png"
  ],
  "output": "<item>/video/run-v01/final-5s.mp4",
  "aspect_ratio": "3:4",
  "duration": 5
}
```

使用本 skill 自带脚本：

```bash
python3 <本skill目录>/scripts/generate_video_minimax.py \
  --batch <project>/video-jobs.json \
  --concurrency 3
```

脚本默认模型即 `MiniMax-H3`、默认分辨率 768P（更省钱；要 2K 画质可在 job 里加 `"resolution": "2K"`）。首尾帧模式下宽高比由输入图片自动决定（3:4 帧即得 3:4 视频），图片以 base64 内联上传。如果报未开通/欠费错误，去 MiniMax 开放平台完成按量购买开通后重试。

### 5. 音效交付（并统一到 768×1024）——纸张拟音可以要，BGM 不要

音轨规则：**纸片组装类动效音效（拟音）是需要的，背景音乐 BGM 是禁止的。**

1. 视频 prompt 末尾必须带 Sound design 段（见上文模板），引导 MiniMax H3 只生成纸张拟音、严禁音乐。
2. 生成后先做音轨 QA（agent 无法试听，用能量分布启发式判断——拟音是稀疏瞬态、含静音间隙；BGM 是连续满能量、几乎无静音）：

```bash
ffmpeg -i <run>/final-5s.mp4 -af silencedetect=noise=-35dB:d=0.15 -f null - 2>&1 | grep silence
```

3. 按检测结果分支（注意 zsh 下 `?` 必须加引号）：
   - **检测到多段静音间隙**（判定为拟音）→ 保留音轨交付：

   ```bash
   ffmpeg -y -i <run>/final-5s.mp4 \
     -map 0:v:0 -map "0:a:0?" -vf "scale=768:1024" -c:v libx264 -crf 18 -pix_fmt yuv420p \
     -c:a aac -b:a 128k -shortest <run>/final-5s-sfx.mp4
   ```

   - **无静音间隙**（判定为 BGM）→ 去音轨降级交付：

   ```bash
   ffmpeg -y -i <run>/final-5s.mp4 \
     -map 0:v:0 -vf "scale=768:1024" -c:v libx264 -crf 18 -pix_fmt yuv420p -an \
     <run>/final-5s-noaudio.mp4
   ```

启发式不百分百准确；拿不准时优先去音轨（宁缺毋滥，绝不允许 BGM 混进交付），并向用户说明可提供带原生音轨的版本供人工试听。原始 `final-5s.mp4` 始终保留为中间产物。

## 视频 QA

不要只看尾帧，必须检查组装过程和最终落位。

### Contact sheet

```bash
ffmpeg -y -i <run>/final-5s-sfx.mp4 \
  -vf "fps=1,scale=270:360,tile=5x1" \
  -frames:v 1 <run>/contact-sheet.jpg
```

通过标准：

- 首帧接近纯色空场；边缘轻微提前露出纸片可以接受
- 中段能看到结构、人物或卡片逐步进入，而不是整体淡入
- 没有切镜、zoom、3D 化或写实场景漂移
- 没有假字、logo、水印或 UI
- 最终帧与确认静帧一致；轻微姿态或细节漂移（如人物姿势微变、小零件增减）只要不影响隐喻语义即可判通过，不要为此重跑
- 成片为 768×1024、24fps、5 秒；音轨只含纸张拟音（final-5s-sfx.mp4），或为无声降级（final-5s-noaudio.mp4）；绝不含 BGM

另外抽取视频末帧，与确认静帧并排生成 `end-frame-comparison.jpg`。批量项目再合并三张总览图：

- `video-contact-sheet-all.jpg`：全部成片逐秒抽帧
- `video-first-frame-all.jpg`：全部成片实际首帧，验证真的从空色场开始
- `end-frame-comparison-all.jpg`：确认静帧与视频末帧并排对照

逐条 QA 结论（含带瑕疵通过的判定理由）写入 `<project>/gate3-qa.md`。

抽帧与 QA 图注意事项：

- `tile` 需要的格数多于实际抽帧数时会**补黑格**（如 7.29s 视频 `fps=1,tile=2x4` 只有 8 帧但最后一格可能发黑）——先用 `blackdetect=d=0.1:pix_th=0.10` 确认成片真的没有黑帧，再决定是否需要处理，不要被 QA 图吓到重跑。
- 竖版项目的 contact sheet 与末帧对照图一律 **vstack 竖排**（如 540×1440），不要出横版拼图——用户会把横版 QA 图误认为成片比例错了。
- `ffprobe` 一次只能接一个输入文件，批量验证尺寸用 for 循环逐个跑。
- 运动方向存疑时用 `fps=2` 密集抽帧复核，不要只看 `fps=1` 缩略拼图下结论（小人很小容易看错位置和方向）。

### 常见问题

- 首帧边缘提前露出：轻微可接受；严格空场需求改用 HyperFrames 补前段
- 组装感弱：缩短元素数量，并把 prompt 改为明确的逐件 slide in / snap into place 顺序
- 尾帧漂移：强化 “Image 2 is the exact completed last frame” 和 “End by holding the supplied completed composition”
- 已印文字标签漂移/被重绘：prompt 里逐一点名锁定——"The printed paper labels already on the [objects] — the Chinese label on the left and the [X] label on the right — must stay exactly as they are, completely unchanged, not redrawn, not re-lettered, not moved."（实测两处中文/英文标签 7 秒全程零漂移）
- 出现假字：先回到静帧重生，不要直接用视频 prompt 修补
- ImageGen 右下角内置水印（"AI生成 WORKBUDDY"）：用 `drawbox` 拿底色盖掉，但**必须用实测采样色**——ImageGen 实际渲染的底色和提示词里写的 hex 有偏差（实测提示 #0F6E56 渲染成 #1E6E69），直接用提示词色会留下明显色块。采样一行：

  ```bash
  ffmpeg -y -i still.png -vf "crop=1:1:900:1380" -frames:v 1 -f rawvideo -pix_fmt rgb24 - \
    | od -An -tx1 | head -1     # 读出 RGB，再填进 drawbox=color=0x......
  # 去水印 + 统一 3:4，一次完成：
  ffmpeg -y -i still.png -vf "drawbox=x=980:y=1420:w=172:h=116:color=0x1E6E69@1.0:t=fill,scale=1080:1440:force_original_aspect_ratio=increase,crop=1080:1440" -frames:v 1 last-frame.png
  ```

  首帧纯色空场也必须用同一个实测色，否则组装动画首尾底色不一致。
- 个别视频失败：只重跑对应 job，不要重跑已经通过的条目
- **本地轮询被截断，但远端任务还在跑**（shell 被 SIGTERM，或 `poll_task` 抛 "did not finish within 20 minutes"）：`generate_video_minimax.py` 是"先建远端任务、再本地轮询"，`POLL_DEADLINE` 硬编码 20 分钟。**不要重新提交同一 job——会二次计费**。正确做法是只查 `GET /v2/query/video_generation/{task_id}` 拿 `task.content.url` 下载：

  ```python
  # 脚本会打印 "Task created: <task_id>"，记下它
  url = f"https://api.minimaxi.com/v2/query/video_generation/{task_id}"
  # header: Authorization: Bearer $MINIMAX_API_KEY
  # 成功时 task["content"]["url"] 即下载直链，直接 urllib 落盘
  ```

  实测：7 秒任务在高峰期可能排队 30 分钟以上仍为 `running`（`updated_at` 不刷新属正常），远端不会被取消。等待窗口要自己放宽（用独立续查脚本，别依赖 `poll_task` 的 20 分钟上限），并且下载后务必用 `ffprobe` 校验时长/分辨率再进 QA。

## 默认交付

向用户交付：

- 每条 `<item>/video/run-v01/final-5s-sfx.mp4`（带纸张拟音；若模型出了 BGM 则降级交付 `final-5s-noaudio.mp4` 并说明）
- 每条 contact sheet
- 批量总 contact sheet
- 最终帧对照图
- 一句说明每条文稿如何转成视觉隐喻

如果成片问题来自 MiniMax H3 的快速生成限制，直接说明；只有需要精确图层控制时，才建议切换到 HyperFrames。

## 旧脚本

目录中的 `scripts/generate_veo_first_last.py`（Veo）、`scripts/generate_video.py` 与 `scripts/upload_file.py`（Gemini Omni Flash）、`scripts/generate_video_seedance.py`（即梦 Seedance 2.5 / 火山方舟）仅为旧项目兼容保留，Gemini 链路在国内无法直连。不要在默认流程中调用它们。
