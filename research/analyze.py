"""Reproducible exploratory analysis. Run from repository root after build.sh."""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import Ridge
from sklearn.metrics import adjusted_rand_score, mean_absolute_error, mean_squared_error
from football_lab.analysis import FEATURES, fit_profiles, age_model
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/research'; OUT.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(20261007)
m=pd.read_csv(ROOT/'data/processed/player_match_stats.csv').sort_values('date')
s=pd.read_csv(ROOT/'data/processed/season_stats.csv')
sh=pd.read_csv(ROOT/'data/processed/shots.csv')
d=s[(s.scope=='club')&(s.minutes>=450)].sort_values('first_date').copy().reset_index(drop=True)
B=2000
boots={}; rows=[]
for _,r in d.iterrows():
 a=m[(m.team==r.team)&(m.season==r.season)].sort_values('date'); n=len(a)
 def bootstrap(block):
  starts=rng.integers(n,size=(B,int(np.ceil(n/block))))
  ix=((starts[:,:,None]+np.arange(block))%n).reshape(B,-1)[:,:n]
  counts=(a.goals+a.assists).to_numpy()[ix].sum(1); mins=a.minutes.to_numpy()[ix].sum(1)
  return counts/mins*90
 v=bootstrap(3); label=f'{r.team} {r.season}'; boots[label]=v
 row={'label':label,'rate':r.goal_contributions_p90,'low':np.quantile(v,.025),'high':np.quantile(v,.975),'games':len(a),'age':r.age}
 for block in [1,5]:
  vv=bootstrap(block);row[f'low_b{block}']=np.quantile(vv,.025);row[f'high_b{block}']=np.quantile(vv,.975)
 rows.append(row)
ci=pd.DataFrame(rows);ci.to_csv(OUT/'season_uncertainty.csv',index=False)
delta=boots['Barcelona 2012/2013']-boots['Barcelona 2011/2012']
forecast=[]
for i in range(8,len(d)):
 train=d.iloc[:i];test=d.iloc[[i]];y=float(test.goal_contributions_p90.iloc[0])
 for name,degree in [('Ridge lineal',1),('Ridge cuadrático',2)]:
  model=make_pipeline(PolynomialFeatures(degree,include_bias=False),StandardScaler(),Ridge(alpha=10))
  model.fit(train[['age']],train.goal_contributions_p90)
  forecast.append({'test':str(test.season.iloc[0]),'model':name,'actual':y,'prediction':float(model.predict(test[['age']])[0])})
 for name,pred in [('Media histórica',train.goal_contributions_p90.mean()),('Última temporada',train.goal_contributions_p90.iloc[-1])]:
  forecast.append({'test':str(test.season.iloc[0]),'model':name,'actual':y,'prediction':float(pred)})
f=pd.DataFrame(forecast);f.to_csv(OUT/'temporal_predictions.csv',index=False)
errors={name:{'mae':mean_absolute_error(g.actual,g.prediction),'rmse':float(np.sqrt(mean_squared_error(g.actual,g.prediction))),'n':len(g)} for name,g in f.groupby('model')}
profiles,report=fit_profiles(s);x=profiles[FEATURES].to_numpy();z=StandardScaler().fit_transform(x);base=profiles.cluster.to_numpy();k=report['k']
seed_ari=[adjusted_rand_score(base,KMeans(n_clusters=k,n_init=20,random_state=j).fit_predict(z)) for j in range(100)]
drop_ari=[]
for i in range(len(x)):
 mask=np.arange(len(x))!=i; zz=StandardScaler().fit_transform(x[mask]);lab=KMeans(n_clusters=k,n_init=20,random_state=42).fit_predict(zz)
 drop_ari.append(adjusted_rand_score(base[mask],lab))
stability={'k':k,'silhouette':report['silhouette'],'seed_ari_min':float(min(seed_ari)),'delete_one_ari_min':float(min(drop_ari)),'delete_one_ari_median':float(np.median(drop_ari)),'delete_one_ari':drop_ari}
goals=sh[(sh.scope=='club')&(sh.outcome=='Goal')]
body=goals.body_part.value_counts();body.to_csv(OUT/'goal_body_parts.csv')
results={'seed':20261007,'bootstrap_replicates':B,'block_length':3,'matches':len(m),'shots':len(sh),'goals':int(m.goals.sum()),'eligible_seasons':len(d),'delta_2012_vs_2011':{'estimate':float(d.loc[d.season=='2012/2013','goal_contributions_p90'].iloc[0]-d.loc[d.season=='2011/2012','goal_contributions_p90'].iloc[0]),'ci95':np.quantile(delta,[.025,.975]).tolist(),'bootstrap_fraction_positive':float((delta>0).mean())},'temporal_validation':errors,'clustering':stability,'loocv':{a:b for a,b in age_model(s).items() if a in ['mae_loocv','baseline_mae_loocv']},'input_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'data/processed').glob('*.csv')}}
(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white'})
def save(fig,name):
 fig.text(.01,.012,'Fuente: StatsBomb Open Data · muestra parcial · análisis exploratorio',fontsize=8,color='#52606d')
 logo=fig.add_axes([.82,.025,.15,.065]);logo.imshow(plt.imread(ROOT/'assets/statsbomb-logo.png'));logo.axis('off')
 fig.subplots_adjust(bottom=.30)
 for ext in ['png','svg']:fig.savefig(OUT/f'{name}.{ext}',dpi=300,bbox_inches='tight')
 plt.close(fig)
fig,ax=plt.subplots(figsize=(8,4));ax.errorbar(np.arange(len(ci)),ci.rate,yerr=[ci.rate-ci.low,ci.high-ci.rate],fmt='o-',color='#007c91',capsize=3);ax.set_xticks(range(len(ci)),[r.label.replace('Barcelona ','').replace('Paris Saint-Germain ','PSG ') for r in ci.itertuples()],rotation=55,ha='right',fontsize=8);ax.set_ylabel('(Goles + asistencias) / 90 min');ax.set_title('Evolución observada e incertidumbre por temporada');save(fig,'01_evolucion')
top=ci.nlargest(7,'rate').sort_values('rate');fig,ax=plt.subplots(figsize=(8,4));ax.errorbar(top.rate,np.arange(len(top)),xerr=[top.rate-top.low,top.high-top.rate],fmt='o',capsize=4,color='#007c91');ax.set_yticks(range(len(top)),top.label);ax.set_xlabel('(Goles + asistencias) / 90 min');ax.set_title('Las temporadas líderes tienen intervalos que se solapan');save(fig,'02_temporadas')
fig,ax=plt.subplots(figsize=(8,4));names=list(errors);ax.barh(names,[errors[n]['mae'] for n in names],color=['#007c91','#8b9da7','#8b9da7','#007c91']);ax.set_xlabel('Error absoluto medio · menor es mejor');ax.set_title('Validación temporal: 10 temporadas futuras, entrenamiento expansivo');save(fig,'03_validacion')
fig,ax=plt.subplots(figsize=(8,4));ax.hist(drop_ari,bins=np.linspace(-.1,1.1,13),color='#007c91',edgecolor='white');ax.set_xlabel('Índice Rand ajustado al retirar una temporada');ax.set_ylabel('Número de réplicas');ax.set_title('Estabilidad exploratoria de los perfiles K-means');save(fig,'04_estabilidad')
fig,ax=plt.subplots(figsize=(8,4));ax.barh(body.index,body.values,color='#007c91');ax.set_xlabel('Goles observados · clubes (n = 495)');ax.set_title('Distribución de goles por parte del cuerpo');save(fig,'05_goles')
print(json.dumps(results,ensure_ascii=False,indent=2))
