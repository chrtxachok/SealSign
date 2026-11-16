"""Find low-distance dHash candidates, without declaring identity or assigning splits."""

import csv
import io
import json
import zipfile
from collections import Counter
from itertools import combinations
from pathlib import Path

from audit_leakage import dhash
from PIL import Image

from sealsign.data.importer import sha256, zip_inventory

DOC = Path("artifacts/data-audit/doclaynet-small/dataset_small.zip")
MAPO = Path("artifacts/data-audit/mapo80")
EXPECTED = {
    "dataset_small.zip": "85e289b3635b2e17937e201e567d98097173a7b8116daa72dd9e9fb61d738597",
    "train.zip": "07016aa6df14b4b4fab6bfa896469003160f932677bae86e8f91712f6cbdef0c",
    "val.zip": "0dd0b1fd1259a4a28bdaea12711c658ff0b419af868bcb37ef1686d71aa7c3f5",
    "test.zip": "c3942fd1dc8037649885c7cec7d5e1c8399b131fe75605083c39d50b674d5f4b",
}


def fingerprints(path, source):
    if sha256(path) != EXPECTED[path.name]:
        raise ValueError("Archive checksum mismatch")
    result = []
    with zipfile.ZipFile(path) as archive:
        entries = zip_inventory(archive)
        for name in sorted(entries):
            if "/images/" not in f"/{name}" or not name.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            if entries[name].file_size > 32 * 1024**2:
                raise ValueError("Image exceeds budget")
            with Image.open(io.BytesIO(archive.read(name))) as image:
                if image.width * image.height > 50_000_000:
                    raise ValueError("Image exceeds pixel budget")
                image.load()
                result.append((source, name, dhash(image)))
    return result


def main():
    output = Path("artifacts/data-qc/doclaynet-similarity-v1")
    if output.exists():
        raise ValueError("Output exists")
    docs = fingerprints(DOC, "doclaynet-small")
    mapo = []
    for split in ("train", "val", "test"):
        mapo.extend(fingerprints(MAPO / f"{split}.zip", f"mapo80-{split}"))
    counts = Counter()
    pairs = []
    for label, candidates in (
        ("within_doclaynet", combinations(docs, 2)),
        ("cross_source", ((a, b) for a in docs for b in mapo)),
    ):
        for a, b in candidates:
            distance = (a[2] ^ b[2]).bit_count()
            if distance <= 2:
                counts[label] += 1
                counts[f"{label}_distance_{distance}"] += 1
                pairs.append((label, a[0], a[1], b[0], b[1], distance, "unreviewed"))
    output.mkdir(parents=True)
    with (output / "candidate-pairs.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(("scope", "source_a", "file_a", "source_b", "file_b", "distance", "status"))
        writer.writerows(pairs)
    report = {
        "schema_version": "sealsign-doclaynet-similarity-v1",
        "inputs_sha256": EXPECTED,
        "doclaynet_images": len(docs),
        "mapo80_images": len(mapo),
        "within_doclaynet_pairs_compared": len(docs) * (len(docs) - 1) // 2,
        "cross_source_pairs_compared": len(docs) * len(mapo),
        "method": "64-bit grayscale dHash, Hamming distance <= 2",
        "candidate_counts": dict(counts),
        "candidate_pairs": len(pairs),
        "candidates_confirmed_duplicates": False,
        "all_duplicates_excluded": False,
        "accepted_for_training": False,
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    Path("reports/data/doclaynet-similarity-audit.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
