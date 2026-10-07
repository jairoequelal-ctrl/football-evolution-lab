import pandas as pd
import pytest
from football_lab.pipeline import clock, exposure, extract, aggregate
from football_lab.assistant import answer_tool
from football_lab.impact import impact_score,on_off

def event(kind,period=1,timestamp='00:00:00',**kw):return dict(type={'name':kind},period=period,timestamp=timestamp,**kw)
def xi():return event('Starting XI',tactics={'lineup':[{'player':{'id':5503}}]})
def test_period_clock_excludes_stoppage():
    assert clock(event('Pass',1,'00:47:00'))==45
    assert clock(event('Pass',2,'00:15:30'))==60.5
    assert clock(event('Shot',5)) is None

def test_sub_minutes_and_red_card():
    sub=event('Substitution',2,'00:15:00',player={'id':1},substitution={'replacement':{'id':5503}})
    end=event('Half End',2,'00:49:00')
    assert exposure([sub,end],5503)==30
    red=event('Bad Behaviour',2,'00:20:00',player={'id':5503},bad_behaviour={'card':{'name':'Red Card'}})
    assert exposure([xi(),red,end],5503)==65

def test_no_appearance_is_not_zero_minutes():
    assert exposure([event('Half End',2)],5503) is None

def test_rate_is_ratio_of_sums():
    d=pd.DataFrame([dict(player_id=5503,player_name='Messi',scope='club',team='Barcelona',competition='La Liga',season='2010',date='2010-01-01',match_id=i,age=23,minutes=minute,goals=g,assists=0,shots=g,xg=.5,key_passes=0,passes=1,completed_passes=1,dribbles=0,successful_dribbles=0) for i,minute,g in [(1,90,1),(2,10,1)]])
    s=aggregate(d)
    assert s.iloc[0].goals_p90==pytest.approx(1.8)

def test_assistant_rejects_unknown_metric():
    with pytest.raises(ValueError):answer_tool(pd.DataFrame(),metric='DROP TABLE')

def test_score_weights_validation():
    with pytest.raises(ValueError):impact_score(pd.DataFrame(),{'goals_p90':-1})

def test_on_off_zero_denominator():
    d=pd.DataFrame([dict(scope='club',team='Barcelona',team_on_minutes=90,team_off_minutes=0,team_on_goals=2,team_off_goals=0,team_on_xg=1.2,team_off_xg=0)])
    out=on_off(d)
    assert pd.isna(out.iloc[0].goals_off_p90)

def test_shootout_excluded_and_shot_units():
    m={'match_id':1,'match_date':'2022-12-18','season':{'season_name':'2022'},'competition':{'competition_name':'World Cup'},'home_team':{'home_team_id':1,'home_team_name':'Argentina'},'away_team':{'away_team_id':2,'away_team_name':'France'},'home_score':3,'away_score':3}
    shot=event('Shot',1,'00:20:00',player={'id':5503,'name':'Messi'},team={'id':1},minute=20,id='s1',location=[108,40],shot={'outcome':{'name':'Goal'},'statsbomb_xg':.5})
    pen=dict(shot,period=5,id='s2')
    row,shots=extract(m,[xi(),shot,pen,event('Half End',4,'00:18:00')],5503,'1987-06-24')
    assert row['goals']==1 and row['minutes']==120 and shots[0]['distance_m']==pytest.approx(10.5)
