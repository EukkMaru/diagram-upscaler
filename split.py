# pip install pillow numpy tqdm
import argparse
from pathlib import Path
import numpy as np
from PIL import Image
from tqdm import tqdm

def apply_soft_mask(orig: Image.Image, mask: Image.Image):
    """Return (positive, negative) images as PIL.Image objects."""
    if mask.mode != "L":
        mask = mask.convert("L")
    if orig.mode != "RGB":
        orig = orig.convert("RGB")

    img_arr  = np.asarray(orig, dtype=np.float32)      # H×W×3
    m_arr    = np.asarray(mask, dtype=np.float32)[..., None] / 255.0  # H×W×1

    pos_arr  = (img_arr * m_arr).astype(np.uint8)
    neg_arr  = (img_arr * (1.0 - m_arr)).astype(np.uint8)

    return (Image.fromarray(pos_arr, mode="RGB"),
            Image.fromarray(neg_arr, mode="RGB"))

def main():
    p = argparse.ArgumentParser(
        description="Split blurred images with their blurred masks")
    p.add_argument("--input_dir",  default="./blurred",
                   help="Folder containing blurred PNGs")
    p.add_argument("--output_dir", default="./split",
                   help="Where to save *_pos.png / *_neg.png")
    args = p.parse_args()

    in_dir  = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Iterate over all masks first
    masks = sorted(in_dir.glob("*_mask.png"))
    for m_path in tqdm(masks, desc="Splitting"):
        base    = m_path.stem.replace("_mask", "")
        img_path = in_dir / f"{base}.png"
        if not img_path.exists():
            print(f"[!] Missing original for {m_path.name}, skipped")
            continue

        try:
            orig = Image.open(img_path)
            mask = Image.open(m_path)
            pos, neg = apply_soft_mask(orig, mask)

            pos.save(out_dir / f"{base}_pos.png")
            neg.save(out_dir / f"{base}_neg.png")
        except Exception as e:
            print(f"[!] {base}: {e}")

if __name__ == "__main__":
    main()
