"""Audit the pinned DocLayNet small archive without extracting private documents."""

import collections
import hashlib
import io
import json
import random
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

from sealsign.data.importer import sha256, zip_inventory

p = Path("artifacts/data-audit/doclaynet-small/dataset_small.zip")
if sha256(p) != "85e289b3635b2e17937e201e567d98097173a7b8116daa72dd9e9fb61d738597":
    raise ValueError("DocLayNet archive checksum mismatch")
expected_mapo = {
    "train": "07016aa6df14b4b4fab6bfa896469003160f932677bae86e8f91712f6cbdef0c",
    "val": "0dd0b1fd1259a4a28bdaea12711c658ff0b419af868bcb37ef1686d71aa7c3f5",
    "test": "c3942fd1dc8037649885c7cec7d5e1c8399b131fe75605083c39d50b674d5f4b",
}
out = Path("artifacts/data-qc/doclaynet-small-v1")
out.mkdir(parents=True, exist_ok=True)
mapo = set()
for a in ("train", "val", "test"):
    mapo_path = Path(f"artifacts/data-audit/mapo80/{a}.zip")
    if sha256(mapo_path) != expected_mapo[a]:
        raise ValueError("Mapo80 archive checksum mismatch")
    with zipfile.ZipFile(mapo_path) as z:
        for n in z.namelist():
            if n.lower().endswith((".png", ".jpg", ".jpeg")):
                mapo.add(hashlib.sha256(z.read(n)).hexdigest())
with zipfile.ZipFile(p) as z:
    entries = zip_inventory(z)
    bad = z.testzip()
    if bad:
        raise ValueError("CRC failed")
    images = sorted(n for n in entries if "/images/" in n and n.endswith(".png"))
    hashes = collections.Counter()
    keys = collections.Counter()
    categories = collections.Counter()
    splits = collections.Counter()
    matches = 0
    dims = collections.Counter()
    train = []
    for n in images:
        info = entries[n]
        if info.file_size > 32 * 1024**2:
            raise ValueError("image too large")
        raw = z.read(n)
        d = hashlib.sha256(raw).hexdigest()
        hashes[d] += 1
        matches += d in mapo
        with Image.open(io.BytesIO(raw)) as im:
            im.load()
            dims[str(im.size)] += 1
        parts = n.split("/")
        spl = parts[1]
        splits[spl] += 1
        stem = Path(n).stem
        ann = f"small_dataset/{spl}/annotations/{stem}.json"
        pdf = f"small_dataset/{spl}/pdfs/{stem}.pdf"
        if ann not in entries or pdf not in entries:
            raise ValueError("missing pair")
        if entries[ann].file_size > 16 * 1024**2:
            raise ValueError("annotation too large")
        data = json.loads(z.read(ann))
        m = data["metadata"]
        keys[(m["original_filename"], m["page_no"])] += 1
        categories[m["doc_category"]] += 1
        if spl == "train":
            train.append(n)
    random.Random(42).shuffle(train)
    selected = train[:30]
    for batch in range(3):
        sheet = Image.new("RGB", (1600, 1200), "white")
        draw = ImageDraw.Draw(sheet)
        for k, n in enumerate(selected[batch * 10 : batch * 10 + 10]):
            im = Image.open(io.BytesIO(z.read(n))).convert("RGB")
            im.thumbnail((310, 550))
            x = (k % 5) * 320
            y = (k // 5) * 600
            sheet.paste(im, (x, y + 22))
            draw.text((x + 5, y + 4), f"{batch * 10 + k + 1:02}", fill="black")
        sheet.save(out / f"sheet-{batch + 1}.jpg")
    (out / "sample-train.json").write_text(json.dumps(selected, indent=2) + "\n")
report = {
    "source_revision": "b61d29f477163034001472614dc97fb9614dddea",
    "archive_sha256": sha256(p),
    "zip_crc_verified": True,
    "archive_entries": len(entries),
    "images": len(images),
    "split_counts": dict(splits),
    "decoded_images": sum(dims.values()),
    "dimensions": dict(dims),
    "category_counts": dict(categories),
    "distinct_image_sha256": len(hashes),
    "duplicate_image_sha256_groups": sum(v > 1 for v in hashes.values()),
    "distinct_source_filename_and_page": len(keys),
    "duplicate_source_filename_and_page_groups": sum(v > 1 for v in keys.values()),
    "exact_image_matches_mapo80": matches,
    "pilot_train_sample": 30,
    "pilot_seed": 42,
    "target_boxes_verified": False,
    "accepted_for_training": False,
}
Path("reports/data/doclaynet-small-audit.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
