# 共享创作参考索引

这里存放所有视频模型共用的创作知识。Seedance、Agnes 和后续 provider 都从这里取词、取结构、取连续性规则；provider 专属语法只放在 `provider-profiles.md` 或各 skill 自己的补充手册里。

## 按任务加载

| 任务 | 必读 | 选读 |
|---|---|---|
| 写任何视频提示词 | `prompt-patterns.md` | `scene-recipes.md` |
| 确定景别、角度、运镜、构图、光线 | `cinematography.md` | `styles-and-visuals.md` |
| 确定画面风格、色调、质感 | `styles-and-visuals.md` | `cinematography.md` |
| 一镜到底、多镜头衔接、视频延长 | `continuity-and-transitions.md` | `cinematography.md` |
| 选择 provider 或转换提示词 | `provider-profiles.md` | `provider-contract.md` |
| 新增第三方视频模型 | `provider-contract.md` | `provider-profiles.md` |
| 产品、对话、动作、悬疑、情绪等类型片 | `scene-recipes.md` | `styles-and-visuals.md` |

## 文档边界

- `cinematography.md`：镜头语言与视听语法，不含任何 API 字段。
- `styles-and-visuals.md`：风格、色调、质感、导演参考与动漫术语。
- `prompt-patterns.md`：跨模型提示词结构与模板，使用通用占位符。
- `continuity-and-transitions.md`：首尾状态、轴线、动作惯性、转场与连续性审计。
- `provider-profiles.md`：Seedance / Agnes 的能力差异与通用字段映射。
- `provider-contract.md`：新增 provider 时必须实现的代码契约。
- `scene-recipes.md`：按内容类型组织的镜头配方与避坑点。

## 单一事实源

通用镜头词、风格词、提示词结构和连续性规则只在本目录维护。provider skill 不应再复制一套通用词库；如需补充，只写该模型独有的语法、限制或示例。
