# pip install pillow tqdm
import argparse
from pathlib import Path
from PIL import Image, ImageFilter
from tqdm import tqdm

def main():
    parser = argparse.ArgumentParser(
        description="Blur all PNGs in ./images and save to ./blurred")
    parser.add_argument("--input_dir",  type=str, default="./images",
                        help="Folder that already contains the PNGs")
    parser.add_argument("--output_dir", type=str, default="./blurred",
                        help="Folder to receive blurred PNGs")
    parser.add_argument("--radius", type=float, default=4.0,
                        help="Gaussian blur radius (pixels)")
    args = parser.parse_args()

    in_dir  = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pngs = sorted(in_dir.rglob("*.png"))
    for src in tqdm(pngs, desc="Blurring"):
        dst = out_dir / src.name
        try:
            img  = Image.open(src)
            blur = img.filter(ImageFilter.GaussianBlur(args.radius))
            blur.save(dst)
        except Exception as e:
            print(f"[!] {src.name}: {e}")

if __name__ == "__main__":
    main()
