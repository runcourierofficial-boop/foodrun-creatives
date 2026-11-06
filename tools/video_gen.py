#!/usr/bin/env python3
"""
Build a 9:16 Reels/Stories ad video from generated creatives.
Usage: python3 video_gen.py out/ "zinger549,pizzarun699,triplecrunch2399" video.mp4 [seconds_per_card=3]
Each card gets a slow Ken Burns zoom + crossfade. Silent (Meta adds music optionally; we keep 'Add music' off).
"""
import os, subprocess, sys

def main():
    out_dir, ids, dst = sys.argv[1], sys.argv[2].split(","), sys.argv[3]
    dur = float(sys.argv[4]) if len(sys.argv) > 4 else 3.0
    fps = 30
    frames = int(dur * fps)
    inputs, filters, labels = [], [], []
    for i, cid in enumerate(ids):
        p = os.path.join(out_dir, f"{cid}_9x16.jpg")
        assert os.path.exists(p), p
        inputs += ["-i", p]  # single frame; zoompan d=frames expands it to `dur` seconds
        # zoompan: slow zoom 1.0 -> 1.08
        filters.append(
            f"[{i}:v]scale=1080:1920,zoompan=z='min(zoom+0.0008,1.08)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps},format=yuv420p[v{i}]"
        )
        labels.append(f"[v{i}]")
    # crossfade chain
    xf = 0.5
    chain = ""
    prev = "[v0]"
    for i in range(1, len(ids)):
        offset = i * dur - i * xf
        outl = f"[x{i}]" if i < len(ids) - 1 else "[vout]"
        chain += f"{prev}[v{i}]xfade=transition=fade:duration={xf}:offset={offset:.2f}{outl};"
        prev = outl
    if len(ids) == 1:
        chain = "[v0]copy[vout];"
    fc = ";".join(filters) + ";" + chain.rstrip(";")
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[vout]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(fps), "-movflags", "+faststart", dst]
    subprocess.run(cmd, check=True, capture_output=True)
    print("wrote", dst)

if __name__ == "__main__":
    main()
