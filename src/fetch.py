
import requests
import json
from bs4 import BeautifulSoup
import time
import pandas as pd
from pathlib import Path

SEASON='CPBL-2026-oB'
def get_json(path, retries=3, pause=1.0):
    for attempt in range(1,retries+1):
        try:
            session=requests.Session()
            ua='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36'

            res=session.get(path,headers={'User-agent':ua},timeout=30)
            res.raise_for_status()
            time.sleep(pause)
            return res.json()
        except (requests.RequestException, ValueError) as e:
            print(f'第{attempt}次失敗 {path} 原因：{e}')
            time.sleep(pause* attempt * 2)
    raise RuntimeError(f'抓不到資料{path}')


def cath_json(path, catch_name, refresh=True):
    path_way=Path(__file__).resolve().parent.parent/"data"/"raw"
    cath=path_way/ catch_name
    cath.parent.mkdir(parents=True,exist_ok=True)
    if cath.exists() and not refresh:
        return json.loads(cath.read_text(encoding="utf-8"))
    data=get_json(path)
    cath.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data

def team_info(season=SEASON,refresh=True):
    data=cath_json(f'https://www.rebas.tw/api/seasons/{season}/leaders?type=team&section=standard&pa=undefined',f'{season}_team.json',refresh=False)['data']
    row=[]
    for i in data:
        o=i['team']
        row.append({
            "team_id": o["uniqid"], "team": o["name"], "abbr": o["abbr"],
                     "color": o["hex_color"].split(";")[0]
        })
    return pd.DataFrame(row)
def team_standing(season=SEASON,refresh=True):
    data=cath_json(f'https://www.rebas.tw/api/seasons/{season}/leaders?type=team&section=standard&pa=undefined',f'{season}_standing.json',refresh=False)['data']
    row=[]
    for i in data:
        row.append({"rank": i["order"], "team": i["team"]["name"], "abbr": i["team"]["abbr"],
                     "W": i["wins"], "L": i["loses"], "T": i["draws"], "PCT": i["PCT"],
                     "GB": i["GB"], "DIFF": i["DIFF"]})
    return pd.DataFrame(row).set_index('rank')

def fetch_games(season=SEASON, refresh=True):
    data=cath_json(f'https://www.rebas.tw/api/seasons/{season}/games',f'games_{season}.json',refresh)['data']
    row=[]
    for i in data:
        if i['info']['status']!='FINISHED':
            continue
        row.append({"game_id": i["uniqid"], "seq": i["seq"],
                     "date": i["info"]["scheduled_start_at"][:10],
                     "away": i["away"]["team"], "home": i["home"]["team"],
                     "away_runs": i["away"]["runs"], "home_runs": i["home"]["runs"],
                     "winner_side": i["info"]["winner_side"]})
    return pd.DataFrame(row)

def fetch_player(kind,season=SEASON,refresh=True):
    data_all=[]
    for section in ['standard','advanced','new']:
        url=f'https://www.rebas.tw/api/seasons/{season}/leaders?type={kind}&section={section}&pa=undefined'
        data=cath_json(url,f'{season}_{kind}_{section}.json',refresh=refresh)['data']
        df=pd.json_normalize(data)
        df = df.rename(columns={"player.uniqid": "player_id", "player.name": "name",
                                "player.team_abbr": "abbr"})
        data_all.append(df)
    std,adv,new=data_all

    keep=['player_id']+[c for c in adv.columns if c not in std.columns]
    merge_1=std.merge(adv[keep],on='player_id',how='left')
    keep_1=['player_id']+[d for d in new.columns if d not in merge_1.columns]
    merge_2=merge_1.merge(new[keep_1],on='player_id',how='left')
    drop=[c for c in merge_2.columns if c.startswith('player.')]+["reach_min"]
    return merge_2.drop(columns=[c for c in drop if c in merge_2.columns])

# ---------- Day 8：逐打席紀錄 ----------
pa_path=Path(__file__).resolve().parent.parent/"data"/"raw"/"pa"

def flatten_pa(logs):
    rows=[]
    for game in logs:
        for pa in game.get('PA_list',[]):
            pitches=[e['pitch'] for e in pa.get('events',[]) if e.get('type')=='PITCH' and e.get('pitch')]
            rows.append({
                'game_id':game['uniqid'],
                'date':game['date'],
                'inning':pa.get('inning'),
                'pa_round':pa.get('PA_round'),
                'batter_id':pa['batter']['uniqid'],
                'batter':pa['batter']['name'],
                'pitcher_id':pa['pitcher']['uniqid'],
                'pitcher':pa['pitcher']['name'],
                'b_hand':pa.get('b_hand'),
                'p_hand':pa.get('p_hand'),
                'result':pa.get('result'),
                'pitch_types':','.join(p.get('type') or '' for p in pitches),
                'pitch_codes':','.join(p.get('code') or '' for p in pitches)
            })
    return rows

def fetch_pitcher_pa(player_id,season=SEASON,refresh=False):
    pa_path.mkdir(parents=True,exist_ok=True)
    file=pa_path/f'{season}_{player_id}.csv'
    if file.exists() and not refresh:
        df=pd.read_csv(file,dtype=str,keep_default_na=False)
    else:
        data_list=get_json(f'https://www.rebas.tw/api/formal/players/{player_id}/seasons/{season}/logs')['data']
        df=pd.DataFrame(flatten_pa(data_list)).astype(str)
        df.to_csv(file,index=False)
    # 野手兼投手（例如林子偉）的紀錄裡也有他當打者的打席，只留他當投手的
    return df[df['pitcher_id']==player_id]
