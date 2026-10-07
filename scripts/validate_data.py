import json
import pandas as pd
import numpy as np
from football_lab.pipeline import ROOT
p=ROOT/'data/processed';m=pd.read_csv(p/'player_match_stats.csv');s=pd.read_csv(p/'season_stats.csv');shots=pd.read_csv(p/'shots.csv')
assert not m.duplicated(['player_id','match_id']).any()
assert not shots.event_id.duplicated().any()
assert m.minutes.between(0,120).all()
assert (m.goals>=0).all() and (m.assists>=0).all()
assert (m.successful_dribbles<=m.dribbles).all()
assert (m.completed_passes<=m.passes).all()
duration=m.team_on_minutes+m.team_off_minutes
assert (np.isclose(duration,90)|np.isclose(duration,120)).all()
assert shots.x.between(0,120).all() and shots.y.between(0,80).all()
assert int(m.goals.sum())==int((shots.outcome=='Goal').sum())==int(s.goals.sum())
assert len(m)==int(s.games.sum())
assert not json.loads((p/'manifest.json').read_text())['failed_matches']
print(f'Validated {len(m)} appearances, {len(s)} season groups, {len(shots)} shots')
