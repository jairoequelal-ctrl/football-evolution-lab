import numpy as np
import pandas as pd
from football_lab.analysis import fit_profiles,age_model,FEATURES
from football_lab.assistant import ask
import pytest

def seasons():
    rng=np.random.default_rng(42)
    d=pd.DataFrame(rng.uniform(.1,2,(12,len(FEATURES))),columns=FEATURES)
    d['minutes']=1000;d['scope']='club';d['team']='Barcelona';d['age']=np.arange(18,30);d['season']=[str(i) for i in range(12)];d['competition']='La Liga';d['games']=15;d['goals']=10;d['assists']=4;d['goal_contributions_p90']=d.goals_p90+d.assists_p90
    return d

def test_clustering_is_reproducible():
    a,r=fit_profiles(seasons());b,t=fit_profiles(seasons())
    assert a.cluster.tolist()==b.cluster.tolist()
    assert 2<=r['k']<=5 and -1<=r['silhouette']<=1

def test_age_fit_stays_within_observed_ages():
    r=age_model(seasons())
    assert min(r['age_grid'])==18 and max(r['age_grid'])==29
    assert r['mae_loocv']>=0 and r['baseline_mae_loocv']>=0

def test_missing_api_key(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    with pytest.raises(ValueError,match='OPENAI_API_KEY'):ask('test',seasons())

def test_llm_routes_to_verified_calculation(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','test-key')
    class Response:
        def raise_for_status(self):pass
        def json(self):return {'choices':[{'message':{'tool_calls':[{'function':{'name':'rank_seasons','arguments':'{"metric":"goals_p90","scope":"club","team":"Barcelona"}'}}]}}]}
    monkeypatch.setattr('football_lab.assistant.requests.post',lambda *a,**kw:Response())
    result=ask('ranking',seasons())
    assert len(result['results'])==5 and result['source']=='StatsBomb Open Data'
    assert result['results'][0]['goals_p90']==pytest.approx(seasons().goals_p90.max())
