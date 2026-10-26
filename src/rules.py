
"""Day 13：用規則自動產生「投手弱點、打線弱點、應對策略」的文字。"""
import pandas as pd

HAND = {"L": "左投", "R": "右投"}
BATS = {"L": "左打", "R": "右打", "S": "左右開弓"}
PITCH_NAME = {"SL": "滑球", "CU": "曲球", "CH": "變速球", "FO": "指叉球", "FS": "指叉球",
              "SC": "螺旋球", "SV": "縱向滑球", "KC": "彈指曲球"}

woba_gap=0.030
min_pa=30

def _f3(x):
    return f'{x:.3f}'.lstrip('0')

def bat_woba(b,hand):
    pa, w=b.get(f'PA_vs{hand}'),b.get(f'wOBA_vs{hand}')
    return w if pd.notna(pa) and pa>=min_pa else  b["wOBA_calc"]
def pitcher_weak(p,opp_lineup,lg):
    out=[]
    vl,vr=p.get("wOBA_vsL"),p.get("wOBA_vsR")
    if pd.notna(vl) and pd.notna(vr) and p.get('PA_vsL',0)>=min_pa and p.get("PA_vsR",0)>=min_pa:
        n_l=int((opp_lineup['bats']!='R').sum())
        n_r=int((opp_lineup['bats']!='L').sum())
        if vl-vr>woba_gap:
            out.append(f"對左打明顯較弱：被 wOBA {_f3(vl)}（對右打 {_f3(vr)}）。對手打線有 {n_l} 位左打或左右開弓。")
        elif vr-vl>woba_gap:
            out.append(f"對右打明顯較弱：被 wOBA {_f3(vr)}（對左打 {_f3(vl)}）。對手打線有 {n_r} 位右打或左右開弓。")
    r3 = p.get("wOBA_round3")
    if pd.notna(r3) and r3 > lg["wOBA"] + 0.020:
        out.append(f"第三輪打線開始被看穿：被 wOBA 升到 {_f3(r3)}（聯盟平均 {_f3(lg['wOBA'])}）。")
    if p["BBp"] >= lg["BBp_p75"]:
        out.append(f"保送率 {p['BBp']:.1f}% 偏高（聯盟前 25%），球數容易拉長。")
    if p["HR9"] >= lg["HR9_p75"]:
        out.append(f"每九局被 {p['HR9']:.2f} 支全壘打，容易挨長打。")
    if not out:
        out.append(f"沒有明顯弱點：三振率 {p['Kp']:.1f}%、FIP {p['FIP_calc']:.2f}。")
    return out
def lineup_weak(lineup,sp):
    out=[]
    hand=sp['throws']
    lineup=lineup.assign(w_vs=lineup.apply(lambda x:bat_woba(x,hand),axis=1))
    weak=lineup[lineup['w_vs']<0.290].nsmallest(3, "w_vs")
    if len(weak):
        names='、'.join(f'{r['name']}({_f3(r['w_vs'])})' for _,r in weak.iterrows())
        out.append(f'對{HAND[hand]}表現差{names}')
    main=sp["main_breaking"]
    if pd.notna(main):
        w=lineup[(lineup['swings']>=50) & (lineup['whiff_rate']>=0.35)].nlargest(3,'whiff_rate')
        if len(w):
            names = "、".join(f"{r['name']}（{r['whiff_rate']:.0%}）" for _, r in w.iterrows())
            out.append(f"對方先發最常用的變化球是{PITCH_NAME.get(main, main)}，"
                       f"這幾位對變化球揮空率高：{names}。")
    if not out:
        out.append("打線對這位先發沒有明顯的對位弱點。")
    return out

def strategy(team_lineup, bench, my_sp, opp_sp, lg):
    out = []
    vl, vr = opp_sp.get("wOBA_vsL"), opp_sp.get("wOBA_vsR")
    if pd.notna(vl) and pd.notna(vr):
        if vl - vr > woba_gap:
            alt = bench[bench["bats"] != "R"].nlargest(1, "wOBA_calc")
            extra = f"，也可以讓板凳的 {alt.iloc[0]['name']} 先發" if len(alt) else ""
            out.append(f"{opp_sp['name']}怕左打：左打排進前五棒{extra}。")
        elif vr - vl > woba_gap:
            alt = bench[bench["bats"] != "L"].nlargest(1, "wOBA_calc")
            extra = f"，也可以讓板凳的 {alt.iloc[0]['name']} 先發" if len(alt) else ""
            out.append(f"{opp_sp['name']}怕右打：右打排進前五棒{extra}。")
    if opp_sp["BBp"] >= lg["BBp_p75"]:
        out.append(f"{opp_sp['name']}控球不穩：前兩輪多看球，拉高他的用球數。")
    r3 = opp_sp.get("wOBA_round3")
    if pd.notna(r3) and r3 > lg["wOBA"] + 0.020:
        out.append("第三輪打線（約 5、6 局）是主要得分機會，可以安排代打或積極跑壘。")
    if opp_sp["HR9"] >= lg["HR9_p75"]:
        top = team_lineup.nlargest(1, "ISO_calc").iloc[0]
        out.append(f"{opp_sp['name']}容易挨長打：把 ISO 最高的 {top['name']}（{_f3(top['ISO_calc'])}）排在第 3、4 棒。")
    my_r3 = my_sp.get("wOBA_round3")
    if pd.notna(my_r3) and my_r3 > lg["wOBA"] + 0.020:
        out.append(f"己方先發 {my_sp['name']} 第三輪容易被打，第 5 局就讓牛棚開始熱身。")
    if my_sp["GBp"] >= 50:
        out.append(f"{my_sp['name']}是滾地球型投手（滾地球率 {my_sp['GBp']:.0f}%），內野要排守備最穩的陣容。")
    if not out:
        out.append("雙方沒有明顯的對位優勢，照正常戰術打。")
    return out
