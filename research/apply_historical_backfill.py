"""Apply the retained one-time research to every 1950-2019 race, offline."""
from collections import Counter
from pathlib import Path
import hashlib, html, json, re, shutil
from f1_analysis.historical_backfill import HistoricalDatabase, HistoricalChartDatabase, augment, folded, supplemental_facts, coverage_notes, write_method_report
from f1_analysis.historical_presentation import enrich_drivers
from f1_analysis.driver_sidebar import sidebar
from f1_analysis.io import read_json, write_json, write_csv, utcnow
from f1_analysis.publication import site_html, with_race_notifications

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / 'analyses/sources/historical'
PAYLOAD = re.compile(r'(<script\b[^>]*\bid=["\x27]archive-data["\x27][^>]*>)(.*?)(</script>)', re.S)

def main():
    package = ROOT / 'storage/search-data/f1db-csv.zip'
    database = HistoricalDatabase(package)
    charts = HistoricalChartDatabase(STORE / 'statsf1-compilation/database/sessionresults.db', database)
    retained = STORE / 'f1db' / (database.sha256 + '.zip'); retained.parent.mkdir(parents=True, exist_ok=True)
    if not retained.exists(): shutil.copy2(package, retained)
    if not (STORE / 'historical.sqlite').exists(): database.sqlite(STORE / 'historical.sqlite')
    release = read_json(STORE / 'f1db/release.json')
    asset = next(a for a in release['assets'] if a['name']=='f1db-csv.zip')
    if asset['digest'] != 'sha256:' + database.sha256: raise ValueError('F1DB official release checksum mismatch')
    write_json(STORE / 'f1db/source.json', {'publisher':'F1DB','release':'v2026.17.0','url':'https://github.com/f1db/f1db/releases/tag/v2026.17.0',
               'download_url':'https://github.com/f1db/f1db/releases/download/v2026.17.0/f1db-csv.zip', 'sha256':database.sha256,
               'license':'CC BY 4.0','scope':'1950-2019 races; original complete CSV release retained','retained_at':utcnow(),
               'release_published_at':release['published_at'], 'official_digest':asset['digest'], 'official_bytes':asset['size']})
    colors = read_json(ROOT / 'assets/historical-team-colors.json')
    fia = read_json(STORE / 'fia/normalized.json')['races']
    pirelli = read_json(STORE / 'pirelli/normalized.json')['races']
    report = []; unmatched = []; conflicts = []; colour_coverage = Counter(); colour_unknown = Counter(); total_added = Counter()
    for pointer in sorted((ROOT / 'analyses').glob('*/*/latest.json')):
        year = int(pointer.parent.parent.name)
        if year > 2019: continue
        run = pointer.parent / read_json(pointer)['run']
        source = run / 'overzicht.html'; text = site_html(source, ROOT); match = PAYLOAD.search(text)
        if not match: raise ValueError(f'Historical payload missing: {run}')
        old = json.loads(match[2]); raw = read_json(run / 'data/raw/race.json')
        baseline = run / 'data/raw/historical/baseline.json'
        if not baseline.exists(): write_json(baseline, read_json(run / 'data/normalized/archive.json'))
        data = read_json(baseline); supplement = database.supplement(data, raw)
        supplement['historical_chart'] = charts.supplement(data, supplement)
        key = f"{year}-{data['round']:02}"
        supplement['fia'] = fia.get(key, {'documents':[], 'best_sectors':[], 'maximum_speeds':[]})
        p = pirelli.get(key, {'sources':[], 'changes':[]}); supplement['pirelli_sources'] = p['sources']; supplement['tyre_changes'] = []
        for change in p['changes']:
            name = folded(change['driver_text']); name = 'alguersuari' if name == 'alguersari' else name
            entries = [e for e in raw['entries'] if folded(e['driver']['surname']) == name or folded(e['driver']['forename'] + e['driver']['surname']) == name]
            if len(entries) == 1:
                entry_id = entries[0]['sessionentry']['id']; career = supplement['entry_drivers'].get(entry_id)
                number = int(entries[0]['roundentry']['car_number'])
                supplement['tyre_changes'].append({**change, 'entry_id':entry_id, 'career_id':career, 'number':number})
            else: supplement.setdefault('unmatched_tyre_changes', []).append(change)
        context_file = run / 'data/normalized/historical-context.json'
        if context_file.exists():
            context = read_json(context_file)
            supplement['timing_context'] = {k:context[k] for k in ('clock','race_control','weather','track_status','session_status','sources')}
            preserved_context = STORE / 'timing-context' / (key + '.json')
            preserved_context.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(context_file,preserved_context)
        stable = STORE / 'supplements' / (key + '.json'); write_json(stable, supplement)
        out = augment(data, supplement, colors)
        if old.get('timing'):
            out['timing'] = old['timing']
            write_json(STORE / 'timing' / (key + '.json'), old['timing'])
        out = enrich_drivers(out, raw)
        for driver in out['drivers']:
            color_key = (driver['team_id'], driver['team'])
            if driver.get('color_source') or out.get('timing', {}).get('drivers', {}).get(str(driver['number']), {}).get('TeamColour'):
                colour_coverage[color_key] += 1
            else: colour_unknown[color_key] += 1
        added = out['historical_supplement']['added']; total_added.update(added)
        newfacts = supplemental_facts(out, old.get('highlights', {}))
        payload = {**old, **out, 'highlights':newfacts}
        text = text[:match.start(2)] + json.dumps(payload, ensure_ascii=False, allow_nan=False).replace('<','\\u003c') + text[match.end(2):]
        originals = {e['sessionentry']['id']:e['driver'] for e in raw['entries']}
        new_sidebar = sidebar([{**d,'color':d['display_color'],'surname':originals[d['id']]['surname']} for d in out['drivers']],all_id='all',none_id='none',archive=True)
        new_sidebar = re.search(r'<aside\b.*?</aside>',new_sidebar,re.S)[0]
        text = re.sub(r'<aside\b[^>]*class=["\x27]driver-sidebar["\x27].*?</aside>',lambda m:new_sidebar,text,count=1,flags=re.S)
        notes = coverage_notes()
        coverage = '<h2>Datadekking</h2><ul id="history-coverage-notes">' + ''.join('<li data-history-note data-nl="'+html.escape(nl,quote=True)+'" data-en="'+html.escape(en,quote=True)+'">'+html.escape(nl)+'</li>' for nl,en in notes) + '</ul>'
        text = re.sub(r'<h2>Datadekking</h2>\s*<ul[^>]*>.*?</ul>',lambda m:coverage,text,count=1,flags=re.S)
        if 'data-historical-source-link' not in text:
            link = '<p data-historical-source-link><a href="data/normalized/historical-supplement.json" data-history-note data-nl="Aanvullende brongegevens en controlelog" data-en="Additional source data and audit log">Aanvullende brongegevens en controlelog</a></p>'
            text = text.replace('</body>',link+'</body>',1)
        if 'coverage-report.html' not in text:
            audit_link = '<p><a href="../../../../../analyses/sources/historical/coverage-report.html" data-history-note data-nl="Dekking van het historische archief" data-en="Historical archive coverage">Dekking van het historische archief</a></p>'
            text = text.replace('</body>',audit_link+'</body>',1)
        text = with_race_notifications(text, source, ROOT)
        source.write_text(text)
        write_json(run / 'data/normalized/archive.json', out)
        write_json(run / 'data/normalized/historical-supplement.json', supplement)
        write_json(run / 'data/raw/historical/f1db.json', {'source':supplement['source'],'race':supplement['race'],'sessions':supplement['sessions']})
        manifest = read_json(run / 'manifest.json')
        manifest['historical_backfill'] = {'schema':1,'retained_at':utcnow(),'source':supplement['source'],'added':added,
            'sources_file':'data/normalized/historical-supplement.json', 'original_results_preserved':True}
        manifest.setdefault('coverage',{}).update(qualifying=len(supplement['sessions'].get('qualifying-results',[])),
            fastest_laps=len(supplement['sessions'].get('fastest-laps',[])), pit=out['pit_records'],laps=out['lap_records'],
            best_sectors=len(supplement['fia']['best_sectors']), tyre_changes=len(supplement['tyre_changes']))
        manifest.update(warnings=out['warnings'], coverage_label=out['coverage_label'])
        write_csv(run / 'exports/uitslag.csv', [{k:v for k,v in d.items() if k not in ('laps','pitstops')} for d in out['drivers']])
        write_csv(run / 'exports/ronden.csv', [{'entry_id':d['id'],'coureur':d['name'],'nummer':d['number'],**l} for d in out['drivers'] for l in d['laps']])
        write_csv(run / 'exports/pitstops.csv', [{'entry_id':d['id'],'coureur':d['name'],'nummer':d['number'],**p} for d in out['drivers'] for p in d['pitstops']])
        write_method_report(run, out, manifest)
        manifest['file_hashes'] = {p.relative_to(run).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(run.rglob('*')) if p.is_file() and p.name != 'manifest.json'}
        manifest['files'] = list(manifest['file_hashes'])
        write_json(run / 'manifest.json', manifest)
        unmatched.extend({'year':year,'round':out['round'],**x} for x in supplement['unmatched_entries'])
        conflicts.extend({'year':year,'round':out['round'],**x} for x in supplement['conflicts'])
        conflicts.extend({'year':year,'round':out['round'],**x} for x in supplement['historical_chart'].get('conflicts', []))
        report.append({'year':year,'round':out['round'],'race':out['name'],'path':str(source.relative_to(ROOT)), 'added':added,
                       'sessions':{k:len(v) for k,v in supplement['sessions'].items()},'fia_documents':len(supplement['fia']['documents']),
                       'best_sectors':len(supplement['fia']['best_sectors']),'tyre_changes':len(supplement['tyre_changes']),
                       'timing_context':bool(supplement.get('timing_context'))})
        report[-1]['lap_chart_records'] = len(supplement['historical_chart'].get('lap_chart', []))
        report[-1]['maximum_speeds'] = len(supplement['historical_chart'].get('maximum_speeds', []))
        report[-1].update(known_lap_positions=sum(l['position'] is not None for d in out['drivers'] for l in d['laps']),
                         measured_lap_times=sum(l['seconds'] is not None for d in out['drivers'] for l in d['laps']), pit_records=out['pit_records'])
        if len(report)%100==0: print('applied',len(report),'added',dict(total_added),flush=True)
    audit = {'created_at':utcnow(),'races':len(report),'added':dict(total_added),'coverage':report,'unmatched_entries':unmatched,'source_conflicts':conflicts,
             'team_color_coverage':[{'team_id':id_,'team':name,'verified_entries':colour_coverage[(id_,name)],'unknown_entries':colour_unknown[(id_,name)]} for id_,name in sorted(set(colour_coverage)|set(colour_unknown),key=lambda p:int(p[0]))]}
    write_json(STORE / 'coverage-audit.json', audit)
    print('complete',len(report),'added',dict(total_added),'conflicts',len(conflicts),'unmatched',len(unmatched),flush=True)

if __name__ == '__main__': main()
