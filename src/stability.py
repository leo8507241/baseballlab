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
# ---------- 實驗 3：資料重抽（Bootstrap） ----------
def exp_bootstrap_series(teams, games, n_boot=200, seed=0):
    """從例行賽 360 場比賽中「有放回地」重抽，重算得失分 → 畢氏勝率 → 奪冠機率。"""
    rng = np.random.default_rng(seed)
    a, b = config.TS_TEAMS
    out = []
    for _ in range(n_boot):
        g = games.iloc[rng.integers(0, len(games), len(games))]
        rs_ra = {}
        for team in (a, b):
            home, away = g[g["home"] == team], g[g["away"] == team]
            rs_ra[team] = (home["home_runs"].sum() + away["away_runs"].sum(),
                           home["away_runs"].sum() + away["home_runs"].sum())
        pa, pb = pythag(*rs_ra[a]), pythag(*rs_ra[b])
        out.append(model.simulate_series(pa, pb, config.TS_HOME_PATTERN, config.TS_NEED,
                                         config.HOME_ADVANTAGE, n=2_000, seed=1)[0])
    return pd.Series(out, name="奪冠機率")
def exp_bootstrap_rules(pa, scale, sp, lineup, lg, n_boot=200, seed=0):
    """重抽逐打席資料，重算這位先發的拆分數據，統計每條弱點規則有幾成的機率成立。"""
    rng = np.random.default_rng(seed)
    base = splits.prepare(pa, scale)
    mine = base[base["pitcher_id"] == sp["player_id"]]
    counts = {}
    for _ in range(n_boot):
        s = mine.iloc[rng.integers(0, len(mine), len(mine))]
        p = sp.copy()
        for hand in ("L", "R"):
            sub = s[s["b_hand"] == hand]
            p[f"PA_vs{hand}"], p[f"wOBA_vs{hand}"] = len(sub), sub["woba_val"].mean()
        p["wOBA_round3"] = s.loc[s["pa_round"] == 3, "woba_val"].mean()
        for sentence in rules.pitcher_weak(p, lineup, lg):
            key = sentence.split("：")[0]          # 用冒號前的標題當作規則名稱
            counts[key] = counts.get(key, 0) + 1
    return pd.Series(counts).div(n_boot).sort_values(ascending=False).rename("成立比例")
def rule_stability_table(pa, scale, teams, batters, pitchers, lg, n_boot=200):
    """台灣大賽兩隊每位先發的每條弱點規則，在重抽中成立的比例。存起來給預測頁過濾用。"""
    t = teams.set_index("team")
    a, b = config.TS_TEAMS
    rows = []
    for team, opp in ((a, b), (b, a)):
        abbr, opp_abbr = t.loc[team, "abbr"], t.loc[opp, "abbr"]
        lineup = batters[batters["abbr"] == opp_abbr].nlargest(9, "PA")
        for _, sp in pitchers[(pitchers["abbr"] == abbr) & (pitchers["role"] == "先發")].iterrows():
            ratio = exp_bootstrap_rules(pa, scale, sp, lineup, lg, n_boot)
            rows += [{"pitcher_id": sp["player_id"], "rule": k, "ratio": v} for k, v in ratio.items()]
    return pd.DataFrame(rows)
