"""Convert dark backgrounds of planet PNGs to true alpha transparency."""
from pathlib import Path
from PIL import Image
import numpy as np


def strip_black_bg(src: Path, dst: Path, low: int = 6, high: int = 34) -> None:
    """Convert near-black pixels to alpha-transparent while preserving glow."""
    img = Image.open(src).convert("RGB")
    arr = np.asarray(img, dtype=np.float32)  # H, W, 3
    # Rec.709 luminance
    lum = 0.2126 * arr[..., 0] + 0.7152 * arr[..., 1] + 0.0722 * arr[..., 2]
    # Smoothstep-ish alpha: 0 below low, 255 above high, linear in between
    alpha = np.clip((lum - low) / max(1, (high - low)), 0.0, 1.0) * 255.0
    rgba = np.dstack([arr, alpha]).astype(np.uint8)
    Image.fromarray(rgba, mode="RGBA").save(dst)
    print(f"Saved {dst}")


if __name__ == "__main__":
    base = Path("/app/frontend/public/mascot")
    for name in ["astro-planet-0.png", "astro-planet-v2-0.png", "astro-planet-v3-0.png"]:
        strip_black_bg(base / name, base / name.replace(".png", "-t.png"))
