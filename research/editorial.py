"""Original editorial charts; sourced photo, exact charts, explicit denominators."""
from pathlib import Path
import json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Arc
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'artifacts/editorial';O.mkdir(exist_ok=True,parents=True)
REV='4b73468fc5b0f1950f9f66fada70ad3a4f9327cb'
m=pd.read_csv(ROOT/'data/processed/player_match_stats.csv');s=pd.read_csv(ROOT/'data/processed/season_stats.csv');shots=pd.read_csv(ROOT/'data/processed/shots.csv')
rows=[]
for year in ['2018','2022']:
 a=m[(m.competition=='FIFA World Cup')&(m.season.astype(str)==year)];den=num=created=attempts=0
 for r in a.itertuples():
  ev=json.loads((ROOT/f'data/raw/{REV}/data/events/{r.match_id}.json').read_text())
  own=[e for e in ev if e.get('player',{}).get('id')==5503 and e.get('period',1)<=4]
  tid=own[0]['team']['id'];teamshots={e['id'] for e in ev if 'shot' in e and e['team']['id']==tid and e.get('period',1)<=4}
  ms={e['id'] for e in own if 'shot' in e};ks={e['pass']['assisted_shot_id'] for e in own if e.get('pass',{}).get('shot_assist') and e.get('pass',{}).get('assisted_shot_id') in teamshots}
  den+=len(teamshots);num+=len(ms|ks);attempts+=len(ms);created+=len(ks)
 rows.append({'year':year,'matches':len(a),'team_shots':den,'messi_shots':attempts,'created_shots':created,'unique_involved_shots':num,'share_pct':100*num/den})
share=pd.DataFrame(rows);share.to_csv(O/'shot_involvement.csv',index=False)
BG='#160f29';PINK='#ff428e';CYAN='#76d5f4';WHITE='#faf8fd';GREY='#b8afc9'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':WHITE,'axes.labelcolor':WHITE,'xtick.color':GREY,'ytick.color':WHITE,'font.size':12})
photo=plt.imread(ROOT/'research/assets/messi.jpg');logo=plt.imread(ROOT/'assets/statsbomb-logo.png')
def card(name,title,subtitle,draw,note):
 for fmt,size in [('LinkedIn',(10.8,13.5)),('X',(16,9))]:
  f=plt.figure(figsize=size,facecolor=BG,dpi=100)
  portrait=f.add_axes([.69,.57,.26,.35] if fmt=='LinkedIn' else [.76,.29,.20,.60]);portrait.imshow(photo);portrait.axis('off')
  f.text(.055,.94,'FOOTBALL EVOLUTION LAB',color=CYAN,fontsize=13,weight='bold')
  f.text(.055,.865,title,color=WHITE,fontsize=27 if fmt=='LinkedIn' else 25,weight='bold',va='top')
  f.text(.055,.755,subtitle,color=GREY,fontsize=13,va='top')
  ax=f.add_axes([.23,.235,.67,.32] if fmt=='LinkedIn' else [.20,.25,.50,.41],facecolor=BG);draw(ax)
  f.text(.055,.155,note,fontsize=11,color=WHITE,va='top')
  f.text(.055,.065,'Datos: StatsBomb Open Data · cobertura parcial · Jairo Quelal',fontsize=9,color=GREY)
  f.text(.055,.04,'Foto: H. Zohrevand / Tasnim · CC BY 4.0 · Wikimedia Commons',fontsize=8,color=GREY)
  l=f.add_axes([.81,.025,.15,.045]);l.imshow(logo);l.axis('off')
  f.savefig(O/f'{name}_{fmt}.png',dpi=160,facecolor=BG)
  plt.close(f)
def polish(ax):
 ax.spines[['top','right','left']].set_visible(False);ax.spines['bottom'].set_color(GREY);ax.tick_params(length=0);ax.grid(axis='x',alpha=.12);ax.set_axisbelow(True)
def involvement(ax):
 y=np.arange(len(share));ax.barh(y,share.messi_shots,label='Disparos de Messi',color=PINK,height=.45);ax.barh(y,share.created_shots,left=share.messi_shots,label='Ocasiones creadas',color=CYAN,height=.45)
 ax.set_yticks(y,share.year);ax.set_xlim(0,60)
 for i,r in enumerate(share.itertuples()):ax.text(r.unique_involved_shots+1,i,f'{r.unique_involved_shots} · {r.share_pct:.1f}%',va='center',fontsize=14,weight='bold')
 ax.set_xlabel('Disparos del equipo en los que participa');ax.legend(loc='upper left',bbox_to_anchor=(0,1.09),frameon=False,labelcolor=WHITE,ncol=2,fontsize=10);polish(ax)
card('01_participacion','CREAR TAMBIÉN\nES ATACAR','Messi con Argentina · Mundiales 2018 y 2022\nDisparos propios + disparos asistidos, sin duplicados.',involvement,'Porcentaje sobre todos los disparos de Argentina en los partidos cubiertos.\nIncluye minutos sin Messi. No es una medida causal ni toda su carrera.')
ci=pd.read_csv(ROOT/'artifacts/research/season_uncertainty.csv').nlargest(5,'rate').sort_values('rate')
def ranking(ax):
 ax.errorbar(ci.rate,np.arange(len(ci)),xerr=[ci.rate-ci.low,ci.high-ci.rate],fmt='o',markersize=8,color=PINK,ecolor=CYAN,capsize=5);ax.set_yticks(range(len(ci)),[x.replace('Barcelona ','') for x in ci.label]);ax.set_xlabel('(Goles + asistencias) / 90 min');polish(ax)
card('02_pico','EL PICO NO ES\nUNA SOLA CIFRA','Barcelona · cinco temporadas con mayor tasa puntual\nIntervalos del 95% · bootstrap por bloques.',ranking,'2012/13 lidera la muestra; la diferencia frente a 2011/12 no es concluyente.\nMinutos estimados sin descuento. Intervalos condicionados a la muestra.')
res=json.loads((ROOT/'artifacts/research/results.json').read_text())['temporal_validation']
def model(ax):
 names=['Media histórica','Última temporada','Ridge lineal','Ridge cuadrático'];vals=[res[n]['mae'] for n in names];ax.barh(names,vals,color=[CYAN,CYAN,PINK,PINK],height=.55);ax.set_xlim(0,.43)
 for i,v in enumerate(vals):ax.text(v+.01,i,f'{v:.3f}',va='center',weight='bold')
 ax.set_xlabel('Error absoluto medio · menor es mejor');polish(ax)
card('03_modelo','¿LA EDAD\nPREDICE MEJOR?','18 temporadas de clubes · diez pruebas cronológicas\nEntrenamiento expansivo; sin ajustar con tasas futuras.',model,'La media histórica supera a los modelos de edad en esta evaluación.\nLa edad media observada es retrospectiva; no es un pronóstico desplegado.')
def roles(ax):
 d=s[(s.team=='Barcelona')&(s.minutes>=450)].sort_values('first_date');xx=np.arange(len(d));ax.plot(xx,d.shots_p90,color=PINK,lw=3,label='Disparos / 90');ax.plot(xx,d.key_passes_p90,color=CYAN,lw=3,label='Pases clave / 90');ax.set_xticks(xx[::3],d.season.iloc[::3],rotation=30,fontsize=10);ax.set_ylabel('Acciones / 90 min');ax.legend(frameon=False,labelcolor=WHITE,fontsize=10);polish(ax)
card('04_creacion','DISPARAR Y\nHACER DISPARAR','Barcelona · La Liga 2005/06–2020/21\nVolumen de remate y creación de ocasiones.',roles,'Pase clave: pase marcado como asistencia de disparo por StatsBomb.\nSon métricas de acciones; no prueban un cambio de rol táctico.')
# Separate comparable grid of shot locations, not reconstructed touches.
f,axes=plt.subplots(1,2,figsize=(14,7),facecolor=BG);hist=[]
for year in ['2018','2022']:
 a=shots[(shots.competition=='FIFA World Cup')&(shots.season.astype(str)==year)];H,_,_=np.histogram2d(a.x,a.y,bins=[np.linspace(0,120,7),np.linspace(0,80,5)]);hist.append((a,H))
vmax=max(h.max() for _,h in hist)
for ax,year,(a,H) in zip(axes,['2018','2022'],hist):
 ax.imshow(H.T,extent=[0,120,80,0],cmap='magma',vmin=0,vmax=vmax,aspect='equal');ax.add_patch(Rectangle((0,0),120,80,fill=False,edgecolor=WHITE));ax.axvline(60,color=WHITE,alpha=.5);ax.add_patch(Rectangle((102,18),18,44,fill=False,edgecolor=WHITE));ax.add_patch(Rectangle((0,18),18,44,fill=False,edgecolor=WHITE))
 for x in range(6):
  for y in range(4):
   if H[x,y]>0:ax.text(x*20+10,y*20+10,str(int(H[x,y])),ha='center',va='center',color=BG if H[x,y]>=vmax*.7 else WHITE,weight='bold',fontsize=16)
 ax.set_title(f'{year} · {len(a)} disparos',color=WHITE,fontsize=20);ax.axis('off')
f.text(.04,.92,'¿DESDE DÓNDE DISPARA MESSI?',fontsize=24,weight='bold',color=WHITE);f.text(.04,.86,'Argentina · dos Mundiales · misma cuadrícula y escala de color · dirección de ataque →',color=GREY,fontsize=12);f.text(.04,.15,'Recuentos por zona. Diferente número de partidos; no compara tasas ni todos sus contactos con el balón.',color=WHITE,fontsize=11);f.text(.04,.08,'StatsBomb Open Data · muestra parcial · Football Evolution Lab / Jairo Quelal',color=GREY,fontsize=10);l=f.add_axes([.81,.03,.15,.05]);l.imshow(logo);l.axis('off');f.savefig(O/'05_zonas_disparos.png',dpi=160);plt.close(f)
print(share.to_string(index=False))
