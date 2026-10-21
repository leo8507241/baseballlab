
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
    df['g']=df['W']+df['L']+df['T']
    df['pythag']=metrics.pythag(df['RS'],df['RA'])
    df['luck']=df['PCT']-df['pythag']
    return df.sort_values('rank')

def build_batters(teams):
    b=fetch.fetch_player('batter')
    scale=metrics.woba_scale(b.sum(numeric_only=True))
    b['woba_cal']=metrics.woba(b["HBP"], b["H"], b["Double"], b["Triple"], b["HR"],
                                      b["AB"], b["BB"], b["IBB"], b["SF"]) * scale
    b=b.merge(teams[['team','abbr']],on='abbr',how='left')
    return b,scale

def build_pitcher(teams):
    teams=fetch.team_info()
    c=fetch.fetch_player('pitcher')
    c['role']=(c['SP']>c['games']/2).map({True:'先發',False:'後援'})
    pre_con=c.sum(numeric_only=True)
    const=metrics.fip_const(pre_con["ER"], pre_con["IPOut"], pre_con["HR"], pre_con["BB"], pre_con["SO"])
    c['fip']=metrics.fip(c["HR"], c["SO"], c["BB"], c["IPOut"])
    c=c.merge(teams[['team','abbr']],on='abbr',how='left')
    return c , const


def main():
    path.mkdir(parents=True,exist_ok=True)
    teams=build_teams()
    batter, scale=build_batters(teams)
    pitcher , const=build_pitcher(teams)
    teams.to_csv(path/'teams.csv',index=False)
    batter.to_csv(path/'batter.csv',index=False)
    pitcher.to_csv(path/'pitcher.csv',index=False)
    pd.Series({'woba係數':scale,'fip係數':const}).to_csv(path/'leg_const.csv',index=False)
    print(f"球隊 {len(teams)}、打者 {len(batters)}、投手 {len(pitchers)}；"
      f"wOBA 倍數 = {scale:.3f}、FIP 常數 = {const:.2f}")

if __name__ == "__main__":
    main()
