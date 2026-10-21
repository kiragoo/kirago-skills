# kirago-skills

Claude Code 可复用技能集。每个子目录是一个独立技能（含 `SKILL.md`），安装到 `.claude/skills/` 或通过仓库克隆引用即可使用。

## 技能列表

### [hanzi-literacy-tutorial](hanzi-literacy-tutorial/) — 汉字启蒙识字教程制作

为 3-5 岁儿童制作「真实照片 + 发音 + 笔顺 + 游戏」的识字教程与动画。

- 产出：双页面交互教程（字卡 / 挑笔顺 / 描红 / 配图游戏）+ 分幕识字动画，完全离线可用
- 素材：Wikimedia Commons 真实摄影（**逐张人工核验**，拒绝卡通失真），自动抓取 CC 授权署名
- 工具：Commons 搜索/下载/署名脚本、经验证的页面模板、笔顺数据本地化流程

### [video-model-router](video-model-router/) — 跨模型视频生成路由

统一 Seedance、Agnes Video 2.5 Flash 及后续第三方视频模型的创作与调用流程。

- 创作层：共享镜头语言、风格词库、提示词模板、连续性与转场规则
- 执行层：provider 能力校验、请求转换、任务创建、轮询与结果归一化
- 已支持：Seedance（火山方舟 Ark）、Agnes Video 2.5 Flash（4–12 秒、720P）
- 扩展：新增 provider 只需实现 `references/provider-contract.md` 中的契约
- 适合：文生视频、图生视频、首尾帧、参考图/音频、多 provider 路由

## 安装使用

```bash
# 方式一：克隆到全局技能目录
git clone https://github.com/<user>/kirago-skills.git ~/.claude/skills/kirago-skills

# 方式二：仅链接单个技能
ln -s "$PWD/kirago-skills/hanzi-literacy-tutorial" ~/.claude/skills/hanzi-literacy-tutorial
```

之后在 Claude Code 中直接说「帮我做一套 10 个字的识字教程」即可触发。

## 目录约定

```
<skill-name>/
├── SKILL.md          # 技能入口：触发条件 + 核心原则 + 工作流（必须）
├── references/       # 深度细节，按需加载（可选）
├── scripts/          # 可执行辅助脚本（可选）
└── templates/        # 产出模板，标注 ✏️ 自定义区（可选）
```

## License

MIT
