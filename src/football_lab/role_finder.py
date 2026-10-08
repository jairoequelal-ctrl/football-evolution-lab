"""Club player-season style comparison. Historical sample, not replacement ability."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score,adjusted_rand_score
from .pipeline import ROOT,REV,get_json,exposure
FEATURES=['npxg_p90','shots_p90','key_passes_p90','xa_p90','box_passes_p90','progressive_passes_p90','successful_dribbles_p90']
GROUPS={'Mixto':FEATURES,'Creación':['key_passes_p90','xa_p90','box_passes_p90','progressive_passes_p90'],'Finalización':['npxg_p90','shots_p90']}
KEYS=['player_id','player_name','team','competition','season']

def player_rows(match,events):
    """All participants in a match; no fabricated ages or missing xG imputation."""
    people={}
    for e in events:
        if e.get('period',1)>4:continue
        if 'player' in e:people[e['player']['id']]=(e['player']['name'],e['team']['name'])
        for p in e.get('tactics',{}).get('lineup',[]):people[p['player']['id']]=(p['player']['name'],e['team']['name'])
    by_player={pid:[] for pid in people}
    shots={e['id']:e['shot'] for e in events if 'shot' in e and e.get('period',1)<=4}
    for e in events:
        if e.get('period',1)<=4 and e.get('player',{}).get('id') in by_player:by_player[e['player']['id']].append(e)
    rows=[]
    for pid,(name,team) in people.items():
        minutes=exposure(events,pid)
        if minutes is None or minutes<=0:continue
        own=by_player[pid];ss=[e['shot'] for e in own if 'shot' in e];nonpen=[s for s in ss if s.get('type',{}).get('name')!='Penalty']
        if any('statsbomb_xg' not in s for s in nonpen):raise ValueError('Missing shot xG')
        passes=[e for e in own if 'pass' in e];kp=[e['pass'] for e in passes if e['pass'].get('shot_assist')]
        if any(p.get('assisted_shot_id') not in shots for p in kp):raise ValueError('Unlinked assisted shot')
        completed=[e for e in passes if 'outcome' not in e['pass']]
        box=sum(e['pass'].get('end_location',[0,0])[0]>=102 and 18<=e['pass'].get('end_location',[0,0])[1]<=62 for e in completed)
        # Fixed operational definition: complete pass advancing >=12 StatsBomb x units.
        progressive=sum(e['pass'].get('end_location',[0,0])[0]-e.get('location',[0,0])[0]>=12 for e in completed)
        rows.append(dict(player_id=pid,player_name=name,team=team,competition=match['competition'],season=str(match['season']),match_id=int(match['match_id']),minutes=minutes,npxg=sum(s['statsbomb_xg'] for s in nonpen),shots=len(ss),key_passes=len(kp),xa=sum(shots[p['assisted_shot_id']]['statsbomb_xg'] for p in kp),box_passes=box,progressive_passes=progressive,successful_dribbles=sum(e.get('dribble',{}).get('outcome',{}).get('name')=='Complete' for e in own)))
    return rows

def build_profiles(matches,min_minutes=450):
    counts=[x.removesuffix('_p90') for x in FEATURES]
    d=matches.groupby(KEYS,as_index=False).agg(**{c:(c,'sum') for c in ['minutes']+counts},games=('match_id','nunique'))
    d=d[d.minutes>=min_minutes].copy()
    for c in counts:d[c+'_p90']=90*d[c]/d.minutes
    return d.reset_index(drop=True)

def compare(profiles,target_index,mode='Mixto',limit=10):
    target=profiles.loc[target_index]
    cohort=profiles[(profiles.competition==target.competition)&(profiles.season==target.season)].copy()
    peers=cohort[cohort.player_id!=target.player_id].copy()
    if len(peers)<8:raise ValueError('At least eight other player-team-season profiles required')
    features=GROUPS[mode]
    if not np.isfinite(cohort[features].to_numpy(dtype=float)).all():raise ValueError('Nonfinite feature')
    scale=StandardScaler().fit(peers[features]);x=scale.transform(peers[features]);t=scale.transform(profiles.loc[[target_index],features])[0]
    peers['distance']=np.linalg.norm(x-t,axis=1)/np.sqrt(len(features))
    ranking=peers.sort_values(['distance','player_id','team']).drop_duplicates('player_id').head(limit)
    return ranking

def map_cohort(profiles,target_index):
    target=profiles.loc[target_index];cohort=profiles[(profiles.competition==target.competition)&(profiles.season==target.season)].copy()
    peers=cohort[cohort.player_id!=target.player_id]
    if len(peers)<8:raise ValueError('Too few peers')
    scaler=StandardScaler().fit(peers[FEATURES]);x=scaler.transform(peers[FEATURES]);allx=scaler.transform(cohort[FEATURES])
    options=[]
    for k in range(2,min(5,len(peers)-1)):
        labels=KMeans(n_clusters=k,random_state=42,n_init=20).fit_predict(x)
        if len(set(labels))==k:options.append((silhouette_score(x,labels),k))
    if not options:raise ValueError('No nondegenerate clusters')
    score,k=max(options);model=KMeans(n_clusters=k,random_state=42,n_init=20).fit(x)
    ari=[adjusted_rand_score(model.labels_,KMeans(n_clusters=k,random_state=seed,n_init=20).fit_predict(x)) for seed in [7,21,99]]
    pca=PCA(n_components=2).fit(x);coords=pca.transform(allx)
    cohort['pc1']=coords[:,0];cohort['pc2']=coords[:,1];cohort['cluster']=model.predict(allx).astype(str)
    return cohort,dict(k=k,silhouette=float(score),seed_ari_min=float(min(ari)),pca_explained_variance=float(pca.explained_variance_ratio_.sum()),peer_profiles=len(peers),features=FEATURES,selection='exploratory silhouette, k=2..4; no predictive validation')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--min-minutes',type=int,default=450);args=parser.parse_args()
    index=ROOT/'data/processed/player_match_stats.csv'
    if not index.exists():raise SystemExit('Run football_lab.pipeline first')
    m=pd.read_csv(index);m=m[m.scope=='club'].drop_duplicates('match_id');rows=[]
    for i,match in enumerate(m.to_dict('records')):
        rows.extend(player_rows(match,get_json(f"data/events/{match['match_id']}.json")))
        if (i+1)%100==0:print(f'{i+1}/{len(m)} matches',flush=True)
    profiles=build_profiles(pd.DataFrame(rows),args.min_minutes)
    out=ROOT/'artifacts/role_finder';out.mkdir(parents=True,exist_ok=True)
    profiles.to_csv(out/'club_profiles.csv',index=False)
    results=[]
    for idx in profiles.index[profiles.player_id==5503]:
        try:
            _,report=map_cohort(profiles,idx)
            t=profiles.loc[idx]
            rankings={mode:compare(profiles,idx,mode).to_dict('records') for mode in GROUPS}
            results.append(dict(target={k:t[k].item() if hasattr(t[k],'item') else t[k] for k in KEYS},clustering=report,rankings=rankings))
        except ValueError:continue
    manifest=dict(source_revision=REV,club_matches=len(m),profiles=len(profiles),min_minutes=args.min_minutes,coverage='Participants in cached Messi club matches only; not complete league populations. Same league-season comparison; no strength adjustment.',minutes='Estimated regulation minutes, stoppage excluded',results=results)
    (out/'report.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
    print(f'{len(profiles)} profiles, {len(results)} Messi targets. Saved {out}',flush=True)
if __name__=='__main__':main()
