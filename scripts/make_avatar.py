"""Generate assets/avatar.png — the bot's profile photo.

Requires Pillow:  pip install Pillow
Run from the project root:  python scripts/make_avatar.py

Telegram crops avatars to a circle, so all content stays inside the
central circle with a safe margin.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 640
SCALE = 3  # supersampling for smooth (anti-aliased) edges
S = SIZE * SCALE

TOP = (0x1E, 0x3A, 0x8A)     # deep blue
BOTTOM = (0x0E, 0xA5, 0xA4)  # teal
WHITE = (255, 255, 255, 255)

OUT = Path(__file__).resolve().parents[1] / "assets" / "avatar.png"

FONT_CANDIDATES = [
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]


def load_font(px: int):
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, px)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=px)
    except TypeError:
        return ImageFont.load_default()


def gradient() -> Image.Image:
    """Diagonal gradient from top-left (blue) to bottom-right (teal)."""
    small = 256
    img = Image.new("RGB", (small, small))
    px = img.load()
    for y in range(small):
        for x in range(small):
            t = (x + y) / (2 * (small - 1))
            t = t * t * (3 - 2 * t)  # smoothstep
            px[x, y] = tuple(round(a + (b - a) * t) for a, b in zip(TOP, BOTTOM))
    return img.resize((S, S), Image.BICUBIC).convert("RGBA")


def u(v: float) -> int:
    """Convert design units (on a 640 canvas) to supersampled pixels."""
    return round(v * SCALE)


def draw_house(d: ImageDraw.ImageDraw, cx: float, top: float) -> None:
    w, roof_h, body_h = 250, 105, 150
    left, right = cx - w / 2, cx + w / 2
    eave = top + roof_h
    bottom = eave + body_h
    overhang = 26

    # Roof
    d.polygon(
        [(u(cx), u(top)), (u(right + overhang), u(eave + 4)), (u(left - overhang), u(eave + 4))],
        fill=WHITE,
    )
    # Body
    d.rounded_rectangle(
        [u(left + 14), u(eave - 2), u(right - 14), u(bottom)], radius=u(12), fill=WHITE
    )
    # Chimney
    d.rectangle([u(right - 70), u(top + 30), u(right - 44), u(eave - 30)], fill=WHITE)

    # Cut-outs (door + 2 windows) show the background through the body
    hole = (0, 0, 0, 0)
    door_w, door_h = 54, 88
    d.rounded_rectangle(
        [u(cx - door_w / 2), u(bottom - door_h), u(cx + door_w / 2), u(bottom + 1)],
        radius=u(10), fill=hole,
    )
    win, gap = 46, 24
    wy = eave + 30
    for wx in (cx - door_w / 2 - gap - win, cx + door_w / 2 + gap):
        d.rounded_rectangle([u(wx), u(wy), u(wx + win), u(wy + win)], radius=u(8), fill=hole)


def centered_text(d, text, cy, font, spacing=0, fill=WHITE):
    widths = [d.textlength(ch, font=font) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = (S - total) / 2
    for ch, w in zip(text, widths):
        d.text((x, cy), ch, font=font, fill=fill, anchor="lm")
        x += w + spacing


def main() -> None:
    bg = gradient()

    # Soft light glow behind the icon for depth
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([u(150), u(90), u(490), u(430)], fill=(255, 255, 255, 22))
    bg = Image.alpha_composite(bg, glow)

    # House on its own layer so cut-outs reveal the gradient
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw_house(ImageDraw.Draw(layer), cx=320, top=128)
    img = Image.alpha_composite(bg, layer)

    d = ImageDraw.Draw(img)
    centered_text(d, "CHIRCHIQ", u(442), load_font(u(66)), spacing=u(3))
    centered_text(d, "KVARTIRA", u(500), load_font(u(30)), spacing=u(9),
                  fill=(255, 255, 255, 215))

    img = img.convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
