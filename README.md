# poem_prompt

面向古诗词短片 / 分镜创作的**意境参考图提示词技能**（Claude Code / Agent skill）。
把一句诗或一整首诗，转写成东方空灵意境的文生图提示词——先提炼意境、再构图，中英双版，
面向 Seedream / Nano Banana / Midjourney；另附一个给成图配竖排诗句的脚本。

> A prompt builder that turns classical Chinese poetry into luminous, pingyuan-style Eastern
> concept-art image prompts. It finds the emotional core of a line first, then builds the picture
> around one colossal form and one tiny focal point — delivered in both Chinese and English.

---

## 它能做什么

- **单句 → 一张图**：构思（诗眼、画面关系、大形体、最亮的线、点景）+ 中文分段提示词 + 英文提示词 + 避开的套路 + 另外的方向。
- **整首诗 → 分镜参考图组**：总览表 + 风格锁 + 逐镜中英提示词；每镜色调不同，支持 21:9 超宽画幅。
- **给成图配诗句**：`scripts/typeset_poem.py` 按每张图的留白位置排竖排诗句（宋体细体 + 粗体小标注），可拼成长图。
- **让画面动起来**：按意境写图生视频动效提示词（Seedance 等），做 2–3 秒短视频或抖音实况图。
- **做成苹果实况照片**：`scripts/make_live.py` 把"原图 + 视频"配成 Live Photo（3:4、3 秒），导入「照片」后可发抖音「图文·实况」。

## 核心方法

- **意境优先**：诗眼 → 一种看得见的画面关系（远/近、大/小、满/空、断/续、有/无、来/去……）→ 最后才决定画什么。诗里的名词不一定画。
- **骨架一重一轻**：一个巨大的深色形体压住画面 + 一条全画最亮的线 + 层层变淡的剪影 + 一个约 1% 的极小点景；提示词约四成篇幅写大形体。
- **氛围**：空气明亮、一个色相从深到浅拉满、光源藏在雾里；painterly 数字绘景——不是照片，不是 3D 渲染，不是插画。
- **原创**：避开国风图用滥的套路（孤舟小人、大树压入、白雾留白、瀑布门洞……）；给了参考图也只学方法、不抄画面。
- **字面陷阱**：同载 → 画成多人宴饮，少年 → 人物写真，明月 → 大月亮……在构图和负向里一起挡住。

## 仓库结构

```
poem_prompt/
├── SKILL.md                      主流程：意境 → 构思 → 空间 → 大形体与点景 → 色彩 → 表现 → 负向
├── CHANGELOG.md                  更新记录
├── references/
│   ├── principles.md             好图的八个要素、意境→画面关系实测例子、常见套路、失败对照
│   ├── annotated-examples.md     范例：桂花（单句）、黄河（单句）、杜甫《登高》（四镜分镜）
│   └── motion.md                 图生视频动效：原则、模板、《登高》四镜动效范例、实况照片流程
├── scripts/
│   ├── typeset_poem.py           给成图配竖排诗句并拼图
│   ├── denggao_config.json       配字配置示例
│   └── make_live.py              原图 + 视频 → 苹果实况照片
└── evals/
    └── evals.json                测试用例
```

## 怎么用

安装到 Claude Code 的 skills 目录：

```bash
git clone https://github.com/kyoko623/poem_prompt.git ~/.claude/skills/poem_prompt
```

然后在对话里直接给诗句，比如"欲买桂花同载酒，终不似，少年游，给我提示词"，或者贴一整首诗说"四句四张图，21:9"。

给成图配诗句：

```bash
pip install pillow
python3 ~/.claude/skills/poem_prompt/scripts/typeset_poem.py 你的配置.json          # 带小标注
python3 ~/.claude/skills/poem_prompt/scripts/typeset_poem.py 你的配置.json --clean  # 纯诗句
```

配置写法见 `scripts/denggao_config.json`。字体默认用 macOS 自带宋体（Songti SC）；其他系统把 `font.path` 换成思源宋体等中文衬线字体。

做实况照片（仅 macOS）：

```bash
pip install makelive
python3 ~/.claude/skills/poem_prompt/scripts/make_live.py --pairs 原图.png 视频.mp4 --out 输出目录 --aspect 3:4
```

参数说明见 `references/motion.md` 第四节。

## 持续迭代

这个 skill 会继续打磨：每次改动记在 `CHANGELOG.md`；改完用 `evals/evals.json` 里的用例回归一遍，确认没有退步。

## 适配模型

- **Seedream 5.0 Pro**：效果最好，直接用中文版。
- **Nano Banana**：优先用英文版。
- **Midjourney**：用英文版，末尾追加 `--ar 16:9`（或 `21:9`）和 `--no …`。

---

*用 [Claude Code](https://claude.com/claude-code) 持续打磨。*
