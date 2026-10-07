"""Portable interactive HTML for reviewing/exporting; not hosted automatically."""
import json
import pandas as pd
import plotly.express as px
from football_lab.pipeline import ROOT
from football_lab.charts import brand
s=pd.read_csv(ROOT/'data/processed/season_stats.csv');q=pd.read_csv(ROOT/'data/processed/shots.csv');q=q[q.outcome=='Goal']
charts=[px.line(s[s.scope=='club'],x='age',y='goal_contributions_p90',color='team',markers=True,hover_data=['season','competition'],title='Producción ofensiva por edad · clubes',template='plotly_dark'),px.scatter(q,x='x',y='y',color='team',hover_data=['date','opponent','body_part'],title='Goles con coordenadas disponibles',template='plotly_dark')]
charts[1].update_xaxes(range=[0,120]);charts[1].update_yaxes(range=[80,0])
html='<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Messi · Football Evolution Lab</title><style>body{background:#0b1421;color:#edf5ff;font:17px system-ui;max-width:1100px;margin:40px auto;padding:20px}h1{color:#66e5c4}.note{padding:20px;background:#16283c;border-radius:16px}a{color:#66e5c4}</style><h1>La evolución de Messi</h1><p>Football Evolution Lab · Análisis reproducible</p><div class="note">Fuente: StatsBomb Open Data. Cobertura parcial: ligas de clubes y torneos seleccionados con Argentina. No son totales de carrera. Minutos reglamentarios estimados; comparaciones descriptivas, sin atribución causal.</div>'
import base64
logo=base64.b64encode((ROOT/'assets/statsbomb-logo.png').read_bytes()).decode()
html+=f'<p><img alt="StatsBomb" style="width:180px;background:white;padding:12px" src="data:image/png;base64,{logo}"></p>'
for i,c in enumerate(charts):html+=brand(c).to_html(full_html=False,include_plotlyjs=True if i==0 else False)
html+='<h2>Datos por temporada</h2>'+s[['season','team','competition','games','goals','assists']].to_html(index=False)+'<p><a href="https://github.com/statsbomb/open-data">Datos y licencia de StatsBomb</a></p></html>'
(ROOT/'artifacts/messi_explorer.html').write_text(html)
