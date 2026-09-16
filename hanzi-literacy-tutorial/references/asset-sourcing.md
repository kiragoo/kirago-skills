# 真实照片搜源指南（Wikimedia Commons）

## API 要点

搜索（返回 title/尺寸/缩略图 URL）：

```
https://commons.wikimedia.org/w/api.php?action=query&format=json
  &generator=search&gsrsearch=<urlencoded 关键词>%20filetype:bitmap
  &gsrnamespace=6&gsrlimit=12
  &prop=imageinfo&iiprop=url|size|mime&iiurlwidth=1000
```

- `gsrnamespace=6` 限定 File 命名空间；`filetype:bitmap` 排除视频/PDF 但**排除不了绘画和书页扫描**，靠人工目检过滤
- 缩略图取 `imageinfo[0].thumburl`（iiurlwidth 指定宽度，1000px 足够页面使用，单张 <700KB）
- 署名信息：`iiprop` 加 `extmetadata|descriptionurl`，读 `extmetadata.Artist` / `extmetadata.LicenseShortName`（值内含 HTML 标签，需正则剥除）
- 必须带 `User-Agent` 头，否则可能被限流；连续请求间 sleep 2s
- 有些标题带全角括号/省略号，直接传完整 title 即可；查不到时用搜索 API 拿准确 title（返回结果可能被截断）

## 搜索词经验

| 主题 | 好用的词 | 常见坑 |
|---|---|---|
| 月 | `crescent moon astrophotography`、`Crescent Moon ESO` | 普通夜空照片月亮太小/太暗，选天文摄影特写 |
| 水 | `crystal clear water lagoon Plitvice` | 溪流照常偏暗，选碧色湖水/泻湖 |
| 木/树 | `oak tree June`、`lone oak tree meadow` | 大量书页扫描（bulletin/Bulletin 1901 等）混入；仰拍只剩树冠的不行，要树干+树冠完整 |
| 鸟 | `sparrow closeup perched` | 鸟在画面中太小的淘汰 |
| 人 | `children running` | 淘汰剪影、背影、人脸过小 |
| 口 | `young girl smiling with teeth` | 直接搜 mouth 会出鳄鱼/河马/罐子 |

通用技巧：主体应占画面主体位置、光线明亮、背景干净；同义词多搜几轮，一次下载 2-3 个候选目检后再定。

## 常见 `filetype:bitmap` 之外需要警惕的

- 书籍扫描件（标题含年份数字如 `(1901) (19879295544)` 的多为 BHL/Internet Archive 扫描）
- 油画/版画（`Google Art Project`、`- Flickr -` 不代表照片，仍需目检）
- 地图、X 光、显微图（.mime 是 jpg 但不是目标实物）

## 淘汰案例记录（来自实际项目）

- `Rising Crescent Moon.jpg` — 月亮只占画面 3%，太暗
- `Dülmen, Wildpark, Eiche am Herzteich -- 2022 -- 4625.jpg` — 仰拍只有树冠，看不出「一棵树」
- `Sparrow on a branch.jpg` — 麻雀太小，背景全虚化
- `Running Girl.jpg` — 逆光剪影，看不见五官，不利于「人」的认知
- `Lone - Flickr - zenera.jpg` — 前景围栏和马干扰主体

## 授权与署名

- 只选 CC BY / CC BY-SA / CC0 / Public domain；记录到 `CREDITS.md`（字、照片标题+链接、作者、协议）
- CC BY-SA 注意：产出若二次分发照片需以相同方式共享
- 人物照片（儿童肖像）在幼儿教材语境下使用合理，但保留来源链接以备查
