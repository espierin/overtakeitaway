from f1_analysis.race_explorer import explorer_data

def test_relative_sector_speed_and_yellow_windows():
    data={'laps':[{'driver_number':1,'lap_number':1,'date_start':'2020-01-01T00:00:00Z','lap_duration':60,'duration_sector_1':10},{'driver_number':2,'lap_number':1,'date_start':'2020-01-01T00:00:00Z','lap_duration':60,'duration_sector_1':20}], 'race_control':[{'date':'2020-01-01T00:00:10Z','flag':'YELLOW','scope':'Sector','sector':12},{'date':'2020-01-01T00:00:20Z','flag':'CLEAR','scope':'Sector','sector':12}],'pit':[{'driver_number':1,'lap_number':1}]}
    d=explorer_data(data)
    assert [r['relative_speed'] for r in d['sectors']]==[50,-25]
    assert len(d['yellow'])==2
    assert d['yellow'][0]['track_sectors']==[12]
    assert d['resolution']=='sector'
    assert d['pit'][0]['lap']==1


def test_replay_keeps_pit_lane_interval_and_changes_tyres_at_exit():
    from f1_analysis.race_explorer import playback_data
    data={'laps':[{'driver_number':1,'lap_number':1,'date_start':'2020-01-01T00:00:00Z','lap_duration':60,'duration_sector_1':20,'duration_sector_2':20,'duration_sector_3':20},
                  {'driver_number':1,'lap_number':2,'date_start':'2020-01-01T00:01:00Z','lap_duration':70}],
          'pit':[{'driver_number':1,'lap_number':1,'entry_date':'2020-01-01T00:00:55Z','date':'2020-01-01T00:01:15Z','lane_duration':20}],
          'stints':[{'driver_number':1,'lap_start':1,'compound':'SOFT'}, {'driver_number':1,'lap_start':2,'compound':'MEDIUM'}]}
    replay=playback_data(data)
    assert replay['clock']==[[0,0],[1,20],[2,40],[3,60],[6,130]]
    assert replay['pit']==[{'driver':1,'lap':1,'start':55,'end':75}]
    assert [s['start'] for s in replay['tyres']]==[0,75]
    # A duration without a recorded entry cannot identify a pit interval.
    data['pit'][0].pop('entry_date')
    assert playback_data(data)['pit']==[]
