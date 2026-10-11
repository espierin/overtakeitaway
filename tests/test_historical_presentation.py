from f1_analysis.historical_presentation import enrich_drivers,in_seasons

def test_season_ranges_allow_discontinuous_layout_use():
    assert in_seasons(1960,'1958,1960-1962')
    assert not in_seasons(1959,'1958,1960-1962')

def test_badges_keep_shared_number_entries_separate_and_use_season_colour():
    data={'drivers':[{'id':'a','team_id':'1','number':7,'color':None},{'id':'b','team_id':'1','number':7,'color':None}],'timing':{'drivers':{'7':{'TeamColour':'DC0000'}}}}
    raw={'entries':[{'sessionentry':{'id':'a'},'driver':{'surname':'Räikkönen','abbreviation':'RAI'}},{'sessionentry':{'id':'b'},'driver':{'surname':'Testerson','abbreviation':None}}]}
    result=enrich_drivers(data,raw)
    assert [d['id'] for d in result['drivers']]==['a','b']
    assert [d['code'] for d in result['drivers']]==['RAI','TES']
    assert all(d['display_color']=='#DC0000' for d in result['drivers'])
    assert all(d['color'] is None for d in result['drivers'])
