"""Render docs/demo.gif — the README's 15-second demo, from a real run.

The script does NOT hand-write the terminal output: it executes
``examples/demo.py`` in a subprocess and animates whatever that run printed.
If the library's behaviour changes, the GIF changes with it, or the render
fails — it cannot drift into showing a result the code no longer produces.

    pip install Pillow
    python docs/make_demo_gif.py

Verdict words are coloured after the fact by matching the exact strings the
gate can return; anything unrecognised stays plain white rather than being
guessed at.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "demo.gif"

FONT_PATH = "/System/Library/Fonts/Menlo.ttc"
FONT_SIZE = 17
LINE_H = 25
PAD = 22
WIDTH = 900

BG = (13, 17, 23)
FG = (201, 209, 217)
DIM = (110, 122, 136)
PROMPT = (126, 231, 135)
BAD = (248, 113, 113)
GOOD = (125, 211, 252)
ACCENT = (250, 204, 21)

# verdict -> colour. Only the verdicts the library actually returns.
VERDICT_COLOURS = {
    "not_found": BAD,
    "misattributed": BAD,
    "supports": GOOD,
    "partial": ACCENT,
    "unrelated": ACCENT,
    "contradicts": BAD,
}

HOLD_LAST = 30  # frames to hold the final screen before looping
DWELL_VERDICT = 9  # a verdict line stays up long enough to be read
DWELL_COMMAND = 6
FRAME_MS = 110


def real_output() -> list[str]:
    """Run the demo for real and return its printed lines."""
    proc = subprocess.run(
        [sys.executable, str(ROOT / "examples" / "demo.py")],
        capture_output=True, text=True, check=True, cwd=ROOT,
    )
    return proc.stdout.rstrip("\n").split("\n")


def script_lines() -> list[str]:
    return [
        "$ pip install git+https://github.com/tonydzi/verbatim-citation-gate",
        "$ python examples/demo.py",
        "",
        *real_output(),
    ]


def draw_frame(lines: list[str], font: ImageFont.FreeTypeFont, height: int) -> Image.Image:
    img = Image.new("RGB", (WIDTH, height), BG)
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        y = PAD + i * LINE_H
        if line.startswith("$ "):
            d.text((PAD, y), "$", font=font, fill=PROMPT)
            d.text((PAD + font.getlength("$ "), y), line[2:], font=font, fill=FG)
            continue
        if line.strip().startswith(("claim:", "quote:")):
            colour = DIM
        elif "citations audited" in line:
            colour = ACCENT
        else:
            colour = FG
        d.text((PAD, y), line, font=font, fill=colour)
        # recolour the verdict token in "  -> <verdict> ..." lines
        stripped = line.lstrip()
        if stripped.startswith("-> "):
            word = stripped[3:].split(" ", 1)[0]
            if word in VERDICT_COLOURS:
                x = PAD + font.getlength(line[: len(line) - len(stripped) + 3])
                d.text((x, y), word, font=font, fill=VERDICT_COLOURS[word])
    return img


def main() -> None:
    lines = script_lines()
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    height = PAD * 2 + LINE_H * len(lines)

    # One frame per revealed line, with a dwell on the lines a reader has to
    # actually read: the two commands and each verdict.
    frames: list[Image.Image] = []
    for n in range(1, len(lines) + 1):
        frame = draw_frame(lines[:n], font, height)
        last = lines[n - 1].strip()
        dwell = DWELL_VERDICT if last.startswith("-> ") else (
            DWELL_COMMAND if last.startswith("$ ") else 1)
        frames += [frame] * dwell
    frames += [frames[-1]] * HOLD_LAST

    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUT, save_all=True, append_images=frames[1:],
        duration=FRAME_MS, loop=0, optimize=True,
    )
    kb = OUT.stat().st_size / 1024
    print(f"{OUT.relative_to(ROOT)}: {len(frames)} frames, {WIDTH}x{height}, {kb:.0f} KB")


if __name__ == "__main__":
    main()
