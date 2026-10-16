"""Check standalone links, dashboard packaging, policy claims and SQL examples."""

import json
import re
import sqlite3
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify():
    for document in ROOT.rglob("*.md"):
        if ".git" in document.parts or ".venv" in document.parts:
            continue
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', document.read_text()):
            if not target.startswith(("http://", "https://", "#")):
                assert (document.parent / target.split("#", 1)[0]).exists(), (document, target)
    bundle = ROOT / "dashboard/dist"

    class AssetLinks(HTMLParser):
        def handle_starttag(self, tag, attrs):
            values = dict(attrs)
            target = values.get("src") or (values.get("href") if tag in ("a", "link") else None)
            if target and not target.startswith(("http://", "https://", "#")):
                assert (bundle / target).exists(), target

    AssetLinks().feed((bundle / "index.html").read_text())
    report = json.loads((ROOT / "outputs/report.json").read_text())
    data_js = (bundle / "data.js").read_text()
    assert json.loads(data_js.removeprefix("window.RETAIL_DATA=").rstrip(";\n")) == report
    policy = json.loads((ROOT / "outputs/discount-solution.json").read_text())
    assert abs(policy["modeled_h2_gp_eur"] - policy["h2_gp_eur"] - policy["modeled_gain_eur"]) < .01
    connection = sqlite3.connect(ROOT / "outputs/retail.sqlite")
    try:
        statements = (ROOT / "sql/kpi_queries.sql").read_text().split(";")
        for statement in statements:
            if statement.strip():
                assert connection.execute(statement).fetchall(), "KPI query returned no rows"
    finally:
        connection.close()
    print("Standalone links, dashboard bundle, scenario identity and SQL examples verified.")


if __name__ == "__main__":
    verify()
