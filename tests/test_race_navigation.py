from f1_analysis.race_navigation import edition_targets,refresh_navigation
import json

def race(year,round,circuit,date):
 return {'year':year,'round':round,'circuitId':circuit,'date':date,'href':f'analyses/{year}/{circuit}-{round}/runs/test/overzicht.html','name':circuit}

def test_year_navigation_skips_missing_years_and_keeps_exact_circuit():
 a=race(2019,2,'shanghai','2019-04-14');b=race(2024,5,'shanghai','2024-04-21');other=race(2020,1,'different','2020-01-01')
 targets=edition_targets([b,other,a])
 assert targets[a['href']][3]==b and targets[b['href']][2]==a
 assert targets[a['href']][2] is None and targets[b['href']][3] is None

def test_race_navigation_wraps_within_the_season():
 first=race(2024,1,'a','2024-03-01');last=race(2024,3,'b','2024-06-01');middle=race(2024,2,'a','2024-04-01')
 targets=edition_targets([last,first,middle])
 assert targets[first['href']][0]==last and targets[last['href']][1]==first
 assert targets[first['href']][1]==middle
 # Year navigation does not silently become a second same-year race.
 assert targets[first['href']][2:]==[None,None]

def test_archived_navigation_is_repaired_when_a_later_edition_arrives(tmp_path):
 a=race(2019,1,'a','2019-01-01');b=race(2024,1,'a','2024-01-01')
 (tmp_path/'race-updates.json').write_text(json.dumps({'races':[a,b]}))
 source=tmp_path/a['href']
 html='<nav class="race-navigation"><button disabled>Volgend jaar</button></nav><script data-race-navigation>keepModulePosition()</script>'
 updated=refresh_navigation(html,source,tmp_path)
 assert '2024/a-1/runs/test/overzicht.html' in updated
 assert 'keepModulePosition()' in updated
 assert updated.count('<button disabled>')==3
