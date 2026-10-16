"""Bundle a buildless, offline dashboard. No hosting or cloud services are used."""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build():
    source = ROOT / "dashboard"
    destination = source / "dist"
    assets = destination / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for filename in ("index.html", "style.css", "model.js", "app.js"):
        shutil.copy2(source / filename, destination / filename)
    report = json.loads((ROOT / "outputs/report.json").read_text())
    serialized = json.dumps(report, separators=(",", ":")).replace("<", "\\u003c")
    (destination / "data.js").write_text(f"window.RETAIL_DATA={serialized};\n")
    shutil.copy2(ROOT / "assets/retail-margin-solution.png", assets / "solution.png")
    for filename in ("analysis.png",):
        shutil.copy2(ROOT / "outputs" / filename, assets / filename)
    print(f"Offline dashboard: {destination / 'index.html'}")


if __name__ == "__main__":
    build()

