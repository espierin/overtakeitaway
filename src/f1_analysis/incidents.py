"""Evidence-preserving retirement categories and FIA decision extraction.

An incident, a summons, a decision, a penalty and a causal retirement link are
different observations. Unknown is never encoded as zero or innocent/guilty.
"""
import re, unicodedata

VERSION = 'retirement-stewards-evidence-v1'


def normal(value):
    return re.sub(r'[^a-z0-9]+','',unicodedata.normalize('NFKD',str(value or '')).encode('ascii','ignore').decode().lower())


def retirement_category(reason):
    s=(reason or '').strip().casefold()
    if not s or s in ('unknown','onbekend','retired','not classified','did not finish','dnf','damage'):
        return 'unknown'
    if s in ('finished','lapped') or re.fullmatch(r'\+\d+\s+laps?',s):return 'finished'
    if any(x in s for x in ('disqual','excluded','illegal','underweight','fuel sample','outside assistance')):return 'disqualified'
    if s in ('did not start','did not qualify','did not prequalify','withdrew','withdrawn','not restarted','107% rule','out of fuel','fuel shortage') or any(x in s for x in ('illness','unwell','injur','physical','eye ')):return 'other'
    if any(x in s for x in ('collision','accident','spun off','crash')):return 'incident'
    # These are component / damage descriptions, not reliable root causes.
    if any(x in s for x in ('suspension','puncture','tyre','tire','wheel','wing','chassis','undertray','debris','handling','vibrat','track rod')):return 'ambiguous'
    technical=('engine','gearbox','transmission','brake','hydraulic','power unit','power loss','electri','electron','oil','water','cool','fuel','overheat','clutch','turbo','battery','radiator','ers','drivetrain','driveshaft','halfshaft','differential','exhaust','throttle','ignition','pneumatic','mechanical','technical','inject','alternator','supercharger','magneto','spark','crankshaft','safety switch','airbox','broken seat','steering')
    if any(x in s for x in technical):return 'technical'
    return 'other'


LABELS = re.compile(r'^\s*(No\s*/\s*Driver|Driver|Competitor|Session|Fact|Facts|Offence|Infringement|Decision(?:\s+\d+(?=\s*:))?|Reason(?:s)?)\s*:?\s{1,}(.*)$',re.I)


def fields(text):
    sections={};key=None
    for line in text.replace('\xa0',' ').splitlines():
        if re.search(r'Competitors are reminded|right to appeal|Decisions of the Stewards are taken independently',line,re.I):
            key=None;continue
        match=LABELS.match(line)
        if match:
            key=re.sub(r'\s+',' ',match[1].lower());key={'facts':'fact','reasons':'reason'}.get(key,key)
            sections.setdefault(key,[]).append(match[2].strip())
        elif key and line.strip():sections[key].append(line.strip())
    return {k:re.sub(r'\s+',' ',' '.join(v)).strip() for k,v in sections.items()}


def extract_decision(title, text):
    """Conservative structured extraction; full verbatim fields retain detail.

    No sanction is inferred from 'alleged', 'noted', 'summoned', or title alone.
    Amounts only come from operative decision sections, never past points totals.
    """
    text=text.replace('\xa0',' ');f=fields(text)
    decision=' '.join(v for k,v in f.items() if k.startswith('decision'))
    reason=f.get('reason','');title_num=re.search(r'\bDoc(?:ument)?\s+(\d+)\b',title,re.I)
    body_num=re.search(r'\bDocument\s+(\d+)\b',text,re.I)
    no=f.get('no / driver',f.get('driver',''))
    target=re.match(r'(\d{1,3})(?:\s*[-–]|\s*$)',no)
    if not target:target=re.search(r'\bCar\s+(\d{1,3})\b',title,re.I)
    numbers=sorted(set(int(n) for n in re.findall(r'\b[Cc]ars?\s+(\d{1,3})\b',text+' '+title)))
    for group in re.findall(r'\b[Cc]ars\s+(\d{1,3}(?:\s*(?:,|&|and)\s*\d{1,3})+)',text+' '+title):
        numbers=sorted(set(numbers+[int(n) for n in re.findall(r'\d+',group)]))
    if target:numbers=sorted(set(numbers+[int(target[1])]))
    # Review rulings can contain no structured form and multiple Decisions.
    overturned=bool(re.search(r'(?:penalty.*?(?:is|was) (?:removed|rescinded|cancelled)|reverse the previous decision|decision.*?is (?:rescinded|overturned))',decision,re.I))
    no_action=bool(re.search(r'no further action|no (?:further )?penalty|no breach|no action',decision,re.I))
    types=[]
    for typ,pattern in [('time',r'\b(?:\d+|five|ten|twenty)[ -]seconds?\b.{0,30}\bpenalty|\btime penalty\b'),('grid',r'\bgrid.{0,35}\bpenalty|\b(?:drop|grid place)\b.{0,40}\b(?:grid|penalty)\b|start.{0,45}back of.{0,25}grid'),('drive_through',r'drive[ -]?through'),('stop_go',r'stop[ -](?:and[ -])?go|stop/go'),('fine',r'\bfine(?:d)?\b|€|EUR'),('reprimand',r'\breprimand'),('warning',r'\bwarning'),('disqualification',r'\bdisqualif|\bexcluded from'),('ban',r'\bsuspend(?:ed|sion)?\b.{0,60}\b(?:race|competition)|\brace ban\b'),('pit_lane_start',r'start.{0,30}pit lane'),('lap_deletion',r'lap time.{0,30}(?:deleted|cancelled)')]:
        if re.search(pattern,decision,re.I):types.append(typ)
    summoned=bool(re.search(r'\bsummons\b',title,re.I) or re.search(r'required to report to the Stewards',text,re.I))
    outcome='overturned' if overturned else 'no_further_action' if no_action and not types else 'penalty' if types else 'summons' if summoned else 'unresolved'
    seconds=re.search(r'\b(\d+)\s*(?:[- ]second[s]?)\s+(?:time\s+)?penalty',decision,re.I)
    points=re.search(r'\b(\d+)\s+penalty points?\b',decision,re.I)
    total_points=re.search(r'\btotal of\s+(\d+)\b',decision,re.I)
    grid=re.search(r'\b(\d+)\s*(?:[- ](?:place|position|grid))?.{0,22}\bgrid',decision,re.I)
    money=re.search(r'(?:€|EUR\s*)([\d][\d., ]*)',decision,re.I)
    session=f.get('session')
    # Some report layouts omit a colon / spacing; never assign the race from
    # the fact that an event also contains a race. Sprint remains separate.
    if session:
        session=re.split(r'\b(?:Fact|Offence|Decision)\b',session)[0].strip()
        session='Race' if session.casefold()=='race' else session
    lap=re.search(r'\blap\s+(\d+)\b',f.get('fact',''),re.I)
    incident_time=re.search(r'^\s*No\s*/\s*Driver\b.*?^\s*Time\s*:?\s+(\d{1,2}:\d{2}(?::\d{2})?)\b',text,re.M|re.S|re.I)
    blame=None
    if re.search(r'wholly or predominantly to blame|predominantly to blame|wholly to blame|solely to blame',reason,re.I):blame='stewards_explicit_blame'
    return {'document_number':int((body_num or title_num)[1]) if title_num or body_num else None,
            'driver_number':int(target[1]) if target else None,'driver_label':no or None,
            'involved_numbers':numbers,'session':session,'incident_time_local':incident_time[1] if incident_time else None,'lap':int(lap[1]) if lap else None,
            'outcome':outcome,'sanction_types':types if outcome=='penalty' else [],
            'time_penalty_seconds':int(seconds[1]) if seconds and outcome=='penalty' else None,
            'grid_places':int(grid[1]) if grid and outcome=='penalty' and 'grid' in types else None,
            'penalty_points':int(points[1]) if points and outcome=='penalty' else None,
            'penalty_points_total_at_decision':int(total_points[1]) if points and total_points and outcome=='penalty' else None,
            'fine_text':money[0].strip().rstrip('.,') if money and outcome=='penalty' else None,
            'fact':f.get('fact') or None,'offence':f.get('offence',f.get('infringement')) or None,
            'decision':decision or None,'reason':reason or None,'blame_evidence':blame,
            'requires_review':True,'fields_extracted':bool(decision and session),
            'is_collision':bool(re.search(r'collision|collid|causing an accident',f.get('fact','')+' '+title,re.I))}


def reconcile_decisions(records):
    """Retain revisions but count only operative versions of each document.

    A replacement can keep a time penalty while removing licence points. Such
    a replacement does not cancel every sanction from that incident.
    """
    from collections import defaultdict
    groups=defaultdict(list)
    for d in records:
        d['effective_outcome']=d['outcome']
        if d.get('race') and d.get('document_number') is not None:groups[d['race'],d['document_number']].append(d)
    def order(d):
        p=re.search(r'(\d{2})\.(\d{2})\.(\d{2}) (\d{2}):(\d{2})',d.get('published') or '')
        stamp='20'+p[3]+p[2]+p[1]+p[4]+p[5] if p else ''
        amended=bool(re.search(r'corrected|amended|revised|replacement',d['title'],re.I))
        return stamp,amended,d['id']
    active={}
    for key,versions in groups.items():
        newest=max(versions,key=order);active[key]=newest
        for old in versions:
            if old is not newest:old.update(effective_outcome='superseded',superseded_by=newest['id'])
    for d in records:
        if not d.get('race'):continue
        if d['outcome']=='overturned':
            mentions=re.findall(r'\b[Dd]ocument(?:\s+[Nn]umber|\s+[Nn]o\.?)?\s+(\d+)\b',d.get('decision') or '')
            mode='overturned'
        else:
            mentions=re.findall(r'(?:[Rr]eplacement for [Dd]ocument|[Rr]eplace [Dd]ocument)\s+(\d+)\b',d['title']+' '+(d.get('reason') or ''))
            mode='superseded'
        for n in mentions:
            old=active.get((d['race'],int(n)))
            if old and old is not d:old.update(effective_outcome=mode,superseded_by=d['id'])
    return records


def retirement_links(row, decisions):
    """Link event evidence without promoting temporal proximity to causation."""
    if row.get('finished_on_track') is not False:return []
    out=[];number=row.get('number')
    for d in decisions:
        if d.get('effective_outcome') in ('superseded','overturned'):continue
        if d.get('session')!='Race' or number not in d.get('involved_numbers',[]) or not d.get('is_collision'):continue
        if row.get('category') not in ('incident','ambiguous','unknown'):continue
        # Explicit number + inability to continue in one sentence is recorded as
        # documentary evidence; final causation still needs human review.
        sentences=re.split(r'(?<=[.!?])\s+',d.get('reason') or '')
        evidence=next((s for s in sentences if re.search(rf'\b[Cc]ar\s+{number}\b',s) and re.search(r'\bretir|unable to continue|end(?:ed)? (?:his|their|the) race|out of the race',s,re.I)),None)
        out.append({'document':d['id'],'relation':'explicit_retirement_mention' if evidence else 'collision_involvement_candidate',
                    'role':'decision_subject' if number==d.get('driver_number') else 'other_involved_driver',
                    'penalty_outcome':d.get('effective_outcome',d['outcome']),'causation_confirmed':False,'evidence':evidence})
    return out


def attach_retained(data, root):
    """Attach compact evidence references, not thousands of PDF paragraphs.

    This optional registry is retained across later driver-page rebuilds. New
    races absent from the registry remain unclassified rather than guessed.
    """
    import gzip, json, hashlib
    from pathlib import Path
    path=Path(root)/'assets/driver-incidents.json.gz'
    if not path.exists():return 0
    packed=path.read_bytes();registry=json.loads(gzip.decompress(packed))
    lookup={(r['race'],r['driver_id']):r for r in registry['retirements']}
    recovered={(r['race'],r['driver']):r for r in registry.get('recovered_finishers',[])}
    attached=0
    for driver in data['drivers']:
        for row in driver['races']:
            key=row['race'],driver['id']
            if key in recovered and row.get('finish_status') in (None,'Lapped'):
                row.update(dnf=False,finished_on_track=True,finish_status='Lapped')
            evidence=lookup.get(key)
            if evidence:
                row['retirement_evidence']={'id':evidence['id'],'reason':evidence['reason'],'category':evidence['category']};attached+=1
    data.setdefault('settings',{})['incident_evidence']={'version':VERSION,'href':'assets/driver-incidents.json.gz','sha256':hashlib.sha256(packed).hexdigest(),'bytes':len(packed),'embedded':False}
    return attached
