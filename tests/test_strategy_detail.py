from f1_analysis.strategy_detail import detail_cycles

def test_sector_points_are_measured_and_missing_sectors_not_interpolated():
    c={'early_driver':1,'late_driver':2,'trace':[{'lap':3,'gap':-2},{'lap':4,'gap':-3}]}
    laps=[{'driver_number':n,'lap_number':3,'date_start':f'2020-01-01T00:00:0{n}Z','lap_duration':60,'duration_sector_1':20,'duration_sector_2':20,'duration_sector_3':20} for n in (1,2)]
    result=detail_cycles([c],laps)[0]['detail_trace']
    assert len(result)==4
    assert [r['sector'] for r in result]==[1,2,3,3]
    assert result[0]['gap']==-1
    assert result[-1]['gap']==-3
    assert 'detail_trace' not in c
