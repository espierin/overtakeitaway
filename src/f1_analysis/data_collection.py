"""Rebuild the bilingual collection ledger from retained data, never estimates.

Layers are deliberately separate: a source row, a dashboard value and a derived
rank may describe the same event. Their counts must not be summed as new facts.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import argparse
import gzip
import hashlib
import html
import json
import math
import re
import shutil
import sqlite3


def json_text(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).replace('</', '<\\/')


def count_parameters(value):
    """Non-null primitive values, with null/unknown separately, per schema path.

    Arrays of tuples are kept as array values; named lap-rank columns receive
    explicit names instead of being mistaken for five independent lap ranks.
    """
    out = defaultdict(Counter)
    def walk(v, path):
        if isinstance(v, dict):
            # Dictionary identifiers are records, not different parameters.
            # Keep real schema names while grouping source IDs and car numbers.
            dynamic=(path in ('styles','sources','search_drivers') or path.endswith('.sources'))
            for k, x in v.items():
                key='*' if dynamic or str(k).lstrip('-').isdigit() or re.fullmatch(r'[12]\d{3}[-/]\d{1,2}',str(k)) else k
                walk(x, path+'.'+key if path else key)
        elif isinstance(v, list):
            if path.endswith('.lap_rankings'):
                columns = ('lap', 'rank', 'field_size', 'compound', 'context_flags')
                for row in v:
                    for key, x in zip(columns, row):walk(x, path+'[].'+key)
            else:
                for x in v:walk(x, path+'[]')
        else:
            count = out[path]; count['slots'] += 1
            if v is None or v == '' or isinstance(v, float) and not math.isfinite(v):
                count['missing'] += 1
            elif isinstance(v, str) and v.upper() in ('UNKNOWN', 'N/A', 'UNAVAILABLE'):
                count['unknown'] += 1
            else:
                count['values'] += 1
                count['numeric' if isinstance(v, (int, float)) and not isinstance(v, bool) else 'boolean' if isinstance(v, bool) else 'text'] += 1
    walk(value, '')
    return {k: dict(v) for k, v in out.items()}


def _load(path):
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_text())


def snapshot(root):
    from .phase2 import extract
    from .publication import site_html
    root = Path(root).resolve()
    cache_path = root/'storage/data-collection/count-cache.json'
    cache = _load(cache_path) if cache_path.exists() else {}
    updated_cache = {}; parameters = defaultdict(Counter); years = defaultdict(Counter)
    failures = []; manifests = []; source_urls = set(); datasets = Counter(); checks = Counter()
    def add(layer, counts):
        for key, counts_row in counts.items():parameters[layer, key].update(counts_row)
    def cached(path, loader, content_sha=None):
        key = path.relative_to(root).as_posix(); stat = path.stat()
        signature = ['parameter-census-v3', stat.st_size, stat.st_mtime_ns, content_sha]
        saved = cache.get(key)
        if saved and saved['signature'] == signature:
            updated_cache[key] = saved; return saved['counts']
        counts = count_parameters(loader())
        updated_cache[key] = {'signature': signature, 'counts': counts}
        return counts
    def file_json(path, layer):
        try:
            counts = cached(path, lambda: _load(path)); add(layer, counts); datasets[layer] += 1
        except (ValueError, OSError, TypeError) as exc:
            failures.append({'path': path.relative_to(root).as_posix(), 'error': str(exc)})
    lab = root/'analysis-lab.html'; profile = {}
    if lab.exists():
        match = re.search(r'<script[^>]*id=["\']phase2-data["\'][^>]*>(.*?)</script>', site_html(lab, root), re.S)
        if match:
            profile = json.loads(match[1]); add('drivers', count_parameters(profile)); datasets['drivers'] = 1
            checks['unique_driver_ids'] = int(len({d['id'] for d in profile['drivers']}) == len(profile['drivers']))
            race_ids = {r['id'] for r in profile['races']}
            for driver in profile['drivers']:
                seen = set()
                for row in driver['races']:
                    checks['profile_race_rows'] += 1
                    if row['race'] not in race_ids:checks['broken_race_references'] += 1
                    if row['race'] in seen:checks['duplicate_driver_races'] += 1
                    seen.add(row['race'])
                    y = years[row['year']]; y['driver_races'] += 1
                    checks['shared_car_ambiguous'] += bool(row.get('shared_car_ambiguous'))
                    y['starts'] += bool((row.get('qualities') or {}).get('start'))
                    y['progression'] += bool(row.get('finished_on_track') is True and row.get('lap1_position') and row.get('finish'))
                    y['lap_ranks'] += len(row.get('lap_rankings', []))
                    y['teammate_comparisons'] += bool(row.get('comparison'))
                    for point in row.get('lap_rankings', []):
                        if not 1 <= point[1] <= point[2]:checks['invalid_lap_ranks'] += 1
            profile_sha = hashlib.sha256(match[1].encode()).hexdigest()
        else:
            profile_sha = None
    else:
        profile_sha = None
    catalogue=root/'races.html'
    if catalogue.exists():
        text=site_html(catalogue,root)
        match=re.search(r'<script[^>]*id=["\']catalogue-data["\'][^>]*>(.*?)</script>',text,re.S)
        if match:
            add('catalogue',cached(catalogue,lambda:json.loads(match[1]),hashlib.sha256(match[1].encode()).hexdigest()))
            datasets['catalogue']=1
    for directory in sorted((root/'analyses').glob('[12][0-9][0-9][0-9]')):
        for page, payload, sha in extract(root, int(directory.name)):
            y = years[int(directory.name)]; y['races'] += 1
            y['position_points'] += sum(p.get('lap', 0) > 0 for p in payload.get('positions', []))
            y['timed_laps'] += len(payload.get('all_laps', []))
            y['pitstops'] += len(payload.get('explorer', {}).get('pit', []))
            add('races', cached(page, lambda: payload, sha)); datasets['races'] += 1
            manifests.append({'path': page.relative_to(root).as_posix(), 'payload_sha256': sha})
            for url in re.findall(r'https?://[^\s<>"\']+', json.dumps(payload.get('sources', [])+payload.get('historical_reference', {}).get('sources', []) if isinstance(payload.get('historical_reference'), dict) else payload.get('sources', []))):source_urls.add(url)
            normalized = page.parent/'data/normalized'
            # Prefer a retained plain file over its identical compressed copy.
            files = list(normalized.glob('*.json'))
            files += [p for p in normalized.glob('*.json.gz') if not p.with_suffix('').exists()]
            for path in files:
                layer = 'normalized:'+path.name.removesuffix('.gz')
                file_json(path, layer)
        print('Collection inventory', directory.name, 'races', years[int(directory.name)]['races'], flush=True)
    archive_tables = []
    for family, path in [('F1DB', root/'analyses/sources/historical/historical.sqlite'),
                         ('StatsF1 compilation', root/'analyses/sources/historical/statsf1-compilation/database/sessionresults.db')]:
        if not path.exists():continue
        db = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
        if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
            failures.append({'path': path.relative_to(root).as_posix(), 'error': 'SQLite integrity check failed'})
        for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
            quoted = '"'+table.replace('"', '""')+'"'
            columns = [r[1] for r in db.execute('PRAGMA table_info('+quoted+')')]
            total = db.execute('SELECT COUNT(*) FROM '+quoted).fetchone()[0]
            # COUNT(col) preserves zero/false. Empty strings remain missing.
            def expression(c):
                q='"'+c.replace('"', '""')+'"'
                unknown="UPPER(CAST("+q+" AS TEXT)) IN ('UNKNOWN','N/A','UNAVAILABLE')"
                return ('SUM(CASE WHEN '+q+" IS NOT NULL AND "+q+" != '' AND NOT ("+unknown+") THEN 1 ELSE 0 END),"+
                        'SUM(CASE WHEN '+unknown+' THEN 1 ELSE 0 END)')
            expr = ','.join(expression(c) for c in columns)
            values = db.execute('SELECT '+expr+' FROM '+quoted).fetchone()
            archive_tables.append({'source': family, 'table': table, 'rows': total, 'columns': len(columns)})
            for i, c in enumerate(columns):
                n,unknown=values[i*2:i*2+2]
                add('archive:'+family, {table+'.'+c: {'slots': total, 'values': n or 0, 'unknown': unknown or 0,
                                                    'missing': total-(n or 0)-(unknown or 0)}})
        db.close()
    auxiliary = [root/'assets/historical-team-colors.json', root/'assets/historical-tyre-stints.json',
                 root/'assets/starter-metrics.json',root/'_storage/season-calendar.json',
                 root/'analyses/sources/incidents/registry.json', root/'analyses/sources/historical/coverage-audit.json']
    for folder in ('fia', 'pirelli', 'wayback', 'team-history', 'tyre-research'):
        auxiliary += [p for p in (root/'analyses/sources/historical'/folder).glob('*.json')
                      if p.name in ('inventory.json', 'normalized.json', 'summary.json', 'audit.json')]
    auxiliary += list((root/'analyses/sources/driver-history-expansion').glob('[12][0-9][0-9][0-9]-*.json'))
    for path in auxiliary:
        if not path.exists():continue
        if path.name=='registry.json':layer='incidents'
        elif path.parent.name=='driver-history-expansion':layer='archive:Atlas F1'
        else:layer='archive:'+path.relative_to(root).as_posix().removeprefix('analyses/sources/').removeprefix('assets/')
        file_json(path,layer)
    early=[_load(p) for p in (root/'analyses/sources/driver-history-expansion').glob('[12][0-9][0-9][0-9]-*.json')]
    for item in early:
        source=item['source'];body=root/'analyses/sources/driver-history-expansion'/source['file']
        if not body.exists() or hashlib.sha256(body.read_bytes()).hexdigest()!=source['sha256']:
            failures.append({'path':body.relative_to(root).as_posix(),'error':'Atlas source hash mismatch'})
        else:checks['atlas_verified_source_files']+=1
    atlas={'races':len(early),'retained_laps':sum(len(r['accepted_laps']) for r in early),
           'overlap_checks':sum(len(r.get('fastest_lap_crosschecks',[])) for r in early),
           'conflicting_laps':sum(len(r.get('conflicts',[])) for r in early),
           'winner_elapsed_checks':[dict(year=r['year'],round=r['round'],**r['winner_elapsed_crosscheck'])
                                    for r in early if r.get('winner_elapsed_crosscheck')]}
    inventory = []
    for name in ('analyses/sources', 'cache', '_documents'):
        paths = [p for p in (root/name).rglob('*') if p.is_file()] if (root/name).exists() else []
        inventory.append({'scope': name, 'files': len(paths), 'bytes': sum(p.stat().st_size for p in paths),
                          'extensions': dict(Counter(p.suffix or '(none)' for p in paths))})
    rows = [dict(layer=layer, parameter=key, **values) for (layer, key), values in sorted(parameters.items())]
    result = {'schema': 'data-collection-v1', 'generated_at': datetime.now(timezone.utc).isoformat(),
              'profile_sha256': profile_sha, 'profile_period': profile.get('period'),
              'drivers': len(profile.get('drivers', [])), 'profile_races': len(profile.get('races', [])),
              'parameters': rows, 'years': [dict(year=y, **counts) for y, counts in sorted(years.items())],
              'datasets': dict(datasets), 'archive_tables': archive_tables, 'files': inventory,
              'checks': dict(checks), 'atlas':atlas, 'failures': failures, 'sources_from_payloads': sorted(source_urls),
              'input_payloads': manifests}
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json_text(updated_cache))
    return result


def tr(nl, en, tag='span', attrs=''):
    return '<'+tag+attrs+' data-nl="'+html.escape(nl, quote=True)+'" data-en="'+html.escape(en, quote=True)+'">'+html.escape(nl)+'</'+tag+'>'


def render(data, journal):
    from .branding import branding
    from .site_navigation import with_navigation
    head = '<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Bronnen, parameters, aantallen, zoekmethoden en controles van Overtake It Away."><title>Datacollectie · Overtake It Away</title><link rel="stylesheet" href="assets/data-collection.css"></head><body><div class="collection-shell"><div class="race-hero">'+branding('assets/f1-banner-v3.png', seasons_url='races.html')
    head += tr('HET ARCHIEF ACHTER DE ANALYSE', 'THE ARCHIVE BEHIND THE ANALYSIS', 'p', ' class="eyebrow"')+tr('Datacollectie', 'Data collection', 'h1')
    head += tr('Wat is verzameld, waar komt het vandaan en hoe is het gecontroleerd?', 'What has been collected, where did it come from, and how was it checked?', 'p')+'</div>'
    nav = '<nav class="collection-nav">'+''.join(tr(nl, en, 'a', ' href="#'+key+'"') for key, nl, en in [('scope','Dekking','Coverage'),('parameters','Alle parameters','All parameters'),('sources','Bronnen & methoden','Sources & methods'),('searches','Zoeklogboek','Search journal'),('checks','Datacontroles','Data checks')])+'</nav>'
    content = '<main><section id="scope">'+tr('De verzameling in cijfers', 'Collection at a glance', 'h2')+'<div id="collection-summary" class="summary-grid"></div><details><summary>'+tr('Zo worden de aantallen geteld', 'How the counts are calculated')+'</summary><div class="details-copy">'
    content += tr('Een datapunt is hier één ingevulde parameterwaarde binnen de vermelde gegevenslaag. Een uitslag, een kopie daarvan in een dashboard en een afgeleide ranking zijn geen drie onafhankelijke waarnemingen. Tel de lagen daarom niet bij elkaar op. Nul en false tellen mee; null, lege tekst en expliciet onbekende waarden staan apart. Ontbrekende velden die niet in een record voorkomen zijn niet als null geteld.', 'A data point here is one populated parameter value within the stated data layer. A result, its dashboard copy and a derived rank are not three independent observations. Do not add the layers together. Zero and false count; null, empty text and explicit unknown values are separate. Fields absent from a record are not counted as null.', 'p')
    content += '</div></details>'+tr('De dekking verschilt per parameter en jaar. De tabel toont daadwerkelijk gebruikte coureursgegevens; de racekolommen beschrijven het afzonderlijke racearchief. Losse snelste ronden vóór 1996 gelden niet als volledige rondetijdreeksen.', 'Coverage varies by parameter and year. The table shows driver data actually used; the race columns describe the separate race archive. Isolated fastest laps before 1996 are not treated as complete lap-time series.', 'p', ' class="muted"')+'<div class="table-scroll"><table id="year-table"></table></div>'
    content += tr('Originele bestanden en lokale opslag', 'Original files and local storage', 'h3')+'<div class="table-scroll"><table id="storage-table"></table></div>'
    content += tr('De parameterlijst telt de bewaarde genormaliseerde racegegevens, coureursanalyses, bronregisters en brondatabasetabellen. PDF’s, afbeeldingen, onbewerkte timingstreams en binaire caches staan bij de bestandstelling; hun volledige tekst of pixels zijn geen extra statistische datapunten. Grote originele archieven blijven buiten de interactieve pagina’s.', 'The parameter list counts retained normalized race data, driver analyses, source registers and source database tables. PDFs, images, raw timing streams and binary caches appear in the file census; their full text or pixels are not extra statistical data points. Large original archives stay outside the interactive pages.', 'p', ' class="muted"')+'</section>'
    content += '<section id="parameters">'+tr('Alle parameters en aantallen', 'All parameters and counts', 'h2')+tr('Doorzoek parameter, gegevenslaag of bron', 'Search parameter, data layer or source', 'label', ' for="parameter-search"')+'<input id="parameter-search" type="search"><label class="layer-label" for="layer-filter">'+tr('Gegevenslaag', 'Data layer')+'</label><select id="layer-filter"></select><p id="parameter-count" class="muted" aria-live="polite"></p><div class="table-scroll"><table id="parameter-table"></table></div><div class="pager"><button id="parameter-prev" type="button">←</button><span id="parameter-page"></span><button id="parameter-next" type="button">→</button></div></section>'
    content += '<section id="sources">'+tr('Bronnen en verzamelmethoden', 'Sources and collection methods', 'h2')
    for method in journal.get('methods', []):
        content += '<details><summary>'+tr(method['title']['nl'], method['title']['en'])+'</summary><div class="details-copy">'
        for p in method['description']:content += tr(p['nl'], p['en'], 'p')
        for link in method.get('links', []):content += '<a class="source-link" href="'+html.escape(link['url'], quote=True)+'" target="_blank" rel="noopener">'+html.escape(link['title'])+' ↗</a>'
        content += '</div></details>'
    content += tr('Bewaarde databasetabellen', 'Retained database tables', 'h3')+'<div class="table-scroll"><table id="archive-table"></table></div></section>'
    content += '<section id="searches">'+tr('Zoeklogboek', 'Search journal', 'h2')+tr('Hier staan werkelijk vastgelegde zoekopdrachten en verzoeken. Niet alle oudere gesprekken bewaarden exacte zoektermen. Voor die periode zijn de reproduceerbare verzamelmethoden uit de collectors beschreven; ontbrekende zoekgeschiedenis is niet achteraf verzonnen.', 'These are recorded search queries and requests. Not every earlier conversation retained exact search terms. For that period, reproducible collection methods are documented from the collectors; missing search history has not been invented.', 'p')
    for entry in journal.get('searches', []):
        content += '<details><summary><time>'+html.escape(entry['date'])+'</time> · '+tr(entry['title']['nl'], entry['title']['en'])+'</summary><div class="details-copy">'
        content += '<ul>'+''.join('<li><code>'+html.escape(q)+'</code></li>' for q in entry['queries'])+'</ul>'
        content += tr(entry['result']['nl'], entry['result']['en'], 'p')+'</div></details>'
    content += '</section><section id="checks">'+tr('Controle, beperkingen en herhaalbaarheid', 'Validation, limitations and reproducibility', 'h2')
    for item in journal.get('checks', []):content += '<article class="check">'+tr(item['title']['nl'], item['title']['en'], 'h3')+tr(item['description']['nl'], item['description']['en'], 'p')+'</article>'
    content += '<div id="collection-checks"></div>'+tr('Bijwerken gebeurt tijdens het bouwen van de site en na een coureursbuild zodra deze pagina bestaat. De peildatum verandert alleen bij een nieuwe telling. Er worden vanuit deze pagina geen nieuwe bronverzoeken uitgevoerd. De inventaris is geen achtergrondmonitor.', 'The inventory refreshes during site builds and after driver builds once this page exists. Its timestamp changes only after a new census. This page makes no new source requests. The inventory is not a background monitor.', 'p')
    content += '<p>'+tr('Download de volledige telling', 'Download the full census', 'a', ' href="assets/data-collection.json" download')+'</p></section></main><footer><a href="index.html">Home</a><span id="collection-date"></span></footer></div>'
    page = head+nav+content+'<script type="application/json" id="collection-data">'+json_text(data)+'</script><script defer src="assets/data-collection.js"></script></body></html>'
    return with_navigation(page, 'assets/', True)


def build(root):
    root = Path(root).resolve(); source = Path(__file__).parent
    data = snapshot(root)
    path = root/'config/data-collection-journal.json'
    journal = _load(path) if path.exists() else {'methods': [], 'searches': [], 'checks': []}
    (root/'assets').mkdir(exist_ok=True)
    for name in ('data-collection.css', 'data-collection.js'):shutil.copyfile(source/name, root/'assets'/name)
    (root/'assets/data-collection.json').write_text(json_text(data)+'\n')
    (root/'data-collection.html').write_text(render(data, journal))
    return {'parameters': len(data['parameters']), 'years': len(data['years']), 'drivers': data['drivers'],
            'profile_races': data['profile_races'], 'checks': data['checks'], 'failures': data['failures']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--root', type=Path, default=Path.cwd())
    print(json.dumps(build(p.parse_args().root), indent=2))
