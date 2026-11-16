#!/usr/bin/env python3
"""Build the technology and contact pills in assets/pills/ as static SVG files.

Each pill is an icon plus a label, drawn twice: <slug>-light.svg and
<slug>-dark.svg (the README picks one with <picture>). Labels are converted to
outlines, so the pills look the same on every machine and need no web font.
Logos are drawn in their brand colour; a brand colour that would vanish on one
theme (black logos on the dark page, pale ones on the white page) has its own
value for that theme.

Usage:
    python3 tools/build_pills.py --font path/to/DarkerGrotesque[wght].ttf \
        --icons path/to/simple-icons/icons

Font: Darker Grotesque (OFL). Logos: Simple Icons (CC0). See design/credits.md.
To add a pill, add a row to PILLS, run the script and add the printed
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

ACCENT = "#FF6B00"
ON_ACCENT = "#1a0d00"

# Icons drawn on the Simple Icons 24 x 24 grid.
ENVELOPE = (
    "M2 4h20a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1z"
    "m1.6 2 8.4 6.3L20.4 6H3.6zM21 7.25l-9 6.75-9-6.75V18h18V7.25z"
)

# slug, label, icon (Simple Icons name, or a path from above), kind, colour on light, colour on dark
PILLS = [
    # tools
    ("claude-code", "Claude Code", "claude", "tech", "#D97757", "#D97757"),
    ("chatgpt", "ChatGPT", "openai", "tech", "#000000", "#ffffff"),
    ("gemini", "Gemini", "googlegemini", "tech", "#8E75B2", "#A992D0"),
    ("perplexity", "Perplexity", "perplexity", "tech", "#1FB8CD", "#1FB8CD"),
    ("python", "Python", "python", "tech", "#3776AB", "#5A9FD4"),
    ("django", "Django", "django", "tech", "#092E20", "#44B78B"),
    ("php", "PHP", "php", "tech", "#777BB4", "#8F93D1"),
    ("javascript", "JavaScript", "javascript", "tech", "#E5C300", "#F7DF1E"),
    ("react", "React", "react", "tech", "#087EA4", "#61DAFB"),
    ("nextjs", "Next.js", "nextdotjs", "tech", "#000000", "#ffffff"),
    ("html", "HTML", "html5", "tech", "#E34F26", "#E34F26"),
    ("css", "CSS", "css", "tech", "#663399", "#A77BDA"),
    ("docker", "Docker", "docker", "tech", "#2496ED", "#2496ED"),
    ("nginx", "Nginx", "nginx", "tech", "#009639", "#2DBA5C"),
    ("linux", "Linux", "linux", "tech", "#000000", "#FCC624"),
    ("git", "Git", "git", "tech", "#F05032", "#F05032"),
    ("github", "GitHub", "github", "tech", "#181717", "#ffffff"),
    # contact
    ("email", "info@iluxa-web.com", ENVELOPE, "primary", ON_ACCENT, ON_ACCENT),
    ("linkedin", "LinkedIn", "linkedin", "tech", "#0A66C2", "#4C9BE8"),
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
    "light": {"ink": "#1f2328", "border": "#d1d9e0"},
    "dark": {"ink": "#f0f6fc", "border": "#3d444d"},
}


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


def icon_path(icons: Path, icon: str) -> str:
    if icon.startswith("M"):
        return icon
    svg = (icons / f"{icon}.svg").read_text(encoding="utf-8")
    found = re.search(r'<path d="([^"]+)"', svg)
    if not found:
        raise SystemExit(f"no path in {icon}.svg")
    return found.group(1)


def round_path(data: str) -> str:
    return re.sub(r"-?\d+\.\d+", lambda m: f"{float(m.group()):.2f}".rstrip("0").rstrip("."), data)


def build(font: TTFont, icons: Path, out: Path) -> None:
    cap_height = font["OS/2"].sCapHeight * FONT_SIZE / font["head"].unitsPerEm
    baseline = (HEIGHT + cap_height) / 2
    for slug, label, icon_name, kind, light_colour, dark_colour in PILLS:
        icon = icon_path(icons, icon_name)
        text_x = PAD_X + ICON + GAP
        text, text_width = label_path(font, label, text_x, baseline)
        width = round(text_x + text_width + PAD_X)
        icon_scale = ICON / 24
        icon_y = (HEIGHT - ICON) / 2
        for theme, colours in THEMES.items():
            icon_ink = light_colour if theme == "light" else dark_colour
            ink = colours["ink"]
            if kind == "primary":
                box = f'<rect width="{width}" height="{HEIGHT}" rx="{RADIUS}" fill="{ACCENT}"/>'
                ink = ON_ACCENT
            else:
                box = (
                    f'<rect x="0.5" y="0.5" width="{width - 1}" height="{HEIGHT - 1}" '
                    f'rx="{RADIUS - 0.5}" fill="none" stroke="{colours["border"]}"/>'
                )
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
