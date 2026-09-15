#!/usr/bin/env python3
# 把「原图 + 图生视频」配成苹果实况照片（Live Photo）：导入「照片」App 后可在抖音发「图文·实况」
# 用法：python3 make_live.py --pairs 原图1.png 视频1.mp4 [原图2.png 视频2.mp4 ...] --out 输出目录
#        [--names 名字1 名字2 ...] [--seconds 3] [--fit speed|trim|pingpong] [--aspect keep|3:4] [--still video|image]
#   --fit speed     超长时整体加速到目标时长，首尾帧不变（首尾帧同图的视频可以无缝循环）
#   --fit trim      直接截取前几秒
#   --fit pingpong  取前一半时长正放再倒放，首尾必然相接（适合首尾对不上的视频）
#   --still video   封面用视频第一帧，起播不跳（默认）；image 用原图，分辨率更高但可能有色差
# 依赖：ffmpeg、ffprobe、makelive（pip install makelive，仅 macOS）
import argparse
import json
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageEnhance, ImageFilter


def run(cmd):
    subprocess.run(cmd, check=True)


def probe(video):
    """读出视频的宽、高、时长"""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height:format=duration", "-of", "json", video],
        check=True, capture_output=True, text=True).stdout
    info = json.loads(out)
    s = info["streams"][0]
    return s["width"], s["height"], float(info["format"]["duration"])


def canvas_size(w, h, aspect):
    """按目标比例算画布尺寸：原画面完整放在中间，不裁切"""
    if aspect == "keep":
        return w, h
    aw, ah = map(int, aspect.split(":"))
    if w / h > aw / ah:          # 原画面更宽：宽度不变，补高度
        return w, round(w * ah / aw / 2) * 2
    return round(h * aw / ah / 2) * 2, h


def pad_still(img, aspect):
    """把图片放进目标比例的画布，背景用画面本身放大、模糊、稍压暗后填满"""
    w, h = img.size
    W, H = canvas_size(w, h, aspect)
    if (W, H) == (w, h):
        return img
    # 和视频补边同一做法：缩小、模糊、放大，只剩柔和的颜色
    sw, sh = max(2, W // 16), max(2, H // 16)
    scale = max(sw / w, sh / h)
    small = img.resize((max(1, round(w * scale)), max(1, round(h * scale))))
    left, top = (small.width - sw) // 2, (small.height - sh) // 2
    bg = small.crop((left, top, left + sw, top + sh)).filter(ImageFilter.GaussianBlur(4))
    bg = bg.resize((W, H), Image.BICUBIC)
    bg = ImageEnhance.Brightness(bg).enhance(0.96)
    bg.paste(img, ((W - w) // 2, (H - h) // 2))
    return bg


def first_frame(video, path):
    """取视频第一帧"""
    run(["ffmpeg", "-y", "-v", "error", "-i", video, "-frames:v", "1", "-update", "1", path])
    return Image.open(path).convert("RGB")


def make_video(src, dst, seconds, fit, aspect):
    w, h, dur = probe(src)
    W, H = canvas_size(w, h, aspect)
    graph = []
    if fit == "pingpong":
        half = min(seconds / 2, dur)
        graph.append(f"[0:v]trim=0:{half:.3f},setpts=PTS-STARTPTS,split[f][r];"
                     f"[r]reverse[rv];[f][rv]concat=n=2:v=1[v0]")
    elif fit == "speed" and dur > seconds:
        graph.append(f"[0:v]setpts=PTS*{seconds / dur:.6f}[v0]")
    else:
        graph.append("[0:v]null[v0]")
    if (W, H) == (w, h):
        graph.append("[v0]format=yuv420p[out]")
    else:
        # 上下补边：画面先缩到很小再模糊、放大，只剩一片柔和的颜色，认不出放大的人和物；原画面居中
        sw, sh = max(2, W // 16 // 2 * 2), max(2, H // 16 // 2 * 2)
        graph.append(f"[v0]split[a][b];"
                     f"[a]scale={sw}:{sh}:force_original_aspect_ratio=increase,crop={sw}:{sh},"
                     f"boxblur=6:3,scale={W}:{H}:flags=bicubic,eq=brightness=-0.04:saturation=0.9[bg];"
                     f"[bg][b]overlay=(W-w)/2:(H-h)/2,format=yuv420p[out]")
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", src, "-filter_complex", ";".join(graph),
           "-map", "[out]", "-an", "-c:v", "libx264", "-crf", "16", "-preset", "slow",
           "-movflags", "+faststart"]
    if fit == "trim" and dur > seconds:
        cmd += ["-t", str(seconds)]
    run(cmd + [dst])


def main():
    ap = argparse.ArgumentParser(description="原图 + 视频 → 苹果实况照片")
    ap.add_argument("--pairs", nargs="+", required=True, help="成对给出：原图 视频 原图 视频 …")
    ap.add_argument("--out", required=True, help="输出目录")
    ap.add_argument("--names", nargs="*", help="每对的输出名字（不含扩展名）")
    ap.add_argument("--seconds", type=float, default=3.0, help="实况视频目标时长，默认 3 秒")
    ap.add_argument("--fit", choices=["speed", "trim", "pingpong"], default="speed")
    ap.add_argument("--aspect", default="keep", help="keep 保持原比例，或如 3:4")
    ap.add_argument("--still", choices=["video", "image"], default="video", help="封面用视频第一帧还是原图")
    args = ap.parse_args()

    if len(args.pairs) % 2:
        sys.exit("--pairs 需要成对给出：原图 视频")
    if not shutil.which("makelive"):
        sys.exit("没找到 makelive，请先 pip install makelive")
    os.makedirs(args.out, exist_ok=True)
    pairs = list(zip(args.pairs[0::2], args.pairs[1::2]))
    names = args.names or [os.path.splitext(os.path.basename(v))[0] for _, v in pairs]

    for (image, video), name in zip(pairs, names):
        still = os.path.join(args.out, f"{name}.jpg")
        mov = os.path.join(args.out, f"{name}.mov")
        make_video(video, mov, args.seconds, args.fit, args.aspect)
        if args.still == "video":
            # 封面直接取成品视频的第一帧，连补边背景都和视频一模一样，起播不跳
            tmp = os.path.join(args.out, f".{name}_first.png")
            first_frame(mov, tmp).save(still, quality=95)
            os.remove(tmp)
        else:
            pad_still(Image.open(image).convert("RGB"), args.aspect).save(still, quality=95)
        # 写入配对标记，让「照片」App 认成实况照片
        run(["makelive", still, mov])
        print("已生成实况照片：", still, "+", mov)


if __name__ == "__main__":
    main()
