"""Validate retained originals, unchanged measurements and rebuilt exports."""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib, html, json, re
from f1_analysis.io import read_json, write_json, utcnow
from f1_analysis.publication import digest
from f1_analysis.render import page
from f1_analysis.branding import language_controls, language_script

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / 'analyses/sources/historical'


def originals():
    checked = Counter(); failures = []
    for path in STORE.rglob('*.json'):
        if not re.fullmatch(r'[a-f0-9]{64}',path.stem): continue
        meta = read_json(path)
        if not meta.get('file') or not meta.get('sha256'): continue
        body = path.parent / meta['file']
        if not body.is_file() or digest(body) != meta['sha256']:
            failures.append(str(path.relative_to(ROOT)))
        else: checked[path.relative_to(STORE).parts[0]] += 1
    for sub, name, expected in [('f1db','1c5c07d064e2988cb31a44206cc679662e0523a9bde0c191eed8ffc22831eec6.zip','1c5c07d064e2988cb31a44206cc679662e0523a9bde0c191eed8ffc22831eec6'),
                                ('statsf1-compilation','sessionresults.zip','27b0e561ecd7e9466e390abcb66dd03160629e7481edfd9ad2cddcea87b07fc3')]:
        if digest(STORE/sub/name) != expected: failures.append(sub+'/'+name)
        else: checked[sub] += 1
    write_json(STORE/'original-integrity.json',{'checked_at':utcnow(),'checked':dict(checked),'failures':failures})
    if failures: raise ValueError('Original source integrity failure: '+repr(failures[:10]))
    return checked


def check_races():
    counts = Counter()
    for pointer in sorted((ROOT/'analyses').glob('*/*/latest.json')):
        if int(pointer.parent.parent.name)>2019:continue
        run = pointer.parent/read_json(pointer)['run']
        baseline = read_json(run/'data/raw/historical/baseline.json'); data = read_json(run/'data/normalized/archive.json')
        by_id = {d['id']:d for d in data['drivers']}
        for d in baseline['drivers']:
            current = by_id[d['id']]
            for field in ('position','grid','completed_laps','points','classified','name','number','team','team_id','driver_id','status','time'):
                if d.get(field) is not None and current.get(field)!=d[field]: raise ValueError(f'Original result changed: {run} {d["id"]} {field}')
            laps = {l['lap']:l for l in current['laps']}
            if len(laps)!=len(current['laps']):raise ValueError('Duplicate driver/lap observation')
            for row in d['laps']:
                for field in ('position','seconds','deleted'):
                    if row.get(field) is not None and laps[row['lap']].get(field)!=row[field]: raise ValueError('Original lap changed')
                counts['original_lap_observations'] += 1
            pits = {p['stop']:p for p in current['pitstops']}
            for row in d['pitstops']:
                for field in ('lap','duration','local_time'):
                    if row.get(field) is not None and pits[row['stop']].get(field)!=row[field]: raise ValueError('Original pit changed')
            counts['original_driver_entries'] += 1
        manifest = read_json(run/'manifest.json')
        for name, expected in manifest['file_hashes'].items():
            if digest(run/name)!=expected: raise ValueError('Run checksum differs: '+str(run/name))
            counts['verified_run_files'] += 1
        counts['races'] += 1
    write_json(STORE/'preservation-audit.json',{'checked_at':utcnow(),**dict(counts)})
    print('preservation',dict(counts),flush=True)


def report(checked):
    audit = read_json(STORE/'coverage-audit.json'); years = defaultdict(Counter)
    for r in audit['coverage']:
        totals = years[r['year']]; totals['races']+=1
        for key in ('known_lap_positions','measured_lap_times','pit_records','best_sectors','maximum_speeds','tyre_changes'):
            totals[key]+=r.get(key,0)
        totals['qualifying']+=r['sessions'].get('qualifying-results',0)
    def pair(nl,en,tag='p'):
        return '<'+tag+' class="history-nl">'+html.escape(nl)+'</'+tag+'><'+tag+' class="history-en">'+html.escape(en)+'</'+tag+'>'
    body = '<style>html[lang="nl"] .history-en,html[lang="en"] .history-nl{display:none}main{max-width:1300px;margin:auto;padding:28px}table{width:100%}td,th{padding:8px;text-align:right;border-bottom:1px solid #344254}.table-scroll{overflow:auto}th{white-space:nowrap}</style>'+language_controls()+'<main>'
    body += pair('Historisch data-archief · 1950–2019','Historical data archive · 1950–2019','h1')
    added = audit['added']; color = audit['team_color_coverage']; verified = sum(r['verified_entries'] for r in color); unknown = sum(r['unknown_entries'] for r in color)
    body += pair(f"{audit['races']:,} races gecontroleerd. Toegevoegd: {added['lap_positions']:,} rondeposities, {added['lap_times']+added['additional_lap_times']:,} rondetijdmetingen en {added['pitstops']:,} pitregistraties. Gedateerde kleuren: {verified:,} van {verified+unknown:,} bronentries ({verified/(verified+unknown):.1%}).",f"{audit['races']:,} races checked. Added: {added['lap_positions']:,} lap positions, {added['lap_times']+added['additional_lap_times']:,} lap-time observations and {added['pitstops']:,} pit records. Dated colour references: {verified:,} of {verified+unknown:,} source entries ({verified/(verified+unknown):.1%}).")
    body += pair('Dit overzicht telt vastgelegde brongegevens, geen geschatte volledigheid. Een lege waarde betekent onbekend. Kwalificatie- en snelste-ronderecords verschillen in dekking per tijdperk.','This report counts retained source observations, not estimated completeness. An empty value means unknown. Qualifying and fastest-lap coverage varies by era.')
    body += pair('Alle oorspronkelijke uitslagen en metingen blijven behouden. Gedeelde auto’s zonder bevestigde rijderwisseltijd worden niet toegewezen aan een veronderstelde rijder. Rondeposities zijn geen inhaalfeed; persoonlijke beste sectoren zijn geen sectortijden per ronde. Historische privé-inschrijvingen en chassismerken hebben niet altijd één uniforme teamkleur.','All original results and measurements are retained. Shared cars without confirmed driver handover timing are not assigned to an assumed driver. Lap positions are not an overtaking feed; personal best sectors are not per-lap sectors. Historical private entrants and chassis brands do not always have one uniform team colour.')
    archived = read_json(STORE/'wayback/inventory.json') if (STORE/'wayback/inventory.json').exists() else {'documents':[]}
    snapshots = sum(d.get('file','').endswith('.pdf') for d in archived['documents'])
    body += pair(f"Oorspronkelijke bronbestanden zijn met SHA-256 gecontroleerd, inclusief {snapshots} FIA-PDF’s teruggevonden via de Wayback Machine. Opnamedatum en oorspronkelijke URL blijven bij iedere archiefkopie bewaard.",f"Original source files are verified with SHA-256, including {snapshots} FIA PDFs recovered through the Wayback Machine. Each archived copy retains its capture timestamp and original URL.")
    headers = [('Jaar','Year'),('Races','Races'),('Kwalificatie','Qualifying'),('Rondeposities','Lap positions'),('Rondetijden','Lap times'),('Pitregistraties','Pit records'),('Beste sectoren','Best sectors'),('Snelheidsmetingen','Speed observations')]
    body += '<div class="table-scroll"><table><thead><tr>'+''.join('<th>'+pair(nl,en,'span')+'</th>' for nl,en in headers)+'</tr></thead><tbody>'
    keys = ['races','qualifying','known_lap_positions','measured_lap_times','pit_records','best_sectors','maximum_speeds']
    for year, totals in sorted(years.items(),reverse=True):
        body += '<tr><td>'+str(year)+'</td>'+''.join('<td>'+format(totals[key],',')+'</td>' for key in keys)+'</tr>'
    body += '</tbody></table></div>'
    body += pair('Aanvullende bewaarde bronnen: vrije trainingen, warm-up, prekwalificatie, kampioenschapsstanden, motoren/chassis/bandenleveranciers, weers- en wedstrijdleidingsberichten. Telemetrie, bandensets en gelokaliseerde inhaalacties blijven onbekend wanneer de bron ze niet bevat.','Additional retained sources include practice, warm-up, pre-qualifying, championship standings, engines/chassis/tyre suppliers, weather and race-control messages. Telemetry, tyre sets and located overtaking events remain unknown when absent from the source.')
    body += '<p><a href="coverage-audit.json">JSON</a> · <a href="original-integrity.json">SHA-256</a> · <a href="preservation-audit.json">'+pair('Controle oorspronkelijke metingen','Original measurement checks','span')+'</a></p>'
    body += '<p><a href="https://github.com/f1db/f1db/releases/tag/v2026.17.0">F1DB · CC BY 4.0</a> · <a href="https://github.com/mclarenmp4-22/f1resultsdatabase/releases/tag/v2.10.1%2B20260921">f1resultsdatabase · ODbL 1.0</a> · <a href="https://www.fia.com">FIA</a> · <a href="https://press.pirelli.com">Pirelli</a> · <a href="https://web.archive.org">Internet Archive</a></p></main>'
    (STORE/'coverage-report.html').write_text(page('Overtake It Away · Historical archive',body+language_script()))


if __name__ == '__main__':
    checked = originals(); check_races(); report(checked)
    print('originals',dict(checked),flush=True)
