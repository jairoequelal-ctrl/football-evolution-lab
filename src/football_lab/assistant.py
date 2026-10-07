"""LLM routes to an allowlisted analytical tool; it never invents SQL or figures."""
import json, os
import pandas as pd
import requests
METRICS={'goals','assists','games','minutes','goals_p90','assists_p90','goal_contributions_p90','key_passes_p90','xg_p90'}

def answer_tool(seasons, metric='goals_p90',scope='club',team=None):
    if metric not in METRICS or scope not in {'club','national'}:raise ValueError('Unsupported metric or scope')
    d=seasons[seasons.scope==scope]
    if team is not None:
        if team not in set(seasons.team):raise ValueError('Unknown team')
        d=d[d.team==team]
    if metric.endswith('_p90'):d=d[d.minutes>=450]
    top=d.nlargest(5,metric)[['season','team','competition','games','minutes',metric]]
    return {'metric':metric,'scope':scope,'team':team,'minimum_minutes':450 if metric.endswith('_p90') else 0,'results':json.loads(top.to_json(orient='records')),'source':'StatsBomb Open Data','warning':'Only covered matches; this is not a full career ranking. League and national tournaments have different context.'}

def ask(question,seasons):
    key=os.getenv('OPENAI_API_KEY')
    if not key:raise ValueError('Configura OPENAI_API_KEY para activar la IA. Las consultas verificables funcionan sin clave.')
    teams=sorted(set(seasons.team))
    schema={'type':'object','properties':{'metric':{'type':'string','enum':sorted(METRICS)},'scope':{'type':'string','enum':['club','national']},'team':{'anyOf':[{'type':'string','enum':teams},{'type':'null'}]}},'required':['metric','scope','team'],'additionalProperties':False}
    response=requests.post('https://api.openai.com/v1/chat/completions',headers={'Authorization':f'Bearer {key}'},json={'model':os.getenv('OPENAI_MODEL','gpt-4.1-mini'),'messages':[{'role':'system','content':'Selecciona una consulta de ranking por temporada dentro de los datos disponibles. No respondas con cifras. Para Argentina usa scope national. Si la pregunta no corresponde, no invoques herramientas.'},{'role':'user','content':question[:2000]}],'tools':[{'type':'function','function':{'name':'rank_seasons','description':'Top 5 temporadas cubiertas por una métrica; no calcula causalidad ni títulos.','parameters':schema,'strict':True}}],'tool_choice':'auto'},timeout=45)
    response.raise_for_status();message=response.json()['choices'][0]['message'];calls=message.get('tool_calls',[])
    if not calls:return {'notice':'Esta versión responde rankings por temporada. Prueba: ¿Qué temporadas tienen más goles por 90 minutos?'}
    if calls[0]['function']['name']!='rank_seasons':raise ValueError('Unknown tool')
    args=json.loads(calls[0]['function']['arguments']);return answer_tool(seasons,**args)
