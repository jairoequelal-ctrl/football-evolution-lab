import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import Ridge
from sklearn.model_selection import LeaveOneOut
from .pipeline import ROOT
FEATURES=["goals_p90","assists_p90","shots_p90","key_passes_p90","dribbles_p90","passes_p90"]

def fit_profiles(seasons, min_minutes=450):
    d=seasons[(seasons.scope=='club') & (seasons.minutes>=min_minutes)].dropna(subset=FEATURES).copy()
    if len(d)<6: return d,{'status':'insufficient_data','rows':len(d)}
    z=StandardScaler().fit_transform(d[FEATURES]); results=[]
    for k in range(2,min(5,len(d)-1)+1):
        km=KMeans(n_clusters=k,n_init=20,random_state=42).fit(z)
        if len(set(km.labels_))>1: results.append((silhouette_score(z,km.labels_),k,km))
    score,k,km=max(results,key=lambda x:x[0]);d['cluster']=km.labels_.astype(int)
    report={'status':'ok','rows':len(d),'k':k,'silhouette':float(score),'features':FEATURES,'minimum_minutes':min_minutes,'candidate_scores':{str(b):float(a) for a,b,_ in results},'interpretation':'Exploratory groups, arbitrary labels. Competition and season context are confounders; not an objective ranking.'}
    return d,report

def age_model(seasons):
    d=seasons[(seasons.scope=='club') & (seasons.minutes>=450)].dropna(subset=['age','goal_contributions_p90'])
    if len(d)<6:return {'status':'insufficient_data'}
    x=d[['age']].to_numpy();y=d.goal_contributions_p90.to_numpy();pred=np.zeros(len(y));baseline=np.zeros(len(y))
    for train,test in LeaveOneOut().split(x):
        model=make_pipeline(PolynomialFeatures(2,include_bias=False),StandardScaler(),Ridge(alpha=10))
        model.fit(x[train],y[train]);pred[test]=model.predict(x[test]);baseline[test]=y[train].mean()
    model.fit(x,y);grid=np.linspace(x.min(),x.max(),100).reshape(-1,1)
    return {'status':'ok','mae_loocv':float(mean_absolute_error(y,pred)),'baseline_mae_loocv':float(mean_absolute_error(y,baseline)),'age_grid':grid.flatten().tolist(),'fitted_p90':model.predict(grid).tolist(),'interpretation':'Retrospective descriptive fit. LOOCV is not forecasting validation. Age does not establish causality; do not extrapolate beyond observed ages.'}

def build():
    s=pd.read_csv(ROOT/'data/processed/season_stats.csv');d,report=fit_profiles(s);a=age_model(s)
    out=ROOT/'artifacts';out.mkdir(exist_ok=True)
    d.to_csv(out/'profiles.csv',index=False);(out/'model_report.json').write_text(json.dumps({'clustering':report,'age_model':a},indent=2))
    payload={'source':'StatsBomb Open Data','coverage':json.loads((ROOT/'data/processed/manifest.json').read_text()),'seasons':json.loads(s.to_json(orient='records')),'models':{'clustering':report,'age_model':a}}
    (out/'web_data.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
    import duckdb
    con=duckdb.connect(str(out/'football.duckdb'))
    for name in ['season_stats','player_match_stats','shots']:
        frame=pd.read_csv(ROOT/f'data/processed/{name}.csv');con.register('frame',frame);con.execute(f'CREATE OR REPLACE TABLE {name} AS SELECT * FROM frame')
    con.close()
    return report
if __name__=='__main__':print(build())
