"""Regenerate the 80 by 80 district from the aligned World Map PNGs (Pillow)."""
import hashlib
import json
from pathlib import Path

from PIL import Image

project = Path(__file__).resolve().parents[1]
floors = project.parent / "plugins/worldmap/static/floors"
center = (32369, 32241)
origin = (31744, 30976)
width = 80
palette = {
    "000000": " ", "999999": ".", "ff3300": "#", "00cc00": "g", "006600": "T",
    "99ff66": "m", "996633": "p", "993300": "r", "336699": "~", "ffff00": "+",
    "666666": "b", "ffcc99": "s", "ff6600": "l", "ffffff": "w", "ccffff": "i",
}
symbols = {bytes.fromhex(key): symbol for key, symbol in palette.items()}
left, top = (center[i] - origin[i] - width // 2 for i in range(2))
data = {"center": center, "width": width, "origin": origin, "palette": palette, "floors": []}
for floor in range(16):
    file = floors / f"floor-{floor:02}.png"
    with Image.open(file) as image:
        assert image.size == (2560, 2048)
        crop = image.convert("RGB").crop((left, top, left + width, top + width))
        rows = ["".join(symbols[bytes(crop.getpixel((x, y)))] for x in range(width)) for y in range(width)]
    data["floors"].append({"floor": floor, "file": file.name, "sha256": hashlib.sha256(file.read_bytes()).hexdigest(), "rows": rows})
(project / "src/thais.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
