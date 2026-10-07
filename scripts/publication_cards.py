"""Generate auditable editorial cards; do not auto-publish anything."""
import json
import pandas as pd
from football_lab.pipeline import ROOT
s=pd.read_csv(ROOT/'data/processed/season_stats.csv');manifest=json.loads((ROOT/'data/processed/manifest.json').read_text())
d=s[(s.scope=='club')&(s.minutes>=450)]
if d.empty:raise RuntimeError('Insufficient coverage')
best=d.loc[d.goal_contributions_p90.idxmax()]
card={'title':'¿Qué temporada tiene mayor producción ofensiva por 90 en esta muestra?','finding':f"{best['team']} · {best['season']} · {best['competition']}: {best['goal_contributions_p90']:.2f} goles + asistencias por 90 minutos reglamentarios estimados.",'filters':{'scope':'club','minimum_minutes':450,'metric':'goal_contributions_p90'},'denominator_minutes':float(best['minutes']),'source_revision':manifest['source_revision'],'source':'StatsBomb Open Data','caveat':'Ranking entre temporadas cubiertas, no toda competición ni toda la carrera. Tasas sensibles a competición y definición de minutos.','publication_requirements':'Incluir crédito y logo StatsBomb; verificar tabla fuente antes de publicar.'}
(ROOT/'artifacts/publication_card.json').write_text(json.dumps(card,ensure_ascii=False,indent=2))
print(card['finding'])
