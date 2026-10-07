"""Static overview generated from real covered data, with source attribution."""
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from football_lab.pipeline import ROOT
s=pd.read_csv(ROOT/'data/processed/season_stats.csv');q=pd.read_csv(ROOT/'data/processed/shots.csv');q=q[(q.outcome=='Goal')&(q.scope=='club')]
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':'#e9f3ff','axes.labelcolor':'#e9f3ff','xtick.color':'#b6c9dd','ytick.color':'#b6c9dd','axes.edgecolor':'#38506c','axes.facecolor':'#102238','figure.facecolor':'#091522'})
fig,axes=plt.subplots(2,1,figsize=(12,10));fig.subplots_adjust(top=.83,bottom=.13,hspace=.5)
fig.text(.12,.95,'LA EVOLUCIÓN DE MESSI',fontsize=27,weight='bold',color='#66e5c4')
fig.text(.12,.915,'Football Evolution Lab  |  Data Science · ML · IA',fontsize=14)
fig.text(.12,.88,'Ligas cubiertas · tasas con minutos reglamentarios estimados',fontsize=11,color='#b6c9dd')
colors={'Barcelona':'#66e5c4','Paris Saint-Germain':'#6e9fff','Inter Miami':'#ffa9d9'}
for team,g in s[(s.scope=='club')&(s.minutes>=450)].groupby('team'):
 axes[0].plot(g.age,g.goal_contributions_p90,'o-',label=team,color=colors.get(team),linewidth=2.5)
axes[0].set_title('Producción ofensiva por edad · temporadas con ≥450 minutos',loc='left',pad=15,color='#e9f3ff');axes[0].set_xlabel('Edad media en los partidos');axes[0].set_ylabel('Goles + asistencias / 90');axes[0].grid(alpha=.15);axes[0].legend(facecolor='#102238',edgecolor='#38506c',labelcolor='#e9f3ff')
axes[1].scatter(q.x,q.y,s=14,alpha=.38,color='#66e5c4');axes[1].set_xlim(0,120);axes[1].set_ylim(80,0);axes[1].set_aspect('equal');axes[1].set_title('Ubicación de goles disponibles · clubes',loc='left',pad=15,color='#e9f3ff');axes[1].set_xlabel('Coordenada X · campo StatsBomb');axes[1].set_ylabel('Y');axes[1].plot([102,102,120],[18,62,62],color='#b6c9dd',lw=1);axes[1].plot([102,120],[18,18],color='#b6c9dd',lw=1)
logoax=fig.add_axes([.72,.04,.17,.06]);logoax.imshow(Image.open(ROOT/'assets/statsbomb-logo.png'));logoax.axis('off')
fig.text(.12,.065,'Fuente: StatsBomb Open Data · cobertura parcial, no totales de carrera.',fontsize=10)
fig.text(.12,.043,'Comparaciones descriptivas; no establecen causalidad.',fontsize=10,color='#b6c9dd')
fig.savefig(ROOT/'artifacts/messi_preview.png',dpi=150)
