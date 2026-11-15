"""Build a private offline editor from an imported pilot, without external assets."""

import argparse
import base64
import json
from pathlib import Path

from sealsign.data.importer import sha256


def build(bundle, output):
    if output.exists():
        raise ValueError("Output exists")
    bundle = bundle.resolve()
    pages = [json.loads(line) for line in (bundle / "manifest.jsonl").read_text().splitlines()]
    if len(pages) > 200:
        raise ValueError("Use a pilot or batch of at most 200 pages")
    coco = json.loads((bundle / "annotations.json").read_text())
    images = {im["page_id"]: im for im in coco["images"]}
    payload = {
        "manifest_sha256": sha256(bundle / "manifest.jsonl"),
        "annotations_sha256": sha256(bundle / "annotations.json"),
        "pages": [],
    }
    size = 0
    for page in pages:
        if page["page_id"] not in images or page.get("exclusion_reason"):
            continue
        image = images[page["page_id"]]
        path = (bundle / image["file_name"]).resolve()
        if not path.is_relative_to(bundle) or sha256(path) != page["normalized_sha256"]:
            raise ValueError("Image path or checksum mismatch")
        raw = path.read_bytes()
        size += len(raw)
        if size > 150 * 1024**2:
            raise ValueError("Offline editor image budget exceeded")
        payload["pages"].append(
            {
                "page_id": page["page_id"],
                "sha256": page["normalized_sha256"],
                "width": image["width"],
                "height": image["height"],
                "image": "data:image/png;base64," + base64.b64encode(raw).decode(),
                "objects": [
                    {"category_id": obj["category_id"], "bbox": obj["bbox"]}
                    for obj in coco["annotations"]
                    if obj["image_id"] == image["id"]
                ],
            }
        )
    if not payload["pages"]:
        raise ValueError("No valid pages")
    template = Path(__file__).parents[1] / "src/sealsign/data/editor/editor.html"
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(template.read_text().replace("__DATASET__", data))
    return {
        "pages": len(payload["pages"]),
        "output_bytes": output.stat().st_size,
        "manifest_sha256": payload["manifest_sha256"],
        "accepted_for_training": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.bundle, args.output)))


if __name__ == "__main__":
    main()
