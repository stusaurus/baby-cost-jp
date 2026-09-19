from pathlib import Path
import json
import os

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"
DATA_DIR = ROOT / "data"
SITE_ID = "baby_cost_jp"
SITE_NAME = "ベビーコスパ比較"
SITE_URL = os.environ.get("SITE_URL", "https://stusaurus.github.io/baby-cost-jp/").rstrip("/") + "/"
GA_MEASUREMENT_ID = os.environ.get("GA_MEASUREMENT_ID", "").strip()


def load_categories():
    return json.loads((DATA_DIR / "categories.json").read_text(encoding="utf-8"))
