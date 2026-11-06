import numpy as np
import pandas as pd

from src import config, model, rules, splits
from src.metrics import pythag

def team_strengths(teams):
    t=teams.set_index('team')
    a,b=config.TS_TEAMS
    return t.loc[a,'pythag'] , t.loc[b,'pythag']
# ---------- 實驗 1：模擬次數與亂數 ----------
def exp_seeds(teams, n_seeds=30, n=10_000):
    pa, pb = team_strengths(teams)
    probs = [model.simulate_series(pa, pb, config.TS_HOME_PATTERN, config.TS_NEED,
                                   config.HOME_ADVANTAGE, n=n, seed=s)[0] for s in range(n_seeds)]
    return pd.Series(probs, name="奪冠機率")
# ---------- 實驗 2：參數敏感度 ----------
def exp_sensitivity(teams):
    """一次只改一個參數，看系列賽奪冠機率和中立場地單場勝率怎麼變。"""
    t = teams.set_index("team")
    a, b = config.TS_TEAMS
    rows = []
    settings = [("主場優勢", v, dict(hfa=v)) for v in [0, 0.015, 0.03, 0.045, 0.06]] + \
               [("畢氏指數", v, dict(exp=v)) for v in [1.8, 1.83, 1.9, 2.0]]
    for name, value, kw in settings:
        exp = kw.get("exp", 1.83)
        hfa = kw.get("hfa", config.HOME_ADVANTAGE)
        pa = pythag(t.loc[a, "RS"], t.loc[a, "RA"], exp)
        pb = pythag(t.loc[b, "RS"], t.loc[b, "RA"], exp)
        series = model.simulate_series(pa, pb, config.TS_HOME_PATTERN, config.TS_NEED, hfa)[0]
        rows.append({"參數": name, "數值": value, "單場勝率（中立）": model.log5(pa, pb), "奪冠機率": series})
    return pd.DataFrame(rows)

def default_game_prob(teams, batters, pitchers, lg, sp_innings=6, a_home=True):
    """用「兩隊投球局數最多的先發＋打席最多的 9 人」算單場勝率，給實驗 2 測先發局數用。"""
    t = teams.set_index("team")
    a, b = config.TS_TEAMS
    ctx = model.league_context(teams, pitchers, lg["wOBA"])
    tp = pd.DataFrame(model.team_pitching(pitchers)).set_index("abbr")
    side = {}
    for team in (a, b):
        abbr = t.loc[team, "abbr"]
        sp = pitchers[(pitchers["abbr"] == abbr) & (pitchers["role"] == "先發")].nlargest(1, "IP").iloc[0]
        lu = batters[batters["abbr"] == abbr].nlargest(9, "PA")
        side[team] = (abbr, sp, lu)
    (aa, sa, la), (ab, sb, lb) = side[a], side[b]
    w = lambda lu, sp: lu.apply(lambda r: rules.bat_woba(r, sp["throws"]), axis=1).mean()
    ra = model.expected_runs(w(la, sb), la["wOBA_calc"].mean(), sb["FIP_calc"], tp.loc[ab, "bullpen_fip"],
                             tp.loc[ab, "DER"], ctx, sp_innings, a_home)
    rb = model.expected_runs(w(lb, sa), lb["wOBA_calc"].mean(), sa["FIP_calc"], tp.loc[aa, "bullpen_fip"],
                             tp.loc[aa, "DER"], ctx, sp_innings, not a_home)
    return model.win_prob_from_runs(ra, rb)
