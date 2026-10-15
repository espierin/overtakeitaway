import subprocess


def test_driver_period_uses_dataset_bounds_legacy_links_and_inclusive_years():
    script = r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),window={};
vm.runInNewContext(fs.readFileSync('src/f1_analysis/driver-period.js','utf8'),{window});
const period=window.driverPeriod,data={races:[{year:2007},{year:2015},{year:2026}]};
let state={year:0};period.normalize(data,state);assert.equal(state.yearMin,2007);assert.equal(state.yearMax,2026);
state={year:2019};period.normalize(data,state);assert.equal(state.yearMin,2019);assert.equal(state.yearMax,2019);
state={yearMin:2024,yearMax:2015};period.normalize(data,state);assert.equal(state.yearMin,2015);assert.equal(state.yearMax,2024);assert.equal(state.year,0);
for(const year of [2015,2019,2024])assert.ok(period.matches({year},state));
for(const year of [2014,2025])assert.equal(period.matches({year},state),false);
assert.equal(period.matches(undefined,state),false);
state={yearMin:1950,yearMax:2040};period.normalize(data,state);assert.equal(state.yearMin,2007);assert.equal(state.yearMax,2026);
// Extending the dataset automatically extends the available range.
data.races.push({year:2027});state={};period.normalize(data,state);assert.equal(state.yearMax,2027);
'''
    subprocess.run(['node', '-e', script], check=True, timeout=15)
