"""Build compact, auditable retirement / FIA-decision records without publishing.

Use --apply to attach only evidence pointers and retirement metadata to existing
driver observations. Position, lap, result, DNF flags and research stay intact.
"""
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
import argparse, csv, gzip, hashlib, html, io, json, re, zipfile
from f1_analysis.io import read_json
from f1_analysis.incidents import VERSION, normal, retirement_category, extract_decision, retirement_links, reconcile_decisions

ROOT=Path(__file__).resolve().parents[1]
STORE=ROOT/'analyses/sources/incidents'
OUT=ROOT/'storage/incident-research-20261016'


def compact(value):return json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False).replace('</','<\\/')


def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False))


def race_key(name):
    s=normal(name).replace('grandprix','').replace('grandpremio','').replace('formulaone','').replace('formula1','')
    s=re.sub(r'rightofreview$','',s)
    if s.startswith('of'):s=s[2:]
    aliases={'australia':'australian','austria':'austrian','hungary':'hungarian','belgium':'belgian','unitedkingdom':'british','china':'chinese','russia':'russian','germany':'german','japan':'japanese','europe':'european','italy':'italian','malaysia':'malaysian','brazil':'brazilian','spain':'spanish','canada':'canadian','mexico':'mexican','usa':'unitedstates','saudiarabia':'saudiarabian','demonaco':'monaco','montecarlo':'monaco','saopaulo':'brazilian','mexicocity':'mexican','barcelonacatalunya':'barcelona','bahraininmalaysia':'bahrain','70thanniversary':'70thanniversary'}
    return aliases.get(s,s)


def document_jobs():
    jobs={}
    for name in ['fia-documents.json','fia-legacy-documents.json','extra-documents.json','wayback-documents.json','early-fia-documents.json','manual-documents.json']:
        if (STORE/name).exists():
            for d in read_json(STORE/name):jobs[d['url']]=d
    for d in jobs.values():
        meta=STORE/'raw'/(hashlib.sha256(d['url'].encode()).hexdigest()+'.json')
        if meta.exists():d['source']=read_json(meta)
        resolved=meta.with_name(meta.stem+'.resolved.json')
        if resolved.exists():d['source']=read_json(resolved)['source']
        src=d.get('source',{});ocr=STORE/'raw'/('content-text-'+src.get('sha256','')+'.json')
        if ocr.exists():src.update(read_json(ocr))
    return list(jobs.values())


def main(apply=False):
    page=ROOT/'analysis-lab.html';markup=page.read_text();match=re.search(r'(<script[^>]*id="phase2-data"[^>]*>)(.*?)(</script>)',markup,re.S)
    data=json.loads(match[2]);races={r['id']:r for r in data['races']};race_by_name={(r['year'],race_key(r['name'])):r['id'] for r in races.values()}
    sources={}
    def source(url,path=None,**metadata):
        key='src-'+hashlib.sha256(url.encode()).hexdigest()[:16]
        if key not in sources:
            sources[key]={'url':url,**metadata}
            if path and path.exists():sources[key].update(local_file=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        return key
    # F1DB's source distribution keeps reasons and added classification penalties.
    archive=next((ROOT/'analyses/sources/historical/f1db').glob('*.zip'))
    release=read_json(archive.parent/'release.json')
    fsource=source(release.get('html_url','https://github.com/f1db/f1db/releases'),archive,publisher='F1DB',release=release.get('tag_name'))
    z=zipfile.ZipFile(archive)
    table=lambda n:list(csv.DictReader(io.TextIOWrapper(z.open(n))))
    fraces={r['id']:r for r in table('f1db-races.csv')}
    fdrivers={r['id']:r for r in table('f1db-drivers.csv')}
    fresults=defaultdict(list);fpenalties=[];unmatched_f1db=[]
    driver_key=lambda name:re.sub(r'jr$','',normal(name))
    for r in table('f1db-races-race-results.csv'):
        if not 2007<=int(r['year'])<=2026:continue
        fr=fraces[r['raceId']]
        # Round identity alone is unsafe when a rescheduled calendar differs.
        matches=[race for race in races.values() if race['year']==int(r['year']) and race['date']==fr['date']]
        if len(matches)!=1:continue
        race=matches[0];driver=fdrivers[r['driverId']]
        fresults[race['id'],driver_key(driver['name'])].append(r)
        if r['timePenalty'] or r['timePenaltyMillis']:
            fpenalties.append({'id':'f1db-'+r['raceId']+'-'+r['driverId'],'race':race['id'],'driver_id':r['driverId'],'driver_name':driver['name'],'driver_number':int(r['driverNumber']) if r['driverNumber'] else None,
                              'session':'Race','time_penalty':r['timePenalty'] or None,'time_penalty_millis':int(r['timePenaltyMillis']) if r['timePenaltyMillis'] else None,'source':fsource,
                              'detail_coverage':'classification_time_added_only','reason':None})
    modern={};controls=[]
    for race in races.values():
        path=ROOT/race['href'];run=path.parent;inp=run/'data/normalized/input.json'
        if not inp.exists() and not inp.with_suffix('.json.gz').exists():continue
        raw=read_json(inp);rows=raw.get('jolpica_results',[])
        url=f"https://api.jolpi.ca/ergast/f1/{race['year']}/{race['round']}/results.json"
        official=run/'data/raw/supplementary/jolpica-results.json'
        stored=official if official.exists() else inp
        sid=source(url,stored,publisher='Jolpica',retained=True)
        for r in rows:
            modern[race['id'],int(r['number'])]={'reason':r.get('status'),'source':sid,'driver_name':r.get('Driver',{}).get('givenName','')+' '+r.get('Driver',{}).get('familyName','')}
        ctrl=raw.get('race_control',[])
        if ctrl:
            cs=source(f"https://api.openf1.org/v1/race_control?session_key={raw.get('session',{}).get('session_key')}",inp,publisher='F1 timing via '+raw.get('timing_source','OpenF1'),retained=True)
            # FastF1 sessions have synthetic OpenF1 keys: use the upstream timing
            # archive reference instead of pretending the synthetic API is real.
            if raw.get('timing_source')=='FastF1':
                sources[cs]['url']='https://livetiming.formula1.com/static/'
                sources[cs]['session_reference']=raw.get('history_cache') or raw.get('session',{})
            for c in ctrl:
                message=c.get('message','')
                if re.search(r'PENALT|REPRIMAND|SUMMON|NOTED|INVESTIGAT|NO FURTHER ACTION|DISQUALIF|BLACK AND WHITE|TRACK LIMIT',message,re.I):
                    cid='rc-'+hashlib.sha256((race['id']+'|'+str(c.get('date'))+'|'+message).encode()).hexdigest()[:20]
                    controls.append({'id':cid,'race':race['id'],'session':'Race','date':c.get('date'),'lap':c.get('lap_number'),'driver_number':c.get('driver_number'),
                                     'message':message,'source':cs,'is_final_decision':False})
    retirements=[];status_conflicts=[];recovered_finishers=[]
    if (STORE/'registry.json').exists():
        recovered_finishers=list(read_json(STORE/'registry.json').get('recovered_finishers',[]))
    for driver in data['drivers']:
        for row in driver['races']:
            if row.get('finished_on_track') is not False:continue
            evidence=[];mr=modern.get((row['race'],row['number']))
            if mr:evidence.append(mr)
            elif row.get('finish_status'):
                race=races[row['race']];url=f"https://api.jolpi.ca/ergast/f1/{race['year']}/{race['round']}/results.json"
                path=ROOT/race['href']
                sid=source(url,path,publisher='Jolpica',retained=True)
                evidence.append({'reason':row['finish_status'],'source':sid})
            candidates=fresults.get((row['race'],driver_key(driver['name'])),[])
            if not candidates:
                # Common cross-source name ordering (Zhou Guanyu / Guanyu Zhou).
                if driver['id'] in ('zhou-guanyu','guanyu-zhou'):
                    candidates=fresults.get((row['race'],normal('Zhou Guanyu')),[]) or fresults.get((row['race'],normal('Guanyu Zhou')),[])
            if len(candidates)==1:
                r=candidates[0]
                if r['reasonRetired']:evidence.append({'reason':r['reasonRetired'],'source':fsource,'f1db_driver':r['driverId']})
                # FastF1 added the explicit status 'Lapped'; the old importer
                # incorrectly treated it as DNF. Require matching positive
                # F1DB finishing classification, distance and no retired reason.
                if (mr and mr['reason']=='Lapped' and not r['reasonRetired'] and r['positionNumber']
                        and r['laps'] and int(r['laps'])==row.get('finish_laps')
                        and int(r['positionNumber'])==row.get('finish')):
                    recovered_finishers.append({'driver':driver['id'],'race':row['race'],'status':'Lapped','source':mr['source'],'corroborating_source':fsource})
                    if apply:row.update(dnf=False,finished_on_track=True,finish_status='Lapped')
                    continue
            result_labels=[e['reason'] for e in evidence if (e['reason'] or '').casefold() in ('did not start','did not qualify','did not prequalify','withdrew','withdrawn','disqualified','excluded')]
            # 'Did not start, fuel leak' and 'Disqualified, fuel' describe
            # outcome and reason respectively, not contradictory causes.
            specific=[e for e in evidence if retirement_category(e['reason']) not in ('unknown','finished') and e['reason'] not in result_labels]
            reason=(specific or evidence or [{'reason':None}])[0]['reason'];category=retirement_category(reason)
            cause_category=category
            categories={retirement_category(e['reason']) for e in specific}
            conflict=(len(categories-{'ambiguous'})>1 and not categories<={'other','disqualified'}) or category=='finished'
            if any(label.casefold() in ('disqualified','excluded') for label in result_labels):category='disqualified'
            elif result_labels and not conflict:category='other'
            if conflict:
                status_conflicts.append({'driver':driver['id'],'race':row['race'],'evidence':evidence});category='conflicting_sources'
            retirements.append({'id':row['race']+':'+driver['id'],'race':row['race'],'driver_id':driver['id'],'driver_name':driver['name'],'number':row['number'],
                                'finished_on_track':False,'finish_laps':row.get('finish_laps'),'classified_position':row.get('finish'),
                                'reason':reason,'category':category,'reported_cause_category':cause_category,'result_labels':result_labels,'source_conflict':conflict,'evidence':evidence})
    official_notes=[]
    if (STORE/'official-results-notes.json').exists():
        country_alias={'great-britain':'britain','south-korea':'korea','united-states':'united-states','sao-paulo':'brazil','mexico-city':'mexico'}
        for p in read_json(STORE/'official-results-notes.json'):
            if not p['notes']:continue
            country=p['url'].split('/')[-2];country=country_alias.get(country,country)
            possible=[r for r in fraces.values() if int(r['year'])==p['year'] and r['grandPrixId']==country]
            mapped=[race for race in races.values() if race['year']==p['year'] and possible and race['date']==possible[0]['date']]
            src=p['source'];sid=source(p['url'],STORE/src['file'],publisher='Formula 1',fetched_at=src.get('fetched_at'))
            official_notes.append({'id':'f1-note-'+src['sha256'][:20],'year':p['year'],'race':mapped[0]['id'] if len(mapped)==1 else None,
                                   'session':p['kind'],'title':p['title'],'notes':p['notes'],'source':sid,'requires_review':True})
    recovered_finishers=list({(r['race'],r['driver']):r for r in recovered_finishers}.values())
    decisions=[];failed=[];unmatched=[]
    for d in document_jobs():
        src=d.get('source',{});race=d.get('race') or race_by_name.get((d['year'],race_key(d['event'])))
        if not src.get('text_file'):
            failed.append({**d,'reason':'no_extractable_pdf'});continue
        text=(STORE/src['text_file']).read_text(errors='replace')
        if len(text.strip())<60:
            failed.append({**d,'reason':'scan_or_empty_pdf'});continue
        record=extract_decision(d['title'],text)
        record['text_method']=src.get('text_method','pdf_text')
        record['text_complete']=not src.get('ocr_truncated',False)
        year_header=re.search(r'\b(20\d{2})\s+[A-Z][A-Z\s–-]{3,70}GRAND\s+PRIX\b',text[:1500])
        if year_header and int(year_header[1])!=d['year']:
            race=None;record.update(year_mismatch=int(year_header[1]),requires_review=True)
        record.update(id='fia-'+src['sha256'][:20],race=race,year=d['year'],event=d['event'],title=d['title'],published=d.get('published'),source=source(src.get('url',d['url']),STORE/src['file'],publisher='FIA',original_url=d['url'],fetched_at=src.get('fetched_at')))
        if not race:unmatched.append({'id':record['id'],'year':d['year'],'event':d['event']})
        decisions.append(record)
    # Content duplicates (old /file/ URLs vs current PDF URLs) are one decision.
    decisions=list({d['id']:d for d in decisions}.values())
    reconcile_decisions(decisions)
    by_race=defaultdict(list)
    for d in decisions:
        if d['race']:by_race[d['race']].append(d)
    for row in retirements:row['related_decisions']=retirement_links(row,by_race[row['race']])
    verified=read_json(STORE/'verified-links.json') if (STORE/'verified-links.json').exists() else []
    for review in verified:
        row=next((r for r in retirements if r['race']==review['race'] and r['driver_id']==review['driver_id']),None)
        doc=next((d for d in decisions if d['id']==review['document'] and d['race']==review['race']),None)
        if not row or not doc:raise ValueError('Verified retirement link has lost its source or driver: '+str(review))
        link=next((l for l in row['related_decisions'] if l['document']==doc['id']),None)
        if not link:raise ValueError('Verified relationship no longer matches source/session: '+str(review))
        link.update(review)
        doc.update(requires_review=False,review_scope='Structured fields and this specific retirement link checked',reviewed_on=review['reviewed_on'])
    # Explicit coverage, never 'zero penalties' merely because nothing was found.
    coverage=[]
    for race in sorted(races.values(),key=lambda r:(r['year'],r['round'])):
        ds=by_race[race['id']]
        coverage.append({'race':race['id'],'year':race['year'],'name':race['name'],'documents':len(ds),'race_control_messages':sum(c['race']==race['id'] for c in controls),
                         'classified_time_penalties':sum(c['race']==race['id'] for c in fpenalties),'complete_penalty_history':False,
                         'coverage':'documents_collected_unreviewed' if ds else 'timing_and_results_only','retirement_reasons':dict(Counter(r['category'] for r in retirements if r['race']==race['id']))})
    registry={'schema':VERSION,'generated_at':datetime.now(timezone.utc).isoformat(),'scope':{'from':2007,'to':2026,'profile_races':len(races),'sessions':'All available FIA weekend decisions; retained race-control messages are Race only.'},
              'method':{'causation':'Never inferred from same-race penalty. Candidate links need review.','completeness':'Unknown remains unknown; no record is not proof of no penalty.','classification_penalties':'Time added to final results only; does not include every served penalty.','categories':['incident','technical','ambiguous','other','disqualified','unknown','conflicting_sources']},
              'races':[{k:r[k] for k in ('id','year','round','name','circuit','date','href')} for r in races.values()],
              'retirements':retirements,'recovered_finishers':recovered_finishers,'decisions':decisions,'official_result_notes':official_notes,'race_control':list({c['id']:c for c in controls}.values()),'classification_penalties':fpenalties,'sources':sources,'coverage':coverage}
    save(STORE/'registry.json',registry)
    packed=gzip.compress(compact(registry).encode(),compresslevel=9,mtime=0);(ROOT/'assets/driver-incidents.json.gz').write_bytes(packed)
    audit={'schema':VERSION,'profile_races':len(races),'nonfinish_results':len(retirements),'categories':dict(Counter(r['category'] for r in retirements)),
           'fia_documents':len(decisions),'outcomes':dict(Counter(d['outcome'] for d in decisions)),
           'effective_outcomes':dict(Counter(d['effective_outcome'] for d in decisions)),
           'documents_by_year':dict(sorted(Counter(d['year'] for d in decisions).items())),
           'penalty_types':dict(Counter(t for d in decisions if d['effective_outcome']=='penalty' for t in d['sanction_types'])),
           'retirements_with_candidate_links':sum(bool(r['related_decisions']) for r in retirements),'source_confirmed_retirement_links':sum(bool(l['causation_confirmed']) for r in retirements for l in r['related_decisions']),'race_control_messages':len(registry['race_control']),
           'classification_penalty_summaries':len(fpenalties),'official_result_notes':len(official_notes),'recovered_lapped_finishers':recovered_finishers,'source_conflicts':status_conflicts,'failed_documents':failed,'unmatched_document_events':unmatched,
           'compressed_public_bytes':len(packed),'complete_penalty_history_claimed':False}
    save(OUT/'audit.json',audit)
    if apply:
        lookup={(r['race'],r['driver_id']):r for r in retirements};changed=0
        for driver in data['drivers']:
            for row in driver['races']:
                evidence=lookup.get((row['race'],driver['id']))
                if evidence:
                    # Keep source results and all model inputs untouched.
                    row['retirement_evidence']={'id':evidence['id'],'reason':evidence['reason'],'category':evidence['category']};changed+=1
        data['settings']['incident_evidence']={'version':VERSION,'href':'assets/driver-incidents.json.gz','sha256':hashlib.sha256(packed).hexdigest(),'bytes':len(packed),'embedded':False}
        markup=markup[:match.start(2)]+compact(data)+markup[match.end(2):];page.write_text(markup)
        audit['attached_to_driver_rows']=changed;save(OUT/'audit.json',audit)
    print(json.dumps({k:(len(v) if k=='recovered_lapped_finishers' else v) for k,v in audit.items() if k not in ('source_conflicts','failed_documents','unmatched_document_events')},indent=2))
    report(registry,audit)


def report(registry,audit):
    esc=lambda s:html.escape(str(s or ''))
    cats={'incident':'Ongeval / botsing','technical':'Technisch gemeld','ambiguous':'Oorzaak niet eenduidig','other':'Overig / niet gestart','disqualified':'Diskwalificatie','unknown':'Onbekend','conflicting_sources':'Bronnen spreken elkaar tegen'}
    trs=''.join(f'<tr><td>{year}</td><td>{audit["documents_by_year"].get(year,0)}</td></tr>' for year in range(2007,2027))
    rows=''.join(f'<tr><td>{esc(r["race"])}</td><td>{esc(r["driver_name"])}</td><td>{esc(r["reason"])}</td><td>{esc(cats[r["category"]])}</td><td>{len(r["related_decisions"])}</td></tr>' for r in registry['retirements'])
    document_rows=''.join(f'<tr><td>{esc(d["year"])}</td><td>{esc(d["event"])}</td><td><a href="{esc(registry["sources"][d["source"]]["url"])}">{esc(d["title"])}</a></td><td>{esc(d["session"])}</td><td>{esc(d["effective_outcome"])}</td><td>{esc(d["decision"])}</td></tr>' for d in sorted(registry['decisions'],key=lambda d:(d['year'],d['event'],d['document_number'] or 0)))
    content=f'''<!doctype html><html lang="nl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Uitvalredenen en straffen — broncontrole</title><style>body{{background:#0d121a;color:#edf2fa;font:16px system-ui;margin:2rem;line-height:1.6}}h1,h2{{color:#c678ff}}a{{color:#51d6dd}}table{{border-collapse:collapse;width:100%;font-size:.85rem}}td,th{{text-align:left;border-bottom:1px solid #354253;padding:.5rem;vertical-align:top}}summary{{cursor:pointer;color:#efc465}}.scroll{{overflow:auto}}.note{{border-left:3px solid #efc465;padding:1rem;background:#171f2c}}input{{padding:.7rem;background:#171f2c;color:white;border:1px solid #51d6dd;width:min(30rem,90%)}}</style><h1>Uitvalredenen en straffen</h1><p>Lokale broncontrole · dataset 2007–2026 · {audit['profile_races']} races · {audit['nonfinish_results']} niet als rijdend gefinisht geregistreerde resultaten.</p><p class="note">Dit is een bronregister, geen schuldscore. Een botsing bewijst geen fout van de betrokken coureur. Een straf tijdens hetzelfde weekend bewijst geen verband met diens uitval. Onderzoek, oproep, opgelegde straf, besluit zonder verdere actie en ingetrokken straf blijven onderscheiden. Een ontbrekend document betekent onbekend, niet nul straffen. Niet alle documenten zijn inhoudelijk handmatig gecontroleerd.</p><h2>Opgeslagen informatie</h2><p>{audit['fia_documents']} FIA-documenten met leesbare tekst; {audit['race_control_messages']} relevante wedstrijdleidingsmeldingen; {audit['classification_penalty_summaries']} samenvattingen van tijd die bij de uitslag is opgeteld. Dit laatste is geen overzicht van alle tijdens een race uitgevoerde straffen. Compact databestand: {audit['compressed_public_bytes']/1e6:.2f} MB. Originele bronbestanden blijven lokaal bewaard.</p><details><summary>FIA-documenten per jaar</summary><table><tr><th>Jaar</th><th>Documenten</th></tr>{trs}</table></details><h2>Brondekking en interpretatie</h2><p>De uitvalreden is letterlijk uit de bewaarde uitslagbron en F1DB overgenomen. 'Technisch gemeld' betekent een component- of systeemprobleem volgens die bron; het bewijst niet dat een eerdere botsing geen rol speelde. Banden, lekke banden, wielophanging, vleugels en schade blijven daarom apart als niet eenduidig gemarkeerd. Bronnen met verschillende categorieën worden niet stilzwijgend samengevoegd.</p><p>FIA-besluiten bewaren feit, overtreden regel, beslissing, motivering, sessie en — indien expliciet vermeld — tijdstraf, gridstraf, strafpunten of boete. Automatisch herkende velden moeten voor gebruik als statistiek worden gecontroleerd. Sprintbesluiten worden niet als hoofdracebesluit gekoppeld. Een teruggedraaide straf blijft historisch zichtbaar met de verwijzing naar het herzieningsbesluit.</p><p>Verbanden met uitval zijn kandidaten op basis van expliciet genoemde betrokken auto's. Zelfs een expliciete vermelding van uitval krijgt zonder inhoudelijke controle nog geen definitief causaal label. Betrokkenheid en de rol van bestrafte rijder blijven apart.</p><label>Zoek in onderstaande tabellen <input id="search" placeholder="Bijvoorbeeld Vettel, 2021-10, collision"></label><h2>Uitvalregistraties</h2><div class="scroll"><table id="retirements"><thead><tr><th>Race</th><th>Coureur</th><th>Bronreden</th><th>Categorie</th><th>Verwante besluiten</th></tr></thead><tbody>{rows}</tbody></table></div><details><summary>Alle verzamelde FIA-besluiten en strafdetails</summary><div class="scroll"><table id="decisions"><thead><tr><th>Jaar</th><th>Evenement</th><th>Bron</th><th>Sessie</th><th>Status</th><th>Besluit</th></tr></thead><tbody>{document_rows}</tbody></table></div></details><script>document.querySelector('#search').addEventListener('input',e=>{{let q=e.target.value.toLowerCase();document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))}})</script></html>'''
    confirmed=[]
    for r in registry['retirements']:
        for link in r['related_decisions']:
            if not link['causation_confirmed']:continue
            d=next(d for d in registry['decisions'] if d['id']==link['document'])
            summaries={'daniel-ricciardo':'De FIA-stewards verbinden de botsing van Stroll expliciet aan de uitval van Ricciardo. De straf is voor Stroll, niet voor Ricciardo.',
                       'george-russell':'De FIA-stewards verbinden de botsing van Räikkönen met auto 63 expliciet aan de uitval van Russell. De straf is voor Räikkönen.',
                       'lando-norris':'De FIA-stewards noemen Norris als enige verantwoordelijke voor de botsing en beschrijven zijn uitval, hoewel hij nog geklasseerd werd. De tijdstraf na de race is voor Norris.'}
            description=summaries.get(r['driver_id'],link['confirmation_scope'])
            confirmed.append(f'<li><b>{esc(r["race"])} · {esc(r["driver_name"])}</b> — {esc(description)} <a href="{esc(registry["sources"][d["source"]]["url"])}">FIA-besluit {d["document_number"]}</a>.</li>')
    notes=''.join(f'<tr><td>{n["year"]}</td><td>{esc(n["session"])}</td><td><a href="{esc(registry["sources"][n["source"]]["url"])}">{esc(n["title"])}</a></td><td>{esc(" ".join(n["notes"]))}</td></tr>' for n in registry['official_result_notes'])
    extra=f'<h2>Inhoudelijk bevestigde koppelingen</h2><p>{audit["source_confirmed_retirement_links"]} koppelingen zijn tegen het oorspronkelijke FIA-besluit gecontroleerd. De overige {audit["retirements_with_candidate_links"]} uitvalregistraties met verwante documenten kunnen ook ongerelateerde incidenten bevatten.</p><ul>{"".join(confirmed)}</ul><h2>Beperkingen die zichtbaar blijven</h2><p>Vooral vóór 2013 is de strafhistorie nog onvolledig. Ook in latere jaren betekent de verzameling geen garantie dat elk strafbesluit is teruggevonden. {len(audit["source_conflicts"])} bronconflicten zijn apart bewaard. {len(audit["failed_documents"])} gevonden documenten missen nog bruikbare tekst of een geslaagde download. Scans zijn waar mogelijk met OCR gelezen; de OCR-uitkomst vraagt extra controle. {len(audit["recovered_lapped_finishers"])} foutief als uitval geïmporteerde Lapped-resultaten zijn door een overeenkomende uitslag en gereden afstand als finish herkend.</p><details><summary>Toelichtingen bij officiële F1-uitslagen en startopstellingen</summary><div class="scroll"><table><thead><tr><th>Jaar</th><th>Onderdeel</th><th>Bron</th><th>Toelichting</th></tr></thead><tbody>{notes}</tbody></table></div></details>'
    extra=extra.replace(f'De overige {audit["retirements_with_candidate_links"]} uitvalregistraties',f'De overige {max(0,audit["retirements_with_candidate_links"]-len(confirmed))} uitvalregistraties')
    content=content.replace('<h2>Uitvalregistraties</h2>',extra+'<h2>Uitvalregistraties</h2>')
    (OUT/'broncontrole.html').write_text(content)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');main(p.parse_args().apply)
