import subprocess


def test_field_reference_uses_shared_races_compounds_and_distinct_drivers():
    script=r'''
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict'),window={lapRankings:{pointsFor:r=>r.ranks||[]}};
vm.runInNewContext(fs.readFileSync('src/f1_analysis/driver-field.js','utf8'),{window,console});
const make=(id,values)=>({id,name:id,races:values.map(([race,soft,medium])=>({race,qualities:{pitwindow:soft===null?[]:[...soft.map(value=>({value,compound:'SOFT'})),...(medium||[]).map(value=>({value,compound:'MEDIUM'}))]}}))});
const a=make('a',[['one',[1,3],[100]],['two',[5]]]),b=make('b',[['one',[4]],['two',[7]]]),c=make('c',[['one',[6]]]),missing=make('unknown',[['one',null]]),unrelated=make('unrelated',[['different',[999]]]);
const data={drivers:[a,b,c,missing,unrelated]},options={data,driver:a,rows:a.races,state:{compound:''},kind:'pitwindow'};
const result=window.driverField.compare(options),find=id=>result.entries.find(e=>e.driver.id===id);
assert.equal(find('a').n,1);assert.equal(find('a').median,-2);assert.equal(find('b').median,0);assert.equal(find('c').median,2);assert.equal(find('unknown').median,null);assert.equal(find('unknown').n,0);assert.equal(find('unrelated'),undefined);
// Each driver contributes one compound median, even when a driver has more stops.
a.races[0].qualities.pitwindow.push({value:2,compound:'SOFT'});assert.equal(window.driverField.compare(options).profile.median,-2);
options.state.compound='MEDIUM';assert.equal(window.driverField.compare(options).profile.n,0);
options.state.compound='';options.kind='metronome';a.races[0].ranks=[{rank:1},{rank:3}];b.races[0].ranks=[{rank:4}];c.races[0].ranks=[{rank:6}];a.races[1].ranks=[{rank:20}];const ranks=window.driverField.compare(options);assert.equal(ranks.profile.median,3);assert.equal(ranks.profile.n,3);assert.equal(ranks.profile.races,2);
// Old bookmarks cannot widen the fixed clean-clear-air selection.
vm.runInNewContext(fs.readFileSync('src/f1_analysis/lap-rankings.js','utf8'),{window,console});
a.races[0].lap_rankings=[[2,1,20,3,0],[3,2,20,3,128],[4,3,20,3,64],[5,4,20,3,2],[6,5,20,3,4],[7,6,20,3,16],[8,7,20,3,8],[1,8,20,3,1]];
a.races[1].lap_rankings=[[2,9,20,3,0]];
options.state.metronomelaps='all';const filtered=window.driverField.compare(options);assert.equal(filtered.profile.n,2);assert.equal(filtered.profile.median,5);assert.equal(filtered.profile.races,2);

'''
    subprocess.run(['node','-e',script],check=True,timeout=15)


def test_profile_metronome_hides_missing_rows_without_changing_measured_values():
    script = r'''
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const window={lapRankings:{pointsFor:r=>r.ranks||[]}};
vm.runInNewContext(fs.readFileSync('_development/assets/driver-field.js','utf8'),{window});
const make=(id,points)=>({id,name:id,code:id,number:1,races:[{race:'shared',ranks:points.map(rank=>({rank,lap:2}))}]});
const a=make('a',[3,1,2]),b=make('b',[5,4]),missing=make('missing',[]);
const options={data:{drivers:[missing,b,a]},driver:a,rows:a.races,state:{compound:''},lang:'nl',kind:'metronome'};
const before=window.driverField.compare(options);
const html=window.driverField.render(options);
assert.deepEqual([...html.matchAll(/data-field-driver="([^"]+)"/g)].map(m=>m[1]),['a','b']);
assert.ok(!html.includes('is-missing'));
assert.ok(html.includes('data-field-median="2" data-field-n="3"'));
assert.ok(html.includes('data-field-median="4.5" data-field-n="2"'));
assert.equal(JSON.stringify(window.driverField.compare(options)),JSON.stringify(before));
assert.equal(before.entries.length,3); // Coverage retains the missing participant.
options.rows=[];
assert.ok(window.driverField.render(options).includes('Onvoldoende gedeelde metingen'));
'''
    subprocess.run(['node', '-e', script], check=True, timeout=15)
