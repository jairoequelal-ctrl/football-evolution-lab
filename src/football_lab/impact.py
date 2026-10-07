import pandas as pd
WEIGHTS={'goals_p90':0.4,'assists_p90':0.25,'key_passes_p90':0.2,'xg_p90':0.15}
def impact_score(seasons,weights=None,min_minutes=450):
    weights=WEIGHTS if weights is None else weights
    if not weights or any(k not in WEIGHTS or v<0 for k,v in weights.items()) or sum(weights.values())<=0:raise ValueError('Invalid weights')
    d=seasons[seasons.minutes>=min_minutes].copy()
    d['impact_score']=0.0
    for metric,w in weights.items():
        d['impact_score']+=d.groupby('scope')[metric].rank(pct=True)*100*w/sum(weights.values())
    return d

def on_off(matches):
    cols=['team_on_minutes','team_off_minutes','team_on_goals','team_off_goals','team_on_xg','team_off_xg']
    d=matches.groupby(['scope','team'],as_index=False)[cols].sum()
    for status in ['on','off']:
        for metric in ['goals','xg']:
            d[f'{metric}_{status}_p90']=d[f'team_{status}_{metric}'].div(d[f'team_{status}_minutes'].where(d[f'team_{status}_minutes']>0))*90
    return d
