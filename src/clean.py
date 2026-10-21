
from pathlib import Path
from src import fetch, cpbl, metrics
import pandas as pd

path=Path(__file__).resolve().parent.parent / "data" / "clean"
def build_teams():
    teams=fetch.team_info()
    standing=fetch.team_standing().reset_index()
    games=fetch.fetch_games()

    home=games.groupby('home').agg(RS=('home_runs','sum'), RA=('away_runs','sum'))
    away=games.groupby('away').agg(RS=('away_runs','sum'), RA=('home_runs','sum'))
    runs=home.add(away,fill_value=0).rename_axis('team').reset_index()
    df=standing.merge(teams[['team_id','team','color']], on='team').merge(runs,on='team')
    df['G']=df['W']+df['L']+df['T']
    df['pythag']=metrics.pythag(df['RS'],df['RA'])
    df['luck']=df['PCT']-df['pythag']
    return df.sort_values('rank')

def build_batters(teams):
    raw=fetch.fetch_player('batter')
    scale=metrics.woba_scale(raw.sum(numeric_only=True))     # 全聯盟加總算倍數
    b=raw.rename(columns={'Double':'2B','Triple':'3B'})       # 後面幾天用 2B、3B 這兩個欄位名稱
    b['1B']=b['H']-b['2B']-b['3B']-b['HR']
    b['uBB']=b['BB']-b['IBB']
    b['wOBA_calc']=metrics.woba(b['HBP'], b['H'], b['2B'], b['3B'], b['HR'],
                                b['AB'], b['BB'], b['IBB'], b['SF']) * scale
    b['ISO_calc']=metrics.iso(b['2B'], b['3B'], b['HR'], b['AB'])
    b['BABIP_calc']=metrics.babip(b['H'], b['HR'], b['AB'], b['SO'], b['SF'])
    b=b.merge(teams[['team','abbr']],on='abbr',how='left')
    return b,scale

def build_pitchers(teams):
    c=fetch.fetch_player('pitcher').rename(columns={'Double':'2B','Triple':'3B'})
    c['IP']=c['IPOut']/3
    c['role']=(c['SP']>=c['games']/2).map({True:'先發',False:'後援'})
    lg=c.sum(numeric_only=True)
    const=metrics.fip_const(lg['ER'], lg['IPOut'], lg['HR'], lg['BB'], lg['SO'])
    c['FIP_calc']=metrics.fip(c['HR'], c['SO'], c['BB'], c['IPOut'], const)
    c=c.merge(teams[['team','abbr']],on='abbr',how='left')
    return c, const


def main():
    path.mkdir(parents=True,exist_ok=True)
    teams=build_teams()
    batters, scale=build_batters(teams)
    pitchers, const=build_pitchers(teams)
    teams.to_csv(path/'teams.csv',index=False)
    batters.to_csv(path/'batters.csv',index=False)
    pitchers.to_csv(path/'pitchers.csv',index=False)
    pd.Series({'woba_scale':scale,'fip_const':const}).to_csv(path/'league_constants.csv')

    # 中職官網的上下半季戰績（抓不到就用野球革命），並跟全年戰績交叉比對
    half, source=cpbl.half_standings()
    half.assign(source=source).to_csv(path/'half_standings.csv',index=False)
    bad=cpbl.cross_check(half, teams)
    print(f"半季戰績來源：{source}；交叉比對" + ("全部一致" if bad.empty else f"對不上：{list(bad.index)}"))
    print(f"球隊 {len(teams)}、打者 {len(batters)}、投手 {len(pitchers)}；"
          f"wOBA 倍數 = {scale:.3f}、FIP 常數 = {const:.2f}")

if __name__ == "__main__":
    main()
