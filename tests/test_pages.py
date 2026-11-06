"""Day 32：自動測試每一頁。執行：python -m pytest -q"""
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["pages/home.py", "pages/academy.py", "pages/watch.py", "pages/predict.py"]

def open_page(page):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    if page != "pages/home.py":
        at.switch_page(page).run()
    return at

@pytest.mark.parametrize("page", PAGES)
def test_page_runs_without_error(page):
    at = open_page(page)
    assert not at.exception, [e.value for e in at.exception]
def test_every_stat_card():
    at = open_page("pages/academy.py")
    stats = json.loads((ROOT / "content" / "stats.json").read_text(encoding="utf-8"))
    for s in stats:
        at.radio[0].set_value(s["key"]).run()
        assert not at.exception, s["key"]

def test_lineup_needs_nine_players():
    at = open_page("pages/predict.py")
    ms = at.multiselect[0]
    ms.unselect(ms.value[0]).run()
    assert any("9 位打者" in i.value for i in at.info)

def test_series_probabilities_add_up():
    import pandas as pd
    import sys
    sys.path.insert(0, str(ROOT))
    from src import config, model
    teams = pd.read_csv(ROOT / "data/clean/teams.csv").set_index("team")
    a, b = config.TS_TEAMS
    p, results, _ = model.simulate_series(teams.loc[a, "pythag"], teams.loc[b, "pythag"],
                                          config.TS_HOME_PATTERN)
    assert 0 < p < 1
    assert sum(results.values()) == 10_000
