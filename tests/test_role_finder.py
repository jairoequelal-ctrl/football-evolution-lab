import numpy as np
import pandas as pd
import pytest
from football_lab.role_finder import FEATURES,build_profiles,compare,map_cohort,player_rows

def profiles():
    rng=np.random.default_rng(8)
    rows=[]
    for pid in range(14):
        row=dict(player_id=pid,player_name=str(pid),team='club',competition='league',season='2022',minutes=900,games=10)
        row.update(dict(zip(FEATURES,rng.uniform(.1,5,len(FEATURES)))))
        rows.append(row)
    return pd.DataFrame(rows)

def test_same_cohort_excludes_target_and_not_percentage():
    d=profiles();other=d.iloc[[1]].copy();other['competition']='other';other[FEATURES]=d.loc[0,FEATURES].to_numpy();d=pd.concat([d,other],ignore_index=True)
    result=compare(d,0)
    assert 0 not in set(result.player_id)
    assert set(result.competition)=={'league'}
    assert result.distance.is_monotonic_increasing

def test_identical_style_has_zero_distance():
    d=profiles();d.loc[1,FEATURES]=d.loc[0,FEATURES]
    assert compare(d,0).iloc[0].distance==pytest.approx(0)

def test_minimum_and_weighted_exposure():
    rows=[]
    for minutes,shots in [(30,1),(90,1)]:
        row=dict(player_id=1,player_name='a',team='c',competition='l',season='s',match_id=minutes,minutes=minutes)
        row.update({f.removesuffix('_p90'):0 for f in FEATURES});row['shots']=shots;rows.append(row)
    d=build_profiles(pd.DataFrame(rows),100)
    assert d.iloc[0].shots_p90==pytest.approx(1.5)
    assert build_profiles(pd.DataFrame(rows),450).empty

def test_seed_stability_and_pca_report():
    d=profiles();mapped,r=map_cohort(d,0)
    assert len(mapped)==len(d)
    assert 0<r['pca_explained_variance']<=1
    assert -1<=r['seed_ari_min']<=1

def test_penalty_not_in_npxg_and_linked_xa():
    match=dict(match_id=1,competition='league',season='2022')
    player={'id':1,'name':'a'};team={'id':1,'name':'c'}
    events=[dict(id='xi',period=1,type={'name':'Starting XI'},team=team,tactics={'lineup':[{'player':player}]}),dict(id='p',period=1,player=player,team=team,pass_={'shot_assist':True}),dict(id='s',period=1,player=player,team=team,shot={'type':{'name':'Penalty'},'statsbomb_xg':.78})]
    events[1]['pass']={'shot_assist':True,'assisted_shot_id':'s','end_location':[110,40]};events[1]['location']=[60,40]
    row=player_rows(match,events)[0]
    assert row['npxg']==0
    assert row['xa']==.78
    assert row['progressive_passes']==1
