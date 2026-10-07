import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from football_lab.pipeline import ROOT
from football_lab.assistant import answer_tool, ask
from football_lab.charts import brand
def chart(fig, **kwargs):
    st.plotly_chart(brand(fig), **kwargs)
st.set_page_config(page_title="Messi · Football Evolution Lab",page_icon="⚽",layout="wide")
st.markdown("<style>.stApp{background:#0b1421;color:#eff6ff}h1,h2,h3{color:#66e5c4}</style>",unsafe_allow_html=True)
st.title("⚽ La evolución de Messi")
st.caption("Football Evolution Lab · Data Science + Machine Learning + IA")
st.image(str(ROOT/'assets/statsbomb-logo.png'),width=160)
p=ROOT/'data/processed'
if not (p/'manifest.json').exists():st.error('Ejecuta python -m football_lab.pipeline y python -m football_lab.analysis');st.stop()
s=pd.read_csv(p/'season_stats.csv');m=pd.read_csv(p/'player_match_stats.csv');shots=pd.read_csv(p/'shots.csv');manifest=json.loads((p/'manifest.json').read_text())
st.info('Datos: StatsBomb Open Data. Son partidos disponibles, no toda su carrera. Barcelona/PSG/Miami: ligas cubiertas; Argentina: torneos seleccionados. Minutos reglamentarios estimados, sin descuento.')
with st.sidebar:
    st.header('Explorar')
    scope=st.radio('Ámbito',['club','national'],format_func=lambda x:'Clubes' if x=='club' else 'Argentina')
    teams=st.multiselect('Equipos',sorted(s[s.scope==scope].team.unique()),default=sorted(s[s.scope==scope].team.unique()))
    min_minutes=st.slider('Mínimo de minutos por temporada',0,3000,450,50)
    st.caption('Las tasas por 90 se calculan sumando primero los minutos y eventos.')
d=s[(s.scope==scope)&s.team.isin(teams)&(s.minutes>=min_minutes)]
cols=st.columns(4)
for col,label,val in zip(cols,['Partidos cubiertos','Goles','Asistencias StatsBomb','Minutos reglamentarios'],[d.games.sum(),d.goals.sum(),d.assists.sum(),round(d.minutes.sum())]):col.metric(label,int(val))
tabs=st.tabs(['Carrera','Mapa de disparos','Machine Learning','Preguntar / IA','Datos y cobertura','Impacto y equipo'])
with tabs[0]:
    metric=st.selectbox('Métrica',['goals_p90','assists_p90','goal_contributions_p90','key_passes_p90','dribbles_p90','xg_p90'])
    chart(px.line(d,x='age',y=metric,color='team',markers=True,hover_data=['season','competition','minutes'],template='plotly_dark'),width="stretch")
    st.dataframe(d[['season','team','competition','games','minutes','goals','assists','goals_p90','assists_p90']],hide_index=True)
with tabs[1]:
    ids=set(m[(m.scope==scope)&m.team.isin(teams)].match_id);q=shots[shots.match_id.isin(ids)]
    only_goals=st.checkbox('Solo goles',True)
    if only_goals:q=q[q.outcome=='Goal']
    seasons=st.multiselect('Temporadas del mapa',sorted(q.season.unique()))
    if seasons:q=q[q.season.isin(seasons)]
    st.caption('Campo StatsBomb: 120 × 80. Distancia aproximada con campo estándar 105 × 68 m. Tandas excluidas.')
    fig=px.scatter(q,x='x',y='y',color='body_part',size='xg',hover_data=['date','opponent','shot_type','distance_m'],template='plotly_dark')
    fig.update_xaxes(range=[0,120]);fig.update_yaxes(range=[80,0],scaleanchor='x',scaleratio=1)
    fig.add_shape(type='rect',x0=0,x1=120,y0=0,y1=80,line_color='white');fig.add_shape(type='rect',x0=102,x1=120,y0=18,y1=62,line_color='white')
    chart(fig,width="stretch")
    if st.checkbox('Mapa de densidad'):chart(px.density_heatmap(q,x='x',y='y',nbinsx=24,nbinsy=16,template='plotly_dark'),width="stretch")
    if st.checkbox('Animación por temporada') and not q.empty:
        animation=px.scatter(q.sort_values('date'),x='x',y='y',animation_frame='season',color='body_part',range_x=[0,120],range_y=[80,0],template='plotly_dark');chart(animation,width="stretch")
with tabs[2]:
    report_path=ROOT/'artifacts/model_report.json'
    if report_path.exists():
        report=json.loads(report_path.read_text());profiles=pd.read_csv(ROOT/'artifacts/profiles.csv')
        st.warning('ML entrenado sobre temporadas de clubes con al menos 450 minutos. Análisis exploratorio. Los grupos no son posiciones tácticas ni rankings. La curva de edad no es una predicción del futuro.')
        if 'cluster' in profiles:
            profiles['cluster']=profiles.cluster.astype(str)
            chart(px.scatter(profiles,x='goals_p90',y='key_passes_p90',color='cluster',hover_data=['season','team','age'],template='plotly_dark'),width="stretch")
            st.dataframe(profiles.groupby('cluster')[report['clustering']['features']].mean())
        age=report['age_model']
        if age.get('status')=='ok':
            fig=px.scatter(s[s.scope=='club'],x='age',y='goal_contributions_p90',color='team',hover_data=['season'],template='plotly_dark')
            fig.add_trace(go.Scatter(x=age['age_grid'],y=age['fitted_p90'],name='Curva descriptiva Ridge',mode='lines'))
            chart(fig,width="stretch")
        st.json(report)
with tabs[3]:
    st.subheader('Consulta verificable sin API')
    metric=st.selectbox('Ranking',sorted(__import__('football_lab.assistant',fromlist=['METRICS']).METRICS))
    result=answer_tool(s,metric,scope)
    st.dataframe(pd.DataFrame(result['results']),hide_index=True);st.caption(result['warning'])
    st.subheader('IA: lenguaje natural → consulta estructurada')
    question=st.text_input('Pregunta','¿Qué temporadas tienen más goles por 90 minutos?')
    if st.button('Consultar con IA'):
        try:st.json(ask(question,s))
        except Exception as e:st.error(str(e))
    st.caption('Requiere OPENAI_API_KEY en el entorno. La IA elige una herramienta; los números se calculan con pandas. No se envía el dataset completo.')
with tabs[4]:
    st.json(manifest)
    st.dataframe(s.groupby(['scope','team','competition']).agg(temporadas=('season','nunique'),partidos=('games','sum')).reset_index())
    for filename in ['season_stats.csv','player_match_stats.csv','shots.csv']:
        st.download_button('Descargar '+filename,(p/filename).read_bytes(),file_name=filename,mime='text/csv')
    st.caption('Crédito obligatorio: StatsBomb Open Data. Antes de publicar imágenes, incluye el logo oficial y revisa docs/StatsBomb-LICENSE.pdf.')

with tabs[5]:
    from football_lab.impact import impact_score,on_off,WEIGHTS
    st.subheader('Índice de impacto configurable')
    st.caption('Percentiles entre temporadas cubiertas del mismo ámbito. No mide grandeza; los componentes están correlacionados. No comparar directamente ligas o épocas.')
    weights={k:st.slider(k,0.0,1.0,float(v),0.05,key='weight_'+k) for k,v in WEIGHTS.items()}
    if sum(weights.values())>0:
        scored=impact_score(s[s.scope==scope],weights)
        chart(px.bar(scored.sort_values('impact_score',ascending=False),x='season',y='impact_score',color='team',template='plotly_dark'),width="stretch")
    st.subheader('Equipo: intervalos con Messi en cancha y fuera de ella')
    st.warning('Solo intervalos de partidos cubiertos en los que participó. No incluye una muestra completa de partidos sin Messi ni identifica su efecto causal. Sustituciones, estado del marcador y rivales sesgan la comparación.')
    if 'team_on_minutes' in m:st.dataframe(on_off(m[m.scope==scope]),hide_index=True)
    else:st.info('Regenera el dataset para calcular intervalos.')

with tabs[4]:
    st.subheader('Títulos verificados: Barcelona')
    st.caption('Catálogo inicial: los 35 títulos con Barcelona. No es su palmarés completo actualizado.')
    st.dataframe(pd.read_csv(ROOT/'data/reference/honours.csv'),hide_index=True)
