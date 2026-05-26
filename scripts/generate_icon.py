"""Generate the application icon (resources/icon.ico).

Run once when the visual identity changes. The output file is committed
so PyInstaller / users don't need Pillow at build time.

  python scripts/generate_icon.py
"""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw


# Apple Music brand pink.
ACCENT = (252, 60, 68)
WHITE = (255, 255, 255)


def render_square(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded squircle background.
    radius = int(size * 0.22)
    draw.rounded_rectangle(
        (0, 0, size, size), radius=radius, fill=ACCENT,
    )

    # White music note: two filled circles + two stems connected by a bar.
    # Coordinates relative to canvas so it scales with `size`.
    cx1 = int(size * 0.34)
    cy1 = int(size * 0.72)
    cx2 = int(size * 0.62)
    cy2 = int(size * 0.65)
    head_r = int(size * 0.12)

    # Note heads
    for cx, cy in ((cx1, cy1), (cx2, cy2)):
        draw.ellipse(
            (cx - head_r, cy - head_r, cx + head_r, cy + head_r),
            fill=WHITE,
        )

    # Stems
    stem_w = max(2, int(size * 0.045))
    stem_top_y = int(size * 0.22)
    draw.rectangle(
        (cx1 + head_r - stem_w, stem_top_y, cx1 + head_r, cy1),
        fill=WHITE,
    )
    draw.rectangle(
        (cx2 + head_r - stem_w, stem_top_y - int(size * 0.07),
         cx2 + head_r, cy2),
        fill=WHITE,
    )

    # Beam connecting the two stems at top.
    beam_h = max(3, int(size * 0.07))
    draw.polygon(
        [
            (cx1 + head_r - stem_w, stem_top_y),
            (cx2 + head_r, stem_top_y - int(size * 0.07)),
            (cx2 + head_r, stem_top_y - int(size * 0.07) + beam_h),
            (cx1 + head_r - stem_w, stem_top_y + beam_h),
        ],
        fill=WHITE,
    )

    return img


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / "resources"
    out_dir.mkdir(exist_ok=True)
    ico_path = out_dir / "icon.ico"
    png_path = out_dir / "icon.png"

    # Multiple sizes so Windows can pick crisp ones for taskbar, dialog,
    # context menu, etc.
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [render_square(s) for s in sizes]

    images[-1].save(png_path)
    images[-1].save(
        ico_path, format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[:-1],
    )
    print(f"wrote {ico_path} and {png_path}")


if __name__ == "__main__":
    main()
