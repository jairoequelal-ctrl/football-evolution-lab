"""Pinned StatsBomb source, explicit coverage and event-derived statistics."""
import argparse, concurrent.futures, hashlib, json, math, time
from datetime import date
from pathlib import Path
import pandas as pd
import requests
ROOT = Path(__file__).resolve().parents[2]
REV = "4b73468fc5b0f1950f9f66fada70ad3a4f9327cb"
BASE = f"https://raw.githubusercontent.com/statsbomb/open-data/{REV}/"
BIRTH = {5503: "1987-06-24"}
OFFSETS = {1: 0, 2: 45, 3: 90, 4: 105}
ENDS = {1: 45, 2: 90, 3: 105, 4: 120}

def get_json(path):
    local = ROOT / "data/raw" / REV / path
    if local.exists():
        return json.loads(local.read_text())
    for attempt in range(4):
        try:
            response = requests.get(BASE + path, timeout=60)
            response.raise_for_status()
            value = response.json()
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_text(json.dumps(value), encoding="utf-8")
            return value
        except (requests.RequestException, ValueError):
            if attempt == 3: raise
            time.sleep(2 ** attempt)

def clock(e):
    """Regulation clock: stoppage time excluded consistently from exposure."""
    p = e.get("period", 1)
    if p not in OFFSETS: return None
    h, m, s = map(float, e.get("timestamp", "00:00:00").split(":"))
    return min(ENDS[p], OFFSETS[p] + h*60 + m + s/60)

def exposure(events, player_id):
    end = max((ENDS[e["period"]] for e in events if e.get("period") in ENDS), default=90)
    start = None
    for e in events:
        if e.get("type", {}).get("name") == "Starting XI":
            if any(p["player"]["id"] == player_id for p in e.get("tactics", {}).get("lineup", [])):
                start = 0.0
        if e.get("substitution", {}).get("replacement", {}).get("id") == player_id:
            start = clock(e)
    if start is None: return None
    stop = end
    for e in events:
        if e.get("player", {}).get("id") != player_id: continue
        card = e.get("bad_behaviour", {}).get("card", {}).get("name") or e.get("foul_committed", {}).get("card", {}).get("name")
        if e.get("type", {}).get("name") == "Substitution" or card in {"Red Card", "Second Yellow"}:
            if clock(e) is not None: stop = min(stop, clock(e))
    return max(0., stop-start)

def extract(match, events, player_id, birthdate):
    minutes = exposure(events, player_id)
    if minutes is None: return None, []
    own = [e for e in events if e.get("player", {}).get("id") == player_id and e.get("period", 1) <= 4]
    team_id = next(e["team"]["id"] for e in events if e.get("player", {}).get("id") == player_id)
    home = match["home_team"]; away = match["away_team"]
    home_side = team_id == home["home_team_id"]
    team = home["home_team_name"] if home_side else away["away_team_name"]
    opponent = away["away_team_name"] if home_side else home["home_team_name"]
    dob = date.fromisoformat(birthdate); played = date.fromisoformat(match["match_date"])
    base = dict(player_id=player_id, player_name=next(e["player"]["name"] for e in own), match_id=match["match_id"], date=match["match_date"], season=match["season"]["season_name"], competition=match["competition"]["competition_name"], team=team, opponent=opponent, scope="national" if match["competition"]["competition_name"] in {"FIFA World Cup","Copa America","UEFA Euro"} else "club", age=(played-dob).days/365.2425, minutes=minutes, team_goals=match["home_score"] if home_side else match["away_score"], opponent_goals=match["away_score"] if home_side else match["home_score"])
    shots=[]
    for e in own:
        if "shot" not in e: continue
        s=e["shot"]; loc=e.get("location", [None,None]); x,y=loc[:2]
        distance=math.hypot((120-x)*105/120,(40-y)*68/80) if x is not None and y is not None else None
        shots.append(dict(**base,event_id=e["id"],period=e["period"],minute=e["minute"],x=x,y=y,distance_m=distance,xg=s.get("statsbomb_xg"),outcome=s.get("outcome",{}).get("name"),body_part=s.get("body_part",{}).get("name"),shot_type=s.get("type",{}).get("name"),play_pattern=e.get("play_pattern",{}).get("name")))
    passes=[e["pass"] for e in own if "pass" in e]
    # Within-match on/off comparison: not before/after causal impact.
    start = 0.0
    for event in events:
        if event.get('substitution',{}).get('replacement',{}).get('id')==player_id:
            start=clock(event)
    finish=start+minutes
    duration=max((ENDS[e['period']] for e in events if e.get('period') in ENDS),default=90)
    on_goals=off_goals=0;on_xg=off_xg=0.0
    for event in events:
        c=clock(event)
        if c is None:continue
        active=start<=c<=finish
        if event.get('team',{}).get('id')==team_id and 'shot' in event:
            shot=event['shot'];is_goal=shot.get('outcome',{}).get('name')=='Goal'
            if active:on_goals+=int(is_goal);on_xg+=shot.get('statsbomb_xg',0)
            else:off_goals+=int(is_goal);off_xg+=shot.get('statsbomb_xg',0)
        if event.get('type',{}).get('name')=='Own Goal Against' and event.get('team',{}).get('id')!=team_id:
            if active:on_goals+=1
            else:off_goals+=1
    row=dict(**base,team_on_minutes=minutes,team_off_minutes=duration-minutes,team_on_goals=on_goals,team_off_goals=off_goals,team_on_xg=on_xg,team_off_xg=off_xg,goals=sum(s["outcome"]=="Goal" for s in shots),assists=sum(bool(p.get("goal_assist")) for p in passes),shots=len(shots),xg=sum(s["xg"] or 0 for s in shots),key_passes=sum(bool(p.get("shot_assist")) for p in passes),passes=len(passes),completed_passes=sum("outcome" not in p for p in passes),dribbles=sum("dribble" in e for e in own),successful_dribbles=sum(e.get("dribble",{}).get("outcome",{}).get("name")=="Complete" for e in own))
    return row,shots

def aggregate(matches):
    keys=["player_id","player_name","scope","team","competition","season"]
    counts=["minutes","goals","assists","shots","xg","key_passes","passes","completed_passes","dribbles","successful_dribbles"]
    s=matches.groupby(keys,as_index=False).agg(**{c:(c,"sum") for c in counts},games=("match_id","nunique"),age=("age","mean"),first_date=("date","min"),last_date=("date","max"))
    for c in ["goals","assists","shots","xg","key_passes","dribbles","passes"]:
        s[c+"_p90"]=s[c].div(s.minutes.where(s.minutes>0))*90
    s["goal_contributions_p90"]=s.goals_p90+s.assists_p90
    return s.sort_values("first_date")

def run(player_id=5503,birthdate="1987-06-24",limit=None,workers=8,teams=None):
    comps=get_json("data/competitions.json")
    selected=[c for c in comps if (c["competition_name"]=="La Liga" and c["season_name"]>="2004") or (c["competition_name"]=="Ligue 1" and c["season_name"] in {"2021/2022","2022/2023"}) or c["competition_name"]=="Major League Soccer" or (c["competition_name"]=="FIFA World Cup" and c["season_name"] in {"2018","2022"}) or c["competition_name"]=="Copa America"]
    candidates=[]
    def competition_matches(c):
        return get_json(f"data/matches/{c['competition_id']}/{c['season_id']}.json")
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        match_lists=list(pool.map(competition_matches, selected))
    for ms in match_lists:
        for m in ms:
            names={m["home_team"]["home_team_name"],m["away_team"]["away_team_name"]}
            if names & set(teams or ["Barcelona","Paris Saint-Germain","Inter Miami","Argentina"]): candidates.append(m)
    candidates=sorted({m['match_id']:m for m in candidates}.values(),key=lambda m:m['match_date'])
    if limit: candidates=candidates[:limit]
    rows=[];shots=[];failures=[]
    def process(m):
        return extract(m,get_json(f"data/events/{m['match_id']}.json"),player_id,birthdate)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        future_map={pool.submit(process,m):m for m in candidates}
        for i,f in enumerate(concurrent.futures.as_completed(future_map),1):
            try:
                row,ss=f.result()
                if row: rows.append(row);shots.extend(ss)
            except Exception as exc:
                failures.append({"match_id":future_map[f]['match_id'],"error":str(exc)})
            if i%40==0: print(f"Processed {i}/{len(candidates)}",flush=True)
    if not rows: raise RuntimeError("No appearances downloaded")
    p=ROOT/"data/processed";p.mkdir(parents=True,exist_ok=True)
    matches=pd.DataFrame(rows).sort_values('date');seasons=aggregate(matches)
    matches.to_csv(p/'player_match_stats.csv',index=False)
    pd.DataFrame(shots).sort_values(['date','minute']).to_csv(p/'shots.csv',index=False)
    seasons.to_csv(p/'season_stats.csv',index=False)
    manifest={"source":"StatsBomb Open Data","source_revision":REV,"retrieved_at":date.today().isoformat(),"player_id":player_id,"birthdate":birthdate,"candidate_matches":len(candidates),"appearances":len(rows),"failed_matches":failures,"sample_limit":limit,"coverage":"Selected league seasons and international tournaments only; not career totals.","minutes_definition":"Regulation exposure inferred from starting XI, substitutions and red cards; stoppage excluded, temporary injury absences not tracked."}
    (p/'manifest.json').write_text(json.dumps(manifest,indent=2))
    for file in ['player_match_stats.csv','shots.csv','season_stats.csv']:
        manifest.setdefault('sha256',{})[file]=hashlib.sha256((p/file).read_bytes()).hexdigest()
    (p/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2),flush=True)
    if failures: raise RuntimeError("Partial export: inspect failed_matches before publishing")

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--limit',type=int);a.add_argument('--workers',type=int,default=8);a.add_argument('--player-id',type=int,default=5503);a.add_argument('--birthdate',default='1987-06-24');a.add_argument('--teams',nargs='+');args=a.parse_args();run(args.player_id,args.birthdate,args.limit,args.workers,args.teams)
