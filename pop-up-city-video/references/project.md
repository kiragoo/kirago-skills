# 城市场景与导出

在项目工作目录新建 city.json 和单独的 artwork 目录；不要修改 Skill 目录内的引擎。以 [city.example.json](city.example.json) 为结构示例，用实际主题、地标、坐标和文件名替换。所有图片文件名直接写本地文件名，不写目录、URL 或跨目录引用。

- `slug` 是短英文小写文件名标识；`title` 是开场片名，`subtitle` 是副标题，`closing` 是收尾片名。默认结尾为夜景。
- `duration` 为 8–180 整秒，`fps` 为 12–60 整数。默认 50 秒 / 24 fps；一处地标至少留一个短镜头，站数多时延长时长。默认 9:16，支持 16:9、1:1、4:5 和 3:4。可加 `"size":[1080,1920]` 覆盖分辨率，必须与画幅严格一致。
- `art.map`、`art.desk`、`art.paper` 必填；地标数组依播放顺序放入 1–8 项。各项 `image` 必须有可用透明通道。
- 地图展开后的尺寸是 10.8×7.68：x 向右，z 向底图图片下方。若地标对应原图中的归一化位置 u、v（均 0–1），换算为 x=(u−0.5)×10.8、z=(v−0.5)×7.68，避开画边和折痕。地标主要活动范围建议 x∈[-4.65,4.65]、z∈[-3.02,3.02]。`width` 是地图单位，图片按原比例缩放，高度最多 2.8。
- `lamps` 是可选的 [[x,y],…]，表示相对图片水平中心的位置和从底部向上的归一化高度；应落在纹理的真实窗灯上。未填写使用两处默认灯点，空数组关闭可见灯珠。场景点光仍负责入夜时照亮纸面。
- 树木和移动物件均可省略。前景贴图写在 `art.greenery`，位置写在 `greenery` 数组，每项 [x,z,高度]。移动物件使用 `moving`，`motion` 可用 ground 或 water；路径必须贴地图的道路或河面。
- 默认镜头按地标生成；换机位优先看已编译项目的 `scene.json`。要让镜头随配置重编译，可在 `city.json` 中加 `shots`。每项为 start/end（秒）、p（起终点相机位置的两组 [x,y,z]）、l（起终点相机目标的两组 [x,y,z]）、f（起终点垂直视角）；start=0，所有片段相接，最后 end 等于成片时长。覆盖相机不会改变地标立起事件；若手动调事件，也同步核对 rise、title、on 以及 previewTimes。

## 运行

依赖 Python 3 + Pillow、Node.js、Playwright Chromium、FFmpeg/ffprobe。先检查是否已可用；缺依赖时只在用户允许的项目环境按需安装，不改全局配置。安装好依赖后：

```sh
python "<skill>/scripts/build_project.py" --city city.json --art artwork --out city-film
cd city-film
npm install
npx playwright install chromium
node render.mjs preview
node render.mjs clip 0 4
node render.mjs video
```

已准备好的 Chromium 可通过 `CHROME_PATH` 指定；慢机器可将 `RENDER_WORKERS` 设为 1。网页预览可用本地静态服务器访问 `index.html?preview=1`。渲染只加载本地图片和随包 Three.js；输出写入 `output/`。调整后可用 `node render.mjs preview 2.4 7.8 18` 快速看指定时刻。

验证 `ffprobe` 的画幅、帧率、时长以及 `nb_frames=duration×fps`；用 `ffmpeg -v error -i <file> -f null -` 解码检查。上传前查目标渠道文件限制。必要时二次压缩保留时长和帧数的轻量版，原文件不覆盖。
