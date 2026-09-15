#!/usr/bin/env python3
# 给成图配竖排诗句：宋体细体诗句 + 粗体小标注，按每张图的留白位置排版，可选竖向拼接成长图
# 用法：python3 typeset_poem.py <配置.json> [--clean]
#   --clean  不画小标注，只保留诗句
# 配置里的坐标与字号：小于等于 1 的数按比例理解（相对宽/高），大于 1 按像素理解
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

DEFAULT_FONT = "/System/Library/Fonts/Supplemental/Songti.ttc"  # macOS 自带宋体；索引 3 为细体，1 为粗体


def rel(value, total):
    """小于等于 1 的数按比例换算成像素，否则原样返回"""
    return value * total if value <= 1 else value


def draw_column(draw, text, cx, top, font, size, track, fill):
    """竖排一列，每个字在自己的格子里居中；返回这一列的底边"""
    cell = size + track
    for i, ch in enumerate(text):
        draw.text((cx, top + i * cell + size / 2), ch, font=font, fill=fill, anchor="mm")
    return top + len(text) * cell - track


def typeset(img, frame, cfg, with_label):
    w, h = img.size
    # 所有间距都以诗句字号为单位，换分辨率时版式比例不变
    size = round(rel(cfg.get("size", 0.045), h))
    track = size * cfg.get("track", 0.27)
    col_gap = size * cfg.get("col_gap", 0.53)
    offset = size * cfg.get("offset", 0.63)
    lsize = round(size * cfg.get("label_size", 0.37))
    ltrack = lsize * cfg.get("label_track", 0.36)
    lgap = size * cfg.get("label_gap", 0.5)
    hair = size * cfg.get("hairline", 1.6)

    font_cfg = cfg.get("font", {})
    path = os.path.expanduser(font_cfg.get("path", DEFAULT_FONT))
    font_poem = ImageFont.truetype(path, size, index=font_cfg.get("poem_index", 3))
    font_label = ImageFont.truetype(path, lsize, index=font_cfg.get("label_index", 1))

    lines = frame["lines"]
    label = frame.get("label") if with_label else None
    n = len(lines)
    block_w = n * size + (n - 1) * col_gap + ((lgap + lsize) if label else 0)
    x = rel(frame["x"], w)
    right = x if frame.get("side", "right") == "right" else x + block_w
    top = rel(frame["y"], h)
    color = tuple(frame["color"])
    halo_color = tuple(frame.get("halo", (255, 255, 255)))

    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # 从右往左排：第一句在最右，偶数列下错一点，形成错落
    cx = right - size / 2
    last_cx, bottom = cx, top
    for i, line in enumerate(lines):
        col_top = top + (offset if i % 2 else 0)
        bottom = draw_column(d, line, cx, col_top, font_poem, size, track, color + (235,))
        last_cx = cx
        cx -= size + col_gap

    if label:
        # 标注与最后一列底部对齐，上方一条细线
        cx_l = last_cx - size / 2 - lgap - lsize / 2
        label_h = len(label) * (lsize + ltrack) - ltrack
        label_top = bottom - label_h
        draw_column(d, label, cx_l, label_top, font_label, lsize, ltrack, color + (200,))
        gap = size * 0.37
        d.line([(cx_l, label_top - gap - hair), (cx_l, label_top - gap)],
               fill=color + (140,), width=max(1, round(h / 670)))

    # 光晕：把文字形状模糊后，用画面里的浅色垫在字下面，让字从背景里轻轻浮出来
    mask = layer.split()[3].filter(ImageFilter.GaussianBlur(cfg.get("halo_blur", 0.3) * size))
    strength = cfg.get("halo_strength", 0.55)
    halo = Image.new("RGBA", (w, h), halo_color + (0,))
    halo.putalpha(mask.point(lambda v: int(v * strength)))

    out = Image.alpha_composite(img.convert("RGBA"), halo)
    out = Image.alpha_composite(out, layer)
    return out.convert("RGB")


def main():
    if len(sys.argv) < 2:
        print(__doc__ or "用法：python3 typeset_poem.py <配置.json> [--clean]")
        sys.exit(1)
    config_path = os.path.abspath(sys.argv[1])
    with_label = "--clean" not in sys.argv[2:]
    base = os.path.dirname(config_path)
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)

    def resolve(p):
        p = os.path.expanduser(p)
        return p if os.path.isabs(p) else os.path.join(base, p)

    out_dir = resolve(cfg.get("output_dir", "output"))
    os.makedirs(out_dir, exist_ok=True)
    suffix = "" if with_label else "_纯诗句"

    frames = []
    for i, frame in enumerate(cfg["frames"], start=1):
        img = Image.open(resolve(frame["image"]))
        out = typeset(img, frame, cfg, with_label)
        name = f"{i:02d}_{frame['lines'][0]}{suffix}.png"
        out.save(os.path.join(out_dir, name))
        frames.append(out)
        print("已输出", os.path.join(out_dir, name))

    if cfg.get("stitch", True) and len(frames) > 1:
        # 竖向拼接；宽度不一致时按第一张的宽度等比缩放
        w = frames[0].width
        frames = [f if f.width == w else f.resize((w, round(f.height * w / f.width))) for f in frames]
        sheet = Image.new("RGB", (w, sum(f.height for f in frames)))
        y = 0
        for f in frames:
            sheet.paste(f, (0, y))
            y += f.height
        stem, ext = os.path.splitext(cfg.get("stitch_name", "拼图.jpg"))
        sheet_path = os.path.join(out_dir, f"{stem}{suffix}{ext or '.jpg'}")
        sheet.save(sheet_path, quality=95)
        print("已输出", sheet_path)


if __name__ == "__main__":
    main()
