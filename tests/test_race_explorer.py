from f1_analysis.race_explorer import explorer_data

def test_relative_sector_speed_and_yellow_windows():
    data={'laps':[{'driver_number':1,'lap_number':1,'date_start':'2020-01-01T00:00:00Z','lap_duration':60,'duration_sector_1':10},{'driver_number':2,'lap_number':1,'date_start':'2020-01-01T00:00:00Z','lap_duration':60,'duration_sector_1':20}], 'race_control':[{'date':'2020-01-01T00:00:10Z','flag':'YELLOW','scope':'Sector','sector':12},{'date':'2020-01-01T00:00:20Z','flag':'CLEAR','scope':'Sector','sector':12}],'pit':[{'driver_number':1,'lap_number':1}]}
    d=explorer_data(data)
    assert [r['relative_speed'] for r in d['sectors']]==[50,-25]
    assert len(d['yellow'])==2
    assert d['yellow'][0]['track_sectors']==[12]
    assert d['resolution']=='sector'
    assert d['pit'][0]['lap']==1
