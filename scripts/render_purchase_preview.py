"""Render the real published catalog locally; never publish this QA snapshot."""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.build_site import load_categories
from src.render import render_comparison

if __name__ == '__main__':
    payload = json.load(sys.stdin)
    categories = load_categories()
    category = categories['diapers']
    segment = next(s for s in category['segments'] if s['id'] == 'pants-m')
    print(render_comparison(categories, 'diapers', category, segment, payload['products'],
                            datetime.fromisoformat(payload['generated_at'])))
