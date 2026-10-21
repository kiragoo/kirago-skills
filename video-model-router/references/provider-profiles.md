# Provider 差异与字段映射

本文件只记录 provider 差异。通用创作知识在 `cinematography.md`、`styles-and-visuals.md`、`prompt-patterns.md` 和 `continuity-and-transitions.md`。

## 1. 能力对照

| 能力 | Seedance | Agnes Video 2.5 Flash |
|---|---|---|
| 默认模型 | `doubao-seedance-2-0-260128` | `agnes-video-2.5-flash` |
| 时长 | 4–15 秒（1.0 为 4–12 秒） | 4–12 秒 |
| 分辨率 | 480p / 720p / 1080p | 仅 720P |
| 画幅 | 16:9、4:3、1:1、3:4、9:16、21:9、adaptive | 21:9、16:9、4:3、1:1、3:4、9:16 |
| 模式 | text / keyframe / reference | text / keyframe / reference |
| 首帧 | 支持 | 支持 |
| 尾帧 | 支持 | 支持 |
| 参考图 | 最多 9 张 | 最多 5 张 |
| 参考音频 | 最多 3 段 | 最多 3 段 |
| 参考视频 | 最多 3 段 | 不支持 |
| 本地文件 | 支持，转 data URL | 不支持，必须公网 URL |
| API Key | `ARK_API_KEY` | `AGNES_API_KEY` |
| Base URL | `ARK_BASE_URL` 可覆盖 | `AGNES_BASE_URL` 可覆盖 |

## 2. 通用语义到字段

| 通用语义 | Seedance | Agnes |
|---|---|---|
| 提示词 | `content[].text` | `prompt` |
| 时长 | `duration` 数字 | `seconds` 字符串 |
| 画幅 | `ratio` | `aspect_ratio` |
| 分辨率 | `resolution` 小写 p | `size` 固定 `720P` |
| 首帧 | `content[].image_url` + `role=first_frame` | `first_frame` |
| 尾帧 | `content[].image_url` + `role=last_frame` | `last_frame` |
| 参考图 | `content[].image_url` + `role=reference_image` | `images[]` |
| 参考音频 | `content[].audio_url` | `audios[]` |
| 参考视频 | `content[].video_url` | 不支持 |
| 任务 ID | `id` / `task_id` | `video_id` / `task_id` |
| 结果 URL | `content.video_url` | 顶层 `url` |
| 状态 | `succeeded` / `failed` 等 | `completed` / `failed` 等，统一归一化为 running/succeeded/failed |

## 3. 模式规则

### text

- 只提交文本。
- 不允许首帧、尾帧、参考图、参考音频、参考视频。

### keyframe

- 首帧和/或尾帧。
- 不允许同时提交参考图/参考音频/参考视频。
- 写清楚中间过程，不要只描述首尾两张图。

### reference

- 参考图/参考音频；Agnes 不支持参考视频。
- 不允许同时提交首帧/尾帧。
- 参考素材必须写清“继承什么 / 不继承什么”。

## 4. 本地素材与公网 URL

- Seedance：本地图片、视频、音频可以转 data URL；仍需注意文件大小限制。
- Agnes：所有媒体必须是公网可访问 URL；本地路径会在校验阶段被拒绝。
- 如果用户给本地文件而目标是 Agnes，必须先上传到对象存储或公网服务器。
- 不要把绝对本地路径写进提示词；提示词只描述素材内容，路径属于执行参数。

## 5. 轮询

- Seedance：轮询 `GET {base}/{task_id}`。
- Agnes：优先 `GET {origin}/agnesapi?video_id=...&model_name=...`。
- Agnes 查询频率过高会返回 HTTP 429；建议 15–20 秒一次，遇到 429 后退避。
- 不要重复创建任务来“重试查询”。

## 6. 选择建议

- 需要参考视频、较长时长、1080p：Seedance。
- 需要 4–12 秒、720P、首尾帧、参考图/音频、公网 URL：Agnes。
- 需要本地文件直接提交：Seedance。
- 需要跨 provider 统一流程：使用 `video-model-router`，不要各写一套创作流程。

## 7. 新 provider 接入

只实现 provider 契约中的能力声明、校验、请求构建、响应归一化。通用镜头词、提示词模板、连续性规则不得复制到 provider 适配器。
