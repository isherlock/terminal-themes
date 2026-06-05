#!/usr/bin/env python3
"""Ingest *.itermcolors files into normalized theme data for the gallery.

Reads themes-src/*.itermcolors (curated/custom themes, committed) and then
corpus/*.itermcolors (the vendored mbadolato corpus, gitignored — fetch with
tools/fetch_corpus.sh), converts each colour to #rrggbb, dedups by display
name (curated wins), and writes:
  - data/themes.json  (pretty JSON array)
  - data/themes.js    (window.THEMES = <same array>;)

Run:  python3 tools/build_themes.py
"""

import json
import plistlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "themes-src"       # curated/custom, committed
CORPUS_DIR = ROOT / "corpus"        # full mbadolato corpus, gitignored
DATA_DIR = ROOT / "data"


def comp_to_255(c):
    """Clamp a 0..1 float component to an 8-bit int 0..255."""
    return max(0, min(255, round(float(c) * 255)))


# --- colour-space handling -------------------------------------------------
# iTerm colours carry a per-component "Color Space": sRGB, P3, or Calibrated
# (and ~150 files omit it, which means Apple Calibrated/Generic RGB). sRGB and
# Calibrated are used as-is (Calibrated ≈ sRGB for our purposes); P3 is wide
# gamut and must be converted or it renders noticeably off.

def _srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c):
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


# Display P3 (D65) linear -> sRGB (D65) linear.
_P3_TO_SRGB = (
    (1.2249401, -0.2249404, 0.0000000),
    (-0.0420569, 1.0420571, 0.0000000),
    (-0.0196376, -0.0786361, 1.0982735),
)


def _p3_to_srgb(r, g, b):
    lr, lg, lb = _srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b)
    out = []
    for row in _P3_TO_SRGB:
        out.append(row[0] * lr + row[1] * lg + row[2] * lb)
    return tuple(_linear_to_srgb(x) for x in out)


def color_to_hex(d):
    """Convert an iTerm colour dict to '#rrggbb', honouring its Color Space."""
    if d is None:
        return None
    r = float(d.get("Red Component", 0))
    g = float(d.get("Green Component", 0))
    b = float(d.get("Blue Component", 0))
    space = (d.get("Color Space") or "").strip().lower()
    if space in ("p3", "display p3"):
        r, g, b = _p3_to_srgb(r, g, b)
    return f"#{comp_to_255(r):02x}{comp_to_255(g):02x}{comp_to_255(b):02x}"


def luminance(hex_str):
    """Perceptual luminance 0..1 from an #rrggbb string (simple v1 weights)."""
    r = int(hex_str[1:3], 16) / 255
    g = int(hex_str[3:5], 16) / 255
    b = int(hex_str[5:7], 16) / 255
    return 0.299 * r + 0.587 * g + 0.114 * b


def nice_name(filename):
    """Derive a display name from the filename: strip ext, underscores/dashes
    -> spaces, title-case words that look lowercase while keeping nice casing."""
    stem = Path(filename).stem
    stem = stem.replace("_", " ").replace("-", " ")
    parts = []
    for w in stem.split():
        parts.append(w if w != w.lower() else w.capitalize())
    return " ".join(parts)


def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower().strip())
    return re.sub(r"-+", "-", s).strip("-")


def build_theme(path):
    with open(path, "rb") as fh:
        pl = plistlib.load(fh)

    def col(key):
        return color_to_hex(pl.get(key))

    bg = col("Background Color") or "#000000"
    fg = col("Foreground Color") or "#ffffff"
    ansi = [col(f"Ansi {i} Color") for i in range(16)]
    variant = "light" if luminance(bg) > 0.5 else "dark"

    return {
        "name": nice_name(path.name),
        "source": path.name,
        "variant": variant,
        "bg": bg,
        "fg": fg,
        "cursor": col("Cursor Color"),
        "cursorText": col("Cursor Text Color"),
        "selection": col("Selection Color"),
        "selectionText": col("Selected Text Color"),
        "bold": col("Bold Color"),
        "link": col("Link Color"),
        "ansi": ansi,
    }


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    themes = []
    skipped = []
    seen = set()  # dedup by display-name slug; first (curated) wins

    # themes-src first so curated/custom versions take priority over the corpus
    files = sorted(SRC_DIR.glob("*.itermcolors")) + sorted(CORPUS_DIR.glob("*.itermcolors"))
    for path in files:
        try:
            theme = build_theme(path)
        except Exception as exc:  # noqa: BLE001 - report & skip, never block
            skipped.append((path.name, str(exc)))
            continue
        key = slugify(theme["name"])
        if key in seen:
            continue
        seen.add(key)
        themes.append(theme)

    # Sort: dark first, then light; alphabetical (case-insensitive) within each.
    order = {"dark": 0, "light": 1}
    themes.sort(key=lambda t: (order.get(t["variant"], 2), t["name"].lower()))

    (DATA_DIR / "themes.json").write_text(
        json.dumps(themes, indent=2) + "\n", encoding="utf-8"
    )
    (DATA_DIR / "themes.js").write_text(
        "window.THEMES = " + json.dumps(themes, indent=2) + ";\n",
        encoding="utf-8",
    )

    n_dark = sum(1 for t in themes if t["variant"] == "dark")
    n_light = sum(1 for t in themes if t["variant"] == "light")
    print(f"Converted {len(themes)} themes ({n_dark} dark, {n_light} light).")
    if skipped:
        print(f"Skipped {len(skipped)}:")
        for name, err in skipped:
            print(f"  - {name}: {err}")
    else:
        print("Skipped 0.")


if __name__ == "__main__":
    main()
