"""Prepare a deterministic train-only overview without accepting annotations."""

import io
import json
import random
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

from sealsign.data.importer import sha256, zip_inventory

SOURCE = Path("artifacts/data-audit/doclaynet-small/dataset_small.zip")
OUTPUT = Path("artifacts/data-qc/doclaynet-pilot100-v1")
EXPECTED = "85e289b3635b2e17937e201e567d98097173a7b8116daa72dd9e9fb61d738597"


def main():
    if sha256(SOURCE) != EXPECTED:
        raise ValueError("Archive checksum mismatch")
    if OUTPUT.exists():
        raise ValueError("Output already exists")
    with zipfile.ZipFile(SOURCE) as archive:
        entries = zip_inventory(archive)
        names = sorted(
            n for n in entries if n.startswith("small_dataset/train/images/") and n.endswith(".png")
        )
        if len(names) < 100:
            raise ValueError("Insufficient train images")
        random.Random(42).shuffle(names)
        names = names[:100]
        OUTPUT.mkdir(parents=True)
        (OUTPUT / "sample.json").write_text(json.dumps(names, indent=2) + "\n")
        for batch in range(10):
            sheet = Image.new("RGB", (1600, 1200), "white")
            draw = ImageDraw.Draw(sheet)
            for i, name in enumerate(names[batch * 10 : batch * 10 + 10]):
                if entries[name].file_size > 32 * 1024**2:
                    raise ValueError("Image exceeds byte budget")
                with Image.open(io.BytesIO(archive.read(name))) as source:
                    if source.width * source.height > 50_000_000:
                        raise ValueError("Image exceeds pixel budget")
                    image = source.convert("RGB")
                image.thumbnail((310, 550))
                x, y = (i % 5) * 320, (i // 5) * 600
                sheet.paste(image, (x, y + 22))
                draw.text((x + 5, y + 4), f"{batch * 10 + i + 1:03}", fill="black")
            sheet.save(OUTPUT / f"sheet-{batch + 1:02}.jpg")


if __name__ == "__main__":
    main()
