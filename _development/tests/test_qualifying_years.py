from pathlib import Path
import json
import subprocess
import pytest
from qualifying import pole_references

ROOT=Path(__file__).resolve().parents[2]
NODE='/home/ericsp/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'


def row(driver='pole',position='1',**fields):
    return {'year':'2025','round':'1','positionNumber':position,'driverId':driver,**fields}


def test_pole_uses_deciding_phase_even_when_q2_was_faster():
    refs=pole_references([row(q1Millis='72000',q2Millis='70000',q3Millis='75000'),
                          row('peer','2',q2Millis='70500',q3Millis='75500')])
    assert refs['2025-1']==['q3Millis',75000,'pole']


def test_no_substitution_of_pole_drivers_earlier_segment_when_final_time_is_missing():
    assert pole_references([row(q2Millis='70000'),row('peer','2',q3Millis='75500')])=={}


def test_cancelled_final_phase_and_historic_aggregate_keep_their_recorded_format():
    assert pole_references([row(q2Millis='70000'),row('peer','2',q2Millis='70500')])['2025-1'][0]=='q2Millis'
    assert pole_references([row(timeMillis='180000')])['2025-1']==['timeMillis',180000,'pole']


@pytest.mark.parametrize('rows',[
    [row(q3Millis='0')], [row(q3Millis='-1')], [row(q3Millis='70000'),row('duplicate',q3Millis='70001')]
])
def test_missing_or_ambiguous_pole_is_not_a_zero_gap(rows):
    assert pole_references(rows)=={}


def test_built_reference_uses_qualifying_position_one_not_the_race_grid():
    facts=json.loads((ROOT/'_development/data/facts.js').read_text().split('=',1)[1].rstrip(';\n'))
    # 2021 British GP: Friday qualifying was led by Hamilton, sprint by Verstappen.
    assert facts['qualifying_poles']['2021-10'][2]=='lewis-hamilton'
    assert facts['qualifying_poles']['2025-1']==['q3Millis',75096,'lando-norris']


def test_frontend_summary_keeps_pole_zero_missing_phases_empty_and_both_scales_ordered():
    script=r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync('_development/assets/qualifying-years.js','utf8'),ctx);const Q=ctx.window.qualifyingYears;
const records=[
 {race:'a',year:2020,qualifying:1,qualifying_ms:{q3Millis:70000}},
 {race:'b',year:2020,qualifying:3,qualifying_ms:{q3Millis:70385}},
 {race:'c',year:2020,qualifying:15,qualifying_ms:{q2Millis:71000}},
 {race:'d',year:2022,qualifying:5,qualifying_ms:{timeMillis:90500}},
 {race:'e',year:2022,qualifying:6,qualifying_ms:{q3Millis:69000}},
 {race:'f',year:2022,qualifying:7,qualifying_ms:{q3Millis:72000}}];
const refs={a:['q3Millis',70000,'pole'],b:['q3Millis',70000,'pole'],c:['q3Millis',70000,'pole'],d:['timeMillis',90000,'pole'],e:['q3Millis',70000,'pole']};
const s=Q.summarize(records,refs,{yearMin:2020,yearMax:2022});assert.equal(s.positions,6);assert.equal(s.times,3);assert.equal(s.groups[0].gaps[0].value,0);assert.equal(s.groups[0].gaps[1].value,.385);assert.equal(s.groups[1].year,2021);assert.equal(s.groups[1].positions.length,0);assert.equal(s.groups[2].gaps[0].value,.5);
assert.equal(s.excluded.phase_missing,1);assert.equal(s.excluded.incompatible_time,1);assert.equal(s.excluded.pole_missing,1);
const filtered=Q.summarize(records,refs,{yearMin:2022,yearMax:2022});assert.equal(filtered.positions,3);assert.equal(filtered.times,1);
const anchors=Q.positionAnchors(22);assert.ok(anchors.every(Number.isInteger));for(let v=2;v<=22;v++)assert.ok(Q.positionScale(v,anchors)>Q.positionScale(v-1,anchors));assert.ok(Q.positionScale(2,anchors)-Q.positionScale(1,anchors)>Q.positionScale(20,anchors)-Q.positionScale(19,anchors));
assert.equal(Q.timeScale(0,4),0);assert.equal(Q.timeScale(4,4),1);assert.ok(Q.timeScale(.1,4)>0);assert.ok(Q.timeScale(1,4)>.25);
assert.equal(Q.quantile([1,2,3,4],.5),2.5);assert.equal(Q.quantile([1,2,3,4],.25),1.75);assert.equal(Q.density([0,0,0,0,0],{min:0,max:1}),null);
const dense=Q.density([0,.1,.2,.3,.4,.5],{min:0,max:1,floor:.003});assert.ok(dense.every(([v,d])=>v>=0&&v<=1&&Number.isFinite(d)));
const html=Q.render({records,poles:refs,races:[],lang:'en'});assert.equal((html.match(/class="qualifying-shared-scroll"/g)||[]).length,1);assert.equal((html.match(/class="starter-plot qualifying-year-plot"/g)||[]).length,2);assert.ok(!html.includes('NaN'));assert.ok(!html.includes('undefined'));
const large=Array.from({length:5},(_,i)=>({race:'large-'+i,year:2021,qualifying:i+2,qualifying_ms:{q3Millis:78000+i*1000}})),largePoles=Object.fromEntries(large.map(r=>[r.race,['q3Millis',70000,'pole']]));
const original=JSON.stringify(large),capSummary=Q.summarize(large,largePoles),capHtml=Q.render({records:large,poles:largePoles,races:[],lang:'en'});
assert.deepEqual(Array.from(capSummary.groups[0].gaps,p=>p.value),[8,9,10,11,12]);assert.equal(JSON.stringify(large),original);
const clipped=[...capHtml.matchAll(/<path[^>]*data-capped="true"[^>]*data-plot-y="([^"]+)"/g)];assert.equal(clipped.length,5);assert.ok(clipped.every(m=>+m[1]===312));assert.ok(capHtml.includes('data-median="10"'));assert.ok(!capHtml.includes('starter-direction'));assert.ok(!capHtml.includes('NaN'));
console.log('summary, true zero, missing phase, historic aggregate, year gaps, integer nonlinear axis, log1p axis, quartiles and one shared scrollbar: passed');
"""
    result=subprocess.run([NODE,'-e',script],cwd=ROOT,text=True,capture_output=True)
    assert result.returncode==0,result.stderr


def test_knockout_cutoffs_respect_fields_and_elimination_formats():
    from qualifying import stage_references
    def field(n):
        return [row(str(i),str(i),q1Millis='70000',
                    q2Millis='70000' if i<=17 else '',
                    q3Millis='70000' if i<=10 else '') for i in range(1,n+1)]
    race={'year':'2025','round':'1','qualifyingFormat':'KNOCKOUT'}
    assert stage_references(field(24),[race])['2025-1']==[10,17,24]
    twenty=field(20)
    for r in twenty:
        if int(r['positionNumber'])>15:r['q2Millis']=''
    assert stage_references(twenty,[race])['2025-1']==[10,15,20]
    assert stage_references(twenty,[{**race,'qualifyingFormat':'ONE_LAP'}])=={}
    # A missing P10 time does not reduce Q3 to nine participants.
    twenty[9]['q3Millis']=''
    assert stage_references(twenty,[race])['2025-1'][0]==10
    assert stage_references([r for r in twenty if r['driverId']!='20'],[race])=={}
    early=field(22)
    for r in early:
        if int(r['positionNumber'])>15:r['q2Millis']=''
        if int(r['positionNumber'])>8:r['q3Millis']=''
    assert stage_references(early,[{**race,'qualifyingFormat':'ELIMINATION'}])['2025-1']==[8,15,22]
    for r in twenty:r['q3Millis']=''
    assert stage_references(twenty,[race])=={}


def test_median_trend_bootstrap_and_stage_backdrops():
    script=r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync('_development/assets/qualifying-years.js','utf8'),ctx);const Q=ctx.window.qualifyingYears;
const group=(year,n,base)=>({year,positions:Array.from({length:n},(_,i)=>({value:base+(i%3),record:{year,race:year+'-'+i}})),gaps:[]});
const groups=[group(2020,15,4),group(2021,15,5),group(2022,0,8),group(2023,15,6),group(2024,15,7)];
const before=JSON.stringify(groups),model=Q.trend(groups,'positions');assert.equal(model.length,2);assert.equal(JSON.stringify(model.map(r=>[r[0].year,r.at(-1).year])),JSON.stringify([[2019.6,2021.4],[2022.6,2024.4]]));assert.equal(JSON.stringify(groups),before);assert.equal(Q.trend(groups,'positions'),model);
assert.ok(model.flat().every(p=>[p.year,p.value,p.lo,p.hi].every(Number.isFinite)&&p.lo<=p.hi&&p.lo>=1));
const constant=[group(2020,10,1),group(2021,10,1)];constant.forEach(g=>g.positions.forEach(o=>o.value=1));assert.ok(Q.trend(constant,'positions').flat().every(p=>Math.abs(p.value-1)<1e-10&&Math.abs(p.lo-1)<1e-10&&Math.abs(p.hi-1)<1e-10));
assert.equal(Q.trend([group(2020,1,3),group(2021,3,2)],'positions').length,1);assert.ok(Q.trend([group(2020,1,3)],'positions')[0].every(p=>p.lo===null&&p.hi===null&&p.value===3));
const records=groups.flatMap(g=>g.positions.map(o=>({...o.record,qualifying:o.value}))),stages=Object.fromEntries(records.map(r=>[r.race,[10,15,20]])),html=Q.render({records,stages});
assert.ok((html.match(/class="qualifying-trend"/g)||[]).length>=2);assert.ok(html.includes('qualifying-year-gap'));assert.equal((html.match(/class="qualifying-confidence"/g)||[]).length,2);assert.ok(html.includes('data-stage="q1"'));assert.ok(html.includes('data-stage="q2"'));assert.ok(html.includes('data-stage="q3"'));assert.ok(!html.includes('NaN'));
const gapPlot=html.split('data-kind="gap" width=')[1];assert.ok(!gapPlot.includes('qualifying-stage-shadow'));
console.log('bootstrap support, determinism, no mutation, constant trend, stage shading and no time-plot shading: passed');
"""
    result=subprocess.run([NODE,'-e',script],cwd=ROOT,text=True,capture_output=True)
    assert result.returncode==0,result.stderr


def bridge_rows(n=7):
    return [row('driver-'+str(i),str(i),q1Millis=str(72000+100*i),
                q2Millis=str(71000+100*i),q3Millis=str(70000+100*i)) for i in range(1,n+1)]


def test_bridge_medians_resist_one_outlier_and_require_five_drivers():
    from qualifying import bridge_step
    rows=bridge_rows()
    assert bridge_step(rows,'q2Millis','q3Millis')==[7,-1000,-1000,-1000]
    rows[-1]['q3Millis']='190000'
    assert bridge_step(rows,'q2Millis','q3Millis')[1]==-1000
    assert bridge_step(rows[:4],'q2Millis','q3Millis') is None
    rows[0]['positionNumber']=''
    assert bridge_step(rows[:5],'q2Millis','q3Millis') is None


def test_hidden_driver_q3_and_q2_never_leak_into_q1_validation():
    from qualifying import qualifying_bridges
    import copy
    rows=bridge_rows()
    poles=pole_references(rows)
    _,validation,checks=qualifying_bridges(rows,poles)
    base=next(r for r in checks if r['driver']=='driver-7' and r['origin']=='Q1')
    assert base['error_ms']==0
    altered=copy.deepcopy(rows)
    altered[-1]['q2Millis']='96000'
    altered[-1]['q3Millis']='97000'
    _,_,new_checks=qualifying_bridges(altered,poles)
    holdout=next(r for r in new_checks if r['driver']=='driver-7' and r['origin']=='Q1')
    assert holdout['estimated_gap_ms']==base['estimated_gap_ms']
    assert holdout['actual_gap_ms']!=base['actual_gap_ms']
    assert holdout['bridge_counts']==[6,6]
    assert validation['summary']['Q1']['n']==7
    assert validation['summary']['Q1']['mae_ms']==0
    assert validation['summary']['Q1']['uncorrected_mae_ms']==2000
    assert validation['summary']['Q2']['uncorrected_mae_ms']==1000


def test_built_bridge_validation_is_reproducible_from_retained_predictions():
    audit=json.loads((ROOT/'storage/qualifying-bridges-20261018/validation.json').read_text())
    facts=json.loads((ROOT/'_development/data/facts.js').read_text().split('=',1)[1].rstrip(';\n'))
    assert facts['qualifying_bridge_validation']==audit['validation']
    for origin in ['Q1','Q2']:
        records=[r for r in audit['predictions'] if r['origin']==origin]
        result=audit['validation']['summary'][origin]
        assert len(records)==result['n']
        assert result['races']==len({r['race'] for r in records})
        assert result['mae_ms']==round(sum(abs(r['error_ms']) for r in records)/len(records),3)
        assert result['mae_ms']<result['uncorrected_mae_ms']
        assert all(n>=5 for r in records for n in r['bridge_counts'])


def test_estimated_points_keep_provenance_and_enter_pooled_statistics():
    script=r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');const ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync('_development/assets/qualifying-years.js','utf8'),ctx);const Q=ctx.window.qualifyingYears;
const poles={a:['q3Millis',70000,'pole']},model={a:[[12,-500,-600,-400],[9,-1000,-1200,-800]]};
const q2={race:'a',year:2025,qualifying:12,qualifying_ms:{q2Millis:73000}},q1={race:'a',year:2025,qualifying:18,qualifying_ms:{q1Millis:76000}};
let r=Q.gap(q2,poles,model);assert.equal(r.value,2);assert.equal(r.estimated,true);assert.equal(r.source_ms,73000);assert.equal(r.estimated_ms,72000);assert.equal(r.steps[0].drivers,9);
r=Q.gap(q1,poles,model);assert.equal(r.value,4.5);assert.equal(r.steps.length,2);
assert.equal(Q.gap(q2,poles).value,null);assert.equal(Q.gap(q1,poles,{a:[null,model.a[1]]}).value,null);assert.equal(Q.gap(q2,poles,{a:[null,[4,-1000]]}).reason,'bridge_missing');
const recorded={...q2,qualifying_ms:{q3Millis:73500,q2Millis:74000}};r=Q.gap(recorded,poles,model);assert.equal(r.value,3.5);assert.equal(r.estimated,false);
assert.equal(Q.gap({...recorded,qualifying_ms:{q3Millis:69000,q2Millis:74000}},poles,model).reason,'incompatible_time');
const actual=Array.from({length:6},(_,i)=>({race:'actual-'+i,year:2025,qualifying:i+1,qualifying_ms:{q3Millis:70000+i*100}})),refs={...poles,...Object.fromEntries(actual.map(x=>[x.race,['q3Millis',70000,'pole']]))};
const input=JSON.stringify([...actual,q1]),base=Q.summarize(actual,refs),mixed=Q.summarize([...actual,q1],refs,{},model);assert.equal(mixed.measured,6);assert.equal(mixed.estimated,1);assert.equal(mixed.times,7);assert.notEqual(Q.trend(base.groups,'gaps'),Q.trend(mixed.groups,'gaps'));assert.ok(Q.trend(mixed.groups,'gaps')[0][0].value>Q.trend(base.groups,'gaps')[0][0].value);assert.equal(Q.quantile(mixed.groups[0].gaps.map(p=>p.value),.5),.3);
const html=Q.render({records:[...actual,q1],poles:refs,bridges:model,lang:'en'});assert.ok(html.includes('data-estimated="true"'));assert.ok(html.includes('data-symbol="chevron-down"'));assert.ok(html.includes('data-value="4.5"'));assert.ok(html.includes('data-plot-y="312"'));assert.ok(html.includes('data-median="0.3"'));assert.equal(JSON.stringify([...actual,q1]),input);
const negative=Q.render({records:[{...q2,qualifying_ms:{q2Millis:70500}}],poles,bridges:model});assert.ok(negative.includes('data-capped-lower="true"'));assert.ok(negative.includes('data-value="-0.5"'));assert.ok(negative.includes('data-symbol="chevron-up"'));assert.ok(!negative.includes('NaN'));
console.log('bridge provenance, missing support, measured priority, signed raw estimates, edge chevrons and pooled distributions include estimates: passed');
"""
    result=subprocess.run([NODE,'-e',script],cwd=ROOT,text=True,capture_output=True)
    assert result.returncode==0,result.stderr


def test_qualifying_chronological_curves_preserve_values_and_show_single_years():
    script=r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');const ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync('_development/assets/qualifying-years.js','utf8'),ctx);const Q=ctx.window.qualifyingYears;
const grid=Array.from({length:25},(_,i)=>2020+i/12),values=Q.cubicValues([2020,2021,2022],[1,8,2],grid);assert.equal(values[0],1);assert.equal(values[12],8);assert.equal(values[24],2);assert.ok(values.slice(0,13).every(v=>v>=1&&v<=8));assert.ok(values.slice(12).every(v=>v>=2&&v<=8));
const groups=[{year:2020,positions:[{value:3}],gaps:[]},{year:2021,positions:[{value:9},{value:11}],gaps:[]}],m=Q.trend(groups,'positions')[0];assert.ok(m.every(p=>p.value>=3&&p.value<=11));assert.ok(m[0].value<m.at(-1).value);assert.ok(m.every(p=>p.sparse));assert.equal(m[0].lo,null);
const records=[{race:'2020-a',year:2020,qualifying:3,qualifying_ms:{timeMillis:70300}}],html=Q.render({records,poles:{'2020-a':['timeMillis',70000,'pole']}});assert.equal((html.match(/class="qualifying-trend"/g)||[]).length,2);assert.ok(!html.includes('class="qualifying-confidence"'));assert.ok(!html.includes('NaN'));
console.log('shape-preserving median curves, bounded interpolation and single-observation lines: passed');
"""
    result=subprocess.run([NODE,'-e',script],cwd=ROOT,text=True,capture_output=True)
    assert result.returncode==0,result.stderr


def test_gaussian_trend_uses_race_order_while_year_distributions_stay_identical():
    script=r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');const ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync('_development/assets/qualifying-years.js','utf8'),ctx);const Q=ctx.window.qualifyingYears;
const make=reverse=>[{year:2020,positions:Array.from({length:20},(_,i)=>({record:{race:'2020-'+(i+1)},value:reverse?20-i:i+1})),gaps:[]}];
const ascending=make(false),descending=make(true),before=JSON.stringify(ascending),up=Q.trend(ascending,'positions')[0],down=Q.trend(descending,'positions')[0];
assert.equal(Q.quantile(ascending[0].positions.map(o=>o.value),.5),Q.quantile(descending[0].positions.map(o=>o.value),.5));assert.ok(up[0].value<up.at(-1).value);assert.ok(down[0].value>down.at(-1).value);assert.ok(up.every(p=>p.value>=1&&p.value<=20&&p.sigma===5));assert.equal(JSON.stringify(ascending),before);
const reverseInput=[{...ascending[0],positions:[...ascending[0].positions].reverse()}],again=Q.trend(reverseInput,'positions')[0];assert.equal(JSON.stringify(up),JSON.stringify(again));
console.log('Chronological smoothing responds to order, preserves distribution and does not depend on input array order: passed');
"""
    result=subprocess.run([NODE,'-e',script],cwd=ROOT,text=True,capture_output=True)
    assert result.returncode==0,result.stderr


def test_isolated_slow_qualifying_does_not_create_a_winter_trough():
    script=r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync('_development/assets/qualifying-years.js','utf8'),ctx);const Q=ctx.window.qualifyingYears;
const groups=[2021,2022,2023].map(year=>({year,positions:[],gaps:Array.from({length:22},(_,i)=>({record:{race:year+'-'+(i+1),date:year+'-'+String(i+1).padStart(2,'0')},value:.2}))}));
groups[2].gaps[3].value=18;const before=JSON.stringify(groups),fit=Q.trend(groups,'gaps').flat(),winter=fit.filter(p=>p.year>2022.3&&p.year<2022.7);assert.ok(winter.length>0);assert.ok(winter.every(p=>p.value<.4));assert.equal(JSON.stringify(groups),before);assert.equal(groups[2].gaps[3].value,18);
const sustained=groups.map(g=>({...g,gaps:g.gaps.map(p=>({...p,value:g.year===2023?2:.2}))}));assert.ok(Q.trend(sustained,'gaps').flat().at(-1).value>1.8);
console.log('Robust chronological curve limits isolated outlier influence, preserves real points and retains sustained changes');
"""
    result=subprocess.run([NODE,'-e',script],cwd=ROOT,text=True,capture_output=True)
    assert result.returncode==0,result.stderr


def test_smooth_qualifying_curve_has_gradual_season_transitions():
    script=r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync('_development/assets/qualifying-years.js','utf8'),ctx);const Q=ctx.window.qualifyingYears;
// A genuine improvement with noisy race results must remain visible without a
// sharp winter step or kinks from changes in the robust local weighting.
const groups=[2020,2021,2022].map(year=>({year,positions:Array.from({length:20},(_,i)=>({record:{race:year+'-'+(i+1)},value:year===2020?10:i%7<3?2:4})),gaps:[]}));
const original=JSON.stringify(groups),curve=Q.trend(groups,'positions')[0];
assert.ok(curve[0].value>9);assert.ok(curve.at(-1).value<4);assert.ok(curve.every(p=>p.value>=2&&p.value<=10));
const bends=curve.slice(2).map((p,i)=>Math.abs(p.value-2*curve[i+1].value+curve[i].value));assert.ok(Math.max(...bends)<.05);
assert.ok(curve.every(p=>Number.isFinite(p.lo)&&Number.isFinite(p.hi)&&p.lo<=p.hi));assert.equal(JSON.stringify(groups),original);
console.log('Gradual qualifying season transitions, sustained improvement, valid bootstrap bands and unchanged observations');
"""
    result=subprocess.run([NODE,'-e',script],cwd=ROOT,text=True,capture_output=True)
    assert result.returncode==0,result.stderr
