#!/usr/bin/env python3
"""Build the technology and contact pills in assets/pills/ as static SVG files.

Each pill is an icon plus a label, drawn twice: <slug>-light.svg and
<slug>-dark.svg (the README picks one with <picture>). Labels are converted to
outlines, so the pills look the same on every machine and need no web font.

Usage:
    python3 tools/build_pills.py --font path/to/DarkerGrotesque[wght].ttf \
        --icons path/to/simple-icons/icons

Font: Darker Grotesque (OFL). Icons: Simple Icons (CC0). See design/credits.md.
To add a technology, add a row to PILLS, run the script and add the printed
<picture> block to README.md.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

# slug, label, Simple Icons file name, kind
PILLS = [
    ("python", "Python", "python", "tech"),
    ("django", "Django", "django", "tech"),
    ("php", "PHP", "php", "tech"),
    ("javascript", "JavaScript", "javascript", "tech"),
    ("react", "React", "react", "tech"),
    ("nextjs", "Next.js", "nextdotjs", "tech"),
    ("html", "HTML", "html5", "tech"),
    ("css", "CSS", "css", "tech"),
    ("docker", "Docker", "docker", "tech"),
    ("git", "Git", "git", "tech"),
    ("github", "GitHub", "github", "tech"),
    ("claude-code", "Claude Code", "claude", "tech"),
    ("chatgpt", "ChatGPT", "openai", "tech"),
    ("gemini", "Gemini", "googlegemini", "tech"),
    ("perplexity", "Perplexity", "perplexity", "tech"),
    ("email", "info@iluxa-web.com", None, "primary"),
    ("linkedin", "LinkedIn", "linkedin", "tech"),
]

HEIGHT = 36
MARGIN_Y = 3  # empty space above and below, so wrapped rows do not touch
PAD_X = 13
ICON = 16
GAP = 8
FONT_SIZE = 18
WEIGHT = 700
TRACKING = 0.2
RADIUS = 9

THEMES = {
    "light": {"ink": "#1f2328", "icon": "#59636e", "border": "#d1d9e0"},
    "dark": {"ink": "#f0f6fc", "icon": "#9198a1", "border": "#3d444d"},
}
ACCENT = "#FF6B00"
ON_ACCENT = "#1a0d00"

# An envelope drawn on the Simple Icons 24 x 24 grid, for the email pill.
ENVELOPE = (
    "M2 4h20a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1z"
    "m1.6 2 8.4 6.3L20.4 6H3.6zM21 7.25l-9 6.75-9-6.75V18h18V7.25z"
)


def label_path(font: TTFont, text: str, x: float, baseline: float) -> tuple[str, float]:
    """Return the SVG path data for `text` and the width it takes."""
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    scale = FONT_SIZE / font["head"].unitsPerEm
    parts = []
    cursor = x
    for char in text:
        name = cmap.get(ord(char))
        if name is None:
            raise SystemExit(f"font has no glyph for {char!r}")
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, cursor, baseline)))
        commands = pen.getCommands()
        if commands:
            parts.append(commands)
        cursor += glyphs[name].width * scale + TRACKING
    return " ".join(parts), cursor - TRACKING - x


def icon_path(icons: Path, name: str) -> str:
    svg = (icons / f"{name}.svg").read_text(encoding="utf-8")
    found = re.search(r'<path d="([^"]+)"', svg)
    if not found:
        raise SystemExit(f"no path in {name}.svg")
    return found.group(1)


def round_path(data: str) -> str:
    return re.sub(r"-?\d+\.\d+", lambda m: f"{float(m.group()):.2f}".rstrip("0").rstrip("."), data)


def build(font: TTFont, icons: Path, out: Path) -> None:
    ascender = font["OS/2"].sCapHeight * FONT_SIZE / font["head"].unitsPerEm
    baseline = (HEIGHT + ascender) / 2
    for slug, label, icon_name, kind in PILLS:
        icon = ENVELOPE if icon_name is None else icon_path(icons, icon_name)
        text_x = PAD_X + ICON + GAP
        text, text_width = label_path(font, label, text_x, baseline)
        width = round(text_x + text_width + PAD_X)
        icon_scale = ICON / 24
        icon_y = (HEIGHT - ICON) / 2
        for theme, colours in THEMES.items():
            if kind == "primary":
                box = f'<rect width="{width}" height="{HEIGHT}" rx="{RADIUS}" fill="{ACCENT}"/>'
                ink = icon_ink = ON_ACCENT
            else:
                box = (
                    f'<rect x="0.5" y="0.5" width="{width - 1}" height="{HEIGHT - 1}" '
                    f'rx="{RADIUS - 0.5}" fill="none" stroke="{colours["border"]}"/>'
                )
                ink, icon_ink = colours["ink"], colours["icon"]
            svg = (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{HEIGHT + 2 * MARGIN_Y}" '
                f'viewBox="0 {-MARGIN_Y} {width} {HEIGHT + 2 * MARGIN_Y}" role="img" aria-label="{label}">'
                f"<title>{label}</title>{box}"
                f'<path fill="{icon_ink}" transform="translate({PAD_X} {icon_y}) scale({icon_scale:.4f})" d="{icon}"/>'
                f'<path fill="{ink}" d="{round_path(text)}"/></svg>\n'
            )
            (out / f"{slug}-{theme}.svg").write_text(svg, encoding="utf-8")
        print(
            f'<picture><source media="(prefers-color-scheme: dark)" srcset="./assets/pills/{slug}-dark.svg">'
            f'<img src="./assets/pills/{slug}-light.svg" height="{HEIGHT + 2 * MARGIN_Y}" alt="{label}"></picture>'
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--font", required=True, type=Path)
    parser.add_argument("--icons", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "assets" / "pills")
    args = parser.parse_args()
    font = TTFont(args.font)
    if "fvar" in font:
        font = instantiateVariableFont(font, {"wght": WEIGHT})
    args.out.mkdir(parents=True, exist_ok=True)
    build(font, args.icons, args.out)


if __name__ == "__main__":
    main()
