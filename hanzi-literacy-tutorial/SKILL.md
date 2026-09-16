---
name: hanzi-literacy-tutorial
description: 制作 3-5 岁儿童汉字启蒙识字教程与配套动画。产出双页面交互教程（字卡/发音/笔顺/描红/配图游戏）+ 分幕动画，配图使用从 Wikimedia Commons 下载并逐张人工核验的真实照片（拒绝卡通失真影响儿童认知），笔顺数据本地化、完全离线可用。当用户要求制作识字教程、汉字学习页面、儿童识字动画或类似早教多媒体内容时使用。
---

# 汉字启蒙识字教程制作

为 3-5 岁儿童制作一套「真实照片 + 发音 + 笔顺 + 游戏」的识字教程与动画。

## 核心原则（不可妥协）

1. **照片必须真实**：只使用真实摄影作品（Wikimedia Commons CC 授权），不用 AI 生成图、插画、剪贴画——失真的图像会破坏幼儿对真实世界的认知。
2. **每张照片必须人工目检**：下载后用 Read 工具查看，确认 ① 真实摄影（非绘画/CG/拼贴）② 主体清晰突出、适合幼儿指认 ③ 无惊吓/不安全内容。不合格就换关键词重搜，宁可多轮迭代。
4. **完全离线可用**：笔顺数据内联为 JS（`window.STROKE_DATA`），不依赖 fetch——`file://` 协议下 Chrome 会拦截 fetch/XHR。库与照片全部本地化。
5. **逐字署名**：产出 `CREDITS.md`，记录每张照片的作者、授权、来源链接（CC BY / CC BY-SA 的署名要求）。

## 工作流

### 1. 选字

- 首选**象形字**（字形与实物直接对应：日月水火山木人口鱼鸟马牛羊…），4 岁以具象思维为主，图↔形对应最易建立；
- 笔画 2–8 画；指代具体（能拍到清晰真实照片）；贴近幼儿生活；
- 每字确定：拼音（声调符号）、配词（太阳/月亮…）、配词拼音、主题色、emoji、一句旁白（含字义 + 安全提示如需要，如「火很烫」）。

### 2. 下载真实照片

用 `scripts/commons_photos.py`（详见 `references/asset-sourcing.md`）：

```bash
# 搜索候选（先看标题清单再挑）
python3 scripts/commons_photos.py search "crescent moon night sky"
# 按 title 下载 + 抓取署名元数据
python3 scripts/commons_photos.py download --width 1000 --out assets/photos \
  --spec '{"yue": {"title": "File:Crescent Moon ESO.jpg"}}'
```

- 一次搜 2-3 组同义词，多轮下载候选并**逐张目检**挑选（常见淘汰原因：主体太小、太暗、有干扰物、剪影）；
- 拒绝绘画/扫描件（书页扫描、油画、地图常混入结果）。

### 3. 本地化笔顺数据

```bash
for ch in 日 月 水 火 山 木 人 口 鱼 鸟; do
  curl -s "https://cdn.jsdelivr.net/npm/hanzi-writer-data@2.0/$ch.json" -o "assets/strokes/$ch.json"
done
# 合并内联为 strokes-data.js（避免 file:// fetch 被拦截）
python3 - << 'EOF'
import json, glob, os
out = ["window.STROKE_DATA = {"]
for p in glob.glob("assets/strokes/*.json"):
    ch = os.path.basename(p)[:-5]
    out.append(f'"{ch}": ' + open(p).read() + ",")
out.append("};")
open("assets/strokes-data.js", "w").write("\n".join(out))
EOF
curl -s "https://cdn.jsdelivr.net/npm/hanzi-writer@3.2.0/dist/hanzi-writer.min.js" -o assets/hanzi-writer.min.js
```

### 4. 产出页面（从模板生成）

复制 `templates/index.html`（识字学堂）与 `templates/animation.html`（识字动画）到目标目录，**只需修改各自的 `HANZI` 数据数组**（模板已标注 `✏️ 自定义区`）：char/pinyin/word/wordPy/photo/tone/emoji/story。页面的其余逻辑（字卡、HanziWriter 笔顺/描红、语音、游戏、分幕播放）无需改动。

- 模板依赖：`assets/hanzi-writer.min.js`、`assets/strokes-data.js`、`assets/photos/<key>.jpg`
- 语音用 Web Speech API（zh-CN，rate≈0.8）；无声时字幕完整，不阻塞使用

### 5. 验证

```bash
# ① JS 语法 + 资源引用检查（抽出 <script> 跑 node --check；核对 assets 路径存在）
# ② 真实渲染检查
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --window-size=1100,1400 --screenshot=/tmp/check_index.png "file://$PWD/index.html"
```

用 Read 查看截图确认布局正常；再抽查 1-2 张照片最终目检。最后写 `README.md`（选字依据、教学法、家长建议）与 `CREDITS.md`。

## 教学法（看-听-认-玩）

每字四步，两个页面共享同一结构：**看**真实照片建立实物认知 → **听**拼音+配词（慢速中文语音）→ **认**笔顺逐笔演示/描红 → **玩**听音配图游戏（正反馈：星星+彩带；答错只鼓励不惩罚）。动画按「照片 Ken Burns → 字义旁白 → 笔顺书写 → 跟读」每幕 12-15 秒串成约 3 分钟的连贯故事。给家长的建议：每天 2-3 字、游戏中复习、真实环境中指认。
