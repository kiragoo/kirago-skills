#!/usr/bin/env python3
"""Wikimedia Commons 真实照片搜索 / 下载 / 署名工具（识字教程素材获取）。

用法:
  # 搜索候选（打印标题清单，人工挑选后再下载）
  python3 commons_photos.py search "crescent moon night sky" [--limit 12]

  # 按完整 title 下载（自动抓取作者/授权写入 _credits.json）
  python3 commons_photos.py download --out assets/photos --width 1000 \
      --spec '{"yue": {"title": "File:Crescent Moon ESO.jpg"}}'

  --spec 支持 {"key": {"title": "...", "query": "备用搜索词"}}；
  title 404 时若提供 query 则自动搜索取第一个 jpg 结果（务必再人工目检）。
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "hanzi-literacy-tutorial/1.0 (educational project)"}
CREDITS_NAME = "_credits.json"


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout)


def _strip(html):
    return re.sub(r"<[^>]+>", "", html).strip()


def search(term, limit=12):
    q = urllib.parse.quote(term + " filetype:bitmap")
    url = ("https://commons.wikimedia.org/w/api.php?action=query&format=json"
           f"&generator=search&gsrsearch={q}&gsrnamespace=6&gsrlimit={limit}"
           "&prop=imageinfo&iiprop=url|size|mime&iiurlwidth=1000")
    d = json.load(_get(url))
    pages = d.get("query", {}).get("pages", {})
    rows = sorted(pages.values(), key=lambda p: p.get("index", 99))
    out = []
    for p in rows:
        ii = p.get("imageinfo", [{}])[0]
        if ii.get("mime") not in ("image/jpeg", "image/png"):
            continue
        out.append({
            "title": p["title"],
            "size": f"{ii.get('width')}x{ii.get('height')}",
            "thumburl": ii.get("thumburl") or ii.get("url"),
        })
    return out


def imageinfo(title):
    api = ("https://commons.wikimedia.org/w/api.php?action=query&format=json"
           f"&titles={urllib.parse.quote(title)}&prop=imageinfo"
           "&iiprop=url|extmetadata|descriptionurl&iiurlwidth=1000")
    d = json.load(_get(api))
    page = list(d["query"]["pages"].values())[0]
    if "imageinfo" not in page:
        return None
    ii = page["imageinfo"][0]
    em = ii.get("extmetadata", {})
    return {
        "thumburl": ii.get("thumburl") or ii["url"],
        "page": ii.get("descriptionurl", ""),
        "artist": _strip(em.get("Artist", {}).get("value", "")),
        "license": _strip(em.get("LicenseShortName", {}).get("value", "")),
    }


def download(spec, out_dir, width=1000):
    """spec: {key: {title, query?}} -> 下载照片 + 更新 _credits.json"""
    os.makedirs(out_dir, exist_ok=True)
    credits_path = os.path.join(out_dir, CREDITS_NAME)
    credits = []
    if os.path.exists(credits_path):
        credits = json.load(open(credits_path))
    done_keys = {c["key"] for c in credits}

    for key, item in spec.items():
        title = item.get("title")
        info = imageinfo(title) if title else None
        if info is None and item.get("query"):
            hits = search(item["query"], limit=3)
            if not hits:
                print(f"{key}: NOT FOUND (query={item['query']})", file=sys.stderr)
                continue
            title, info = hits[0]["title"], imageinfo(hits[0]["title"])
            print(f"{key}: fell back to search -> {title}  ⚠️ 务必人工目检", file=sys.stderr)
        if info is None:
            print(f"{key}: NOT FOUND ({title})", file=sys.stderr)
            continue

        thumb = info["thumburl"]
        if width != 1000 and "/thumb/" in thumb:
            thumb = re.sub(r"/(\d+)px-", f"/{width}px-", thumb)
        dest = os.path.join(out_dir, key + os.path.splitext(urllib.parse.urlparse(thumb).path)[1].lower() or ".jpg")
        with _get(thumb, timeout=60) as resp, open(dest, "wb") as f:
            f.write(resp.read())

        entry = {"key": key, "file": title, "page": info["page"],
                 "artist": info["artist"], "license": info["license"]}
        credits = [c for c in credits if c["key"] != key and c["key"] not in done_keys]
        credits.append(entry)
        done_keys.add(key)
        print(f"{key}: {os.path.getsize(dest) // 1024}KB  {info['license']}  <- {title}")
        time.sleep(1)  # 礼貌限速

    for c in credits:
        if c["key"] not in done_keys:
            done_keys.add(c["key"])  # 保留旧条目
    json.dump(credits, open(credits_path, "w"), ensure_ascii=False, indent=2)
    print(f"credits -> {credits_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="搜索候选照片（打印标题清单）")
    s.add_argument("term")
    s.add_argument("--limit", type=int, default=12)

    d = sub.add_parser("download", help="按 title 下载照片并抓取署名")
    d.add_argument("--spec", required=True, help='JSON: {"key": {"title": "File:...", "query": "备用"}}')
    d.add_argument("--out", default="assets/photos")
    d.add_argument("--width", type=int, default=1000)

    args = ap.parse_args()
    if args.cmd == "search":
        for i, r in enumerate(search(args.term, args.limit), 1):
            print(f"{i:2d} | {r['size']:>10} | {r['title']}")
    else:
        download(json.loads(args.spec), args.out, args.width)


if __name__ == "__main__":
    main()
