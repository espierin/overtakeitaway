"""Resumable acquisition of F1 retirement and steward evidence (local archive).

No inferred guilt, no guessed zero penalties. Raw documents are content hashed.
The public dataset is built separately; PDFs never enter the page payload.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
from datetime import datetime, timezone
import argparse, hashlib, json, re, threading, time, subprocess
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / 'analyses/sources/incidents'
LOCK = threading.Lock()
LOCAL = threading.local()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    temp.replace(path)


def fetch(url, refresh=False):
    key = hashlib.sha256(url.encode()).hexdigest()
    meta = STORE/'raw'/f'{key}.json'
    if meta.exists() and not refresh:
        return json.loads(meta.read_text())
    if not hasattr(LOCAL, 'session'):
        LOCAL.session = requests.Session()
        LOCAL.session.headers['User-Agent'] = 'OvertakeItAway/1.0 (historical F1 data preservation)'
    out = {'url':url, 'fetched_at':datetime.now(timezone.utc).isoformat()}
    for attempt in range(3):
        try:
            r = LOCAL.session.get(url, timeout=(12,45))
            out.update(http_status=r.status_code, final_url=r.url)
            if r.status_code in (429,500,502,503,504):
                time.sleep(2**attempt*2);continue
            if r.status_code == 200:
                body=r.content
                kind='pdf' if body.startswith(b'%PDF') else 'html' if '<html' in r.text[:2000].lower() or '<!doctype' in r.text[:2000].lower() else 'body'
                digest=hashlib.sha256(body).hexdigest();target=STORE/'raw'/f'{digest}.{kind}'
                if not target.exists():target.write_bytes(body)
                out.update(file=str(target.relative_to(STORE)),sha256=digest,bytes=len(body),kind=kind)
                if kind=='pdf':
                    txt=target.with_suffix('.txt')
                    if not txt.exists():
                        subprocess.run(['pdftotext','-layout',str(target),str(txt)],check=False,stderr=subprocess.DEVNULL)
                    if txt.exists():out['text_file']=str(txt.relative_to(STORE))
            break
        except requests.RequestException as exc:
            out['error']=str(exc);time.sleep(attempt+1)
    save(meta,out)
    time.sleep(.12)
    return out


def soup(source):
    return BeautifulSoup((STORE/source['file']).read_text(errors='replace'),'html.parser') if source.get('kind')=='html' else BeautifulSoup('','html.parser')


def pooled(jobs, fn, label):
    out=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(fn,j) for j in jobs]
        for i,f in enumerate(as_completed(futures),1):
            out.append(f.result())
            if i%25==0 or i==len(jobs):print(label,i,'/',len(jobs),flush=True)
    return out


def index_fia():
    STORE.mkdir(parents=True,exist_ok=True)
    first=fetch('https://www.fia.com/documents/formula-1')
    seasons=[]
    for o in soup(first).select('option[value]'):
        v=o['value'];m=re.search(r'/season/season-(\d{4})-',v)
        if m and 2007<=int(m[1])<=2026:
            seasons.append((int(m[1]),urljoin(first['url'],v)+'/championships/fia-formula-one-world-championship-14'))
    def season(job):
        year,url=job;page=fetch(url);events=[]
        for o in soup(page).select('option[value]'):
            if '/event/' in o['value']:events.append({'year':year,'event':o.get_text(' ',strip=True),'url':urljoin(url,o['value'])})
        return {'year':year,'source':page,'events':events}
    years=pooled(seasons,season,'FIA seasons');save(STORE/'fia-seasons.json',years)
    events=[e for y in years for e in y['events']]
    def event(e):
        page=fetch(e['url']);docs=[]
        for a in soup(page).select('li.document-row a[href]'):
            title=a.select_one('.title');title=title.get_text(' ',strip=True) if title else a.get_text(' ',strip=True)
            if re.search(r'decision|offence|infringement|summons|protest|review|reprimand|race classification|final starting grid|parc ferm',title,re.I):
                published=a.select_one('.published')
                docs.append({'year':e['year'],'event':e['event'],'title':title,'published':published.get_text(' ',strip=True) if published else None,'url':urljoin(e['url'],a['href']),'index_url':e['url']})
        return {**e,'source':page,'documents':docs}
    indexed=pooled(events,event,'FIA events');save(STORE/'fia-events.json',indexed)
    docs={d['url']:d for e in indexed for d in e['documents']}
    save(STORE/'fia-documents.json',list(docs.values()));print('FIA indexed documents',len(docs),flush=True)


def legacy_fia():
    # These older event pages expose the original Event & Timing / classification
    # tabs, including FIA decisions predating the new document portal.
    data=json.loads(re.search(r'<script[^>]*id="phase2-data"[^>]*>(.*?)</script>',(ROOT/'analysis-lab.html').read_text(),re.S)[1])
    events=[r for r in data['races'] if r['year']<=2018]
    def event(e):
        name=re.sub('[^a-z0-9]+','-',e['name'].lower()).strip('-')
        url=f"https://www.fia.com/championship/events/fia-formula-one-world-championship/season-{e['year']}/{name}"
        page=fetch(url);tabs=[];docs=[]
        for a in soup(page).select('a[href]'):
            if re.search(r'/(?:eventtiming-information|session-classifications)(?:-|$)',a['href']):tabs.append(urljoin(url,a['href']))
        for tab in dict.fromkeys(tabs):
            p=fetch(tab)
            for a in soup(p).select('a[href]'):
                href=a['href'];title=a.get_text(' ',strip=True)
                if re.search(r'/file/\d+/download|\.pdf(?:\?|$)',href) and re.search(r'decision|offence|infringement|summons|protest|review|penalt|reprimand|race classification|starting grid',title,re.I):
                    docs.append({'year':e['year'],'event':e['name'],'race':e['id'],'title':title,'url':urljoin(tab,href),'index_url':tab,'published':None})
        return {'race':e['id'],'year':e['year'],'event':e['name'],'source':page,'tabs':tabs,'documents':docs}
    indexed=pooled(events,event,'Legacy FIA events');save(STORE/'fia-legacy-events.json',indexed)
    docs={d['url']:d for e in indexed for d in e['documents']};save(STORE/'fia-legacy-documents.json',list(docs.values()));print('Legacy indexed documents',len(docs),flush=True)


def retained_fia():
    """Revisit retained 2013-2019 FIA pages: the prior tyre project deliberately
    excluded steward correspondence, but preserved the original page links.
    """
    previous=ROOT/'analyses/sources/historical/fia'
    inventory=json.loads((previous/'inventory.json').read_text());docs={}
    existing=set()
    for name in ['fia-documents.json','fia-legacy-documents.json']:
        if (STORE/name).exists():existing.update(d['url'] for d in json.loads((STORE/name).read_text()))
    for page in inventory['pages']:
        if not page.get('file'):continue
        html=BeautifulSoup((previous/page['file']).read_text(),'html.parser')
        headings=[h for h in page.get('headings',[]) if not re.fullmatch(r'Event.*(?:Information|information)',h)]
        event=headings[0] if headings else None
        if not event:continue
        event=re.sub(r'^\d{4}\s+|\s*[-–]?\s*Event\s*(?:&?\s*Timing)?\s*Information.*$','',event,flags=re.I).strip()
        for a in html.select('a[href]'):
            title=a.get_text(' ',strip=True);href=a['href']
            if re.search(r'/file/\d+/download|\.pdf(?:\?|$)',href,re.I) and re.search(r'decision|offence|infringement|summons|protest|review|penalt|reprimand|race classification|starting grid',title,re.I):
                url=urljoin(page['url'],href)
                if url not in existing:docs[url]={'year':page['year'],'event':event,'title':title,'url':url,'index_url':page['url'],'published':None}
    save(STORE/'extra-documents.json',list(docs.values()));print('Retained-page additional decisions',len(docs),flush=True)
    out=pooled(docs.values(),lambda d:{**d,'source':fetch(d['url'])},'Retained FIA PDFs')
    save(STORE/'extra-downloaded.json',out)


def documents():
    jobs={}
    for name in ['fia-documents.json','fia-legacy-documents.json','extra-documents.json']:
        if (STORE/name).exists():
            for d in json.loads((STORE/name).read_text()):jobs[d['url']]=d
    def document(d):return {**d,'source':fetch(d['url'])}
    out=pooled(jobs.values(),document,'FIA PDFs');save(STORE/'documents-downloaded.json',out)
    print('PDFs',sum(d['source'].get('kind')=='pdf' for d in out),'/',len(out),flush=True)


def results_notes():
    """Preserve official F1 result/grid footnotes, including older seasons.
    These supplement FIA rulings; they cannot replace all served penalties.
    """
    def year(y):
        url=f'https://www.formula1.com/en/results/{y}/races';p=fetch(url)
        links={urljoin(url,a['href']) for a in soup(p).select('a[href]') if re.search(rf'/en/results/{y}/races/\d+/[^/]+/race-result$',a['href'])}
        return [{'year':y,'url':u,'kind':kind} for u in links for kind in ['race-result','starting-grid','qualifying']]
    jobs=[j for row in pooled(range(2007,2027),year,'F1 result seasons') for j in row]
    def page(job):
        url=job['url'].replace('/race-result','/'+job['kind']);p=fetch(url);s=soup(p)
        table=s.select_one('table');notes=[]
        # Notes may be a div rather than a paragraph in newer result layouts.
        for el in s.find_all(['p','div']):
            if el.find(['p','div','table']):continue
            text=el.get_text(' ',strip=True)
            if 10<len(text)<6000 and re.search(r'penalt|disqualif|reprimand|\bNote\s*:',text,re.I) and 'cookie' not in text.lower():notes.append(text)
        heading=s.select_one('h1');return {**job,'url':url,'title':heading.get_text(' ',strip=True) if heading else '', 'source':p,'notes':list(dict.fromkeys(notes)),'has_table':bool(table)}
    out=pooled(jobs,page,'F1 official result notes');save(STORE/'official-results-notes.json',out)
    print('F1 pages with notes',sum(bool(r['notes']) for r in out),'/',len(out),flush=True)


def wayback():
    # Public CDX index only. Preserve unsuccessful lookups as coverage evidence.
    def year(y):
        u=f'https://web.archive.org/cdx/search/cdx?url=www.fia.com/events/fia-formula-one-world-championship/season-{y}/*&output=json&filter=statuscode:200&collapse=urlkey&filter=mimetype:text/html&limit=3000'
        p=fetch(u);records=[]
        try:
            raw=json.loads((STORE/p['file']).read_text());head=raw[0]
            for r in raw[1:]:
                r=dict(zip(head,r));original=r['original']
                if re.search(r'(?:event.*(?:information|timing)|timing.*information)',original,re.I):
                    records.append({'year':y,'original':original,'capture':r['timestamp']})
        except (KeyError,ValueError,IndexError):pass
        return {'year':y,'source':p,'pages':records}
    indexes=pooled(range(2007,2017),year,'Wayback indexes');save(STORE/'wayback-indexes.json',indexes)
    def page(job):
        original=job['original'];live=fetch(original);p=live
        if live.get('http_status')!=200:p=fetch(f"https://web.archive.org/web/{job['capture']}id_/{original}")
        s=soup(p);h=s.select_one('h1');event=h.get_text(' ',strip=True) if h else ''
        # Old titles can be just 'Event Information'; retain descriptive URL too.
        if len(event)<10 or not re.search(r'prix',event,re.I):event=original.rsplit('/',1)[-1].replace('-',' ')
        event=re.sub(r'^\d{4}\s+|\s*[-–]?\s*Event\s*(?:&?\s*Timing)?\s*Information.*$','',event,flags=re.I).strip()
        docs=[]
        for a in s.select('a[href]'):
            title=a.get_text(' ',strip=True);href=a['href']
            if re.search(r'/file/\d+/download|\.pdf(?:\?|$)',href,re.I) and re.search(r'decision|offence|infringement|summons|protest|review|penalt|reprimand|race classification|starting grid',title,re.I):
                href=re.sub(r'^https?://web.archive.org/web/\d+(?:[a-z_]+)?/','',href)
                docs.append({'year':job['year'],'event':event,'title':title,'url':urljoin(original,href),'index_url':p['url'],'published':None,'wayback_capture':job['capture']})
        return {**job,'source':p,'event':event,'documents':docs}
    pages=pooled([p for ix in indexes for p in ix['pages']],page,'Wayback pages');save(STORE/'wayback-pages.json',pages)
    existing={d['url'] for name in ['fia-documents.json','fia-legacy-documents.json','extra-documents.json'] if (STORE/name).exists() for d in json.loads((STORE/name).read_text())}
    docs={d['url']:d for p in pages for d in p['documents'] if d['url'] not in existing};save(STORE/'wayback-documents.json',list(docs.values()))
    def doc(d):
        src=fetch(d['url'])
        if src.get('kind')!='pdf':
            # Try the capture from the event page. A separate availability query
            # is retained when that snapshot has no matching archived document.
            archive=f"https://web.archive.org/web/{d['wayback_capture']}id_/{d['url']}"
            archived=fetch(archive)
            if archived.get('kind')=='pdf':src=archived
            else:
                avail=fetch('https://archive.org/wayback/available?url='+requests.utils.quote(d['url'],safe='')+'&timestamp='+d['wayback_capture'])
                try:
                    closest=json.loads((STORE/avail['file']).read_text())['archived_snapshots']['closest']
                    archived=fetch(closest['url'].replace('http://web.archive.org','https://web.archive.org').replace('/http','id_/http'))
                    if archived.get('kind')=='pdf':src=archived
                except (KeyError,ValueError):pass
        # Preserve the source actually retrieved while retaining original URL.
        out={**d,'source':src};save(STORE/'raw'/(hashlib.sha256(d['url'].encode()).hexdigest()+'.resolved.json'),out)
        return out
    out=pooled(docs.values(),doc,'Wayback additional PDFs');save(STORE/'wayback-downloaded.json',out)


def early_directories():
    # Before the modern Drupal site, FIA stored decisions in country-specific
    # /...gp/documents/ directories. A season-* search does not find these.
    countries={'australia':'Australian','australian':'Australian','malaysia':'Malaysian','malaysian':'Malaysian','bahrain':'Bahrain','spain':'Spanish','spanish':'Spanish','monaco':'Monaco','turkey':'Turkish','turkish':'Turkish','canada':'Canadian','canadian':'Canadian','usa':'United States','us':'United States','france':'French','french':'French','britain':'British','british':'British','germany':'German','german':'German','hungary':'Hungarian','hungarian':'Hungarian','europe':'European','european':'European','belgium':'Belgian','belgian':'Belgian','italy':'Italian','italian':'Italian','singapore':'Singapore','japan':'Japanese','japanese':'Japanese','china':'Chinese','chinese':'Chinese','brazil':'Brazilian','brazilian':'Brazilian','abudhabi':'Abu Dhabi','korea':'Korean','korean':'Korean','india':'Indian','indian':'Indian'}
    def directory(job):
        country,event=job;u=f'https://web.archive.org/cdx/search/cdx?url=www.fia.com/{country}gp/documents/*&output=json&filter=statuscode:200&collapse=urlkey&filter=mimetype:application/pdf&filter=original:.*(Doc|DOC|doc|decision|Decision).*&from=2007&to=2014&limit=2000';p=fetch(u);docs=[]
        try:
            raw=json.loads((STORE/p['file']).read_text());head=raw[0]
            for r in raw[1:]:
                r=dict(zip(head,r));original=r['original'];filename=original.rsplit('/',1)[-1]
                year=re.search(r'(?:_|-|%20)(0[7-9]|1[012])(?:_|-|%20)',filename)
                full=re.search(r'\b(20(?:0[7-9]|1[012]))\b',filename)
                y=int(full[1]) if full else 2000+int(year[1]) if year else None
                if y:docs.append({'year':y,'event':event+' Grand Prix','title':filename,'url':original,'index_url':u,'published':None,'wayback_capture':r['timestamp'],'archive_url':f"https://web.archive.org/web/{r['timestamp']}id_/{original}"})
        except (KeyError,ValueError,IndexError):pass
        return {'directory':country,'source':p,'documents':docs}
    indexes=pooled(countries.items(),directory,'Early FIA archive directories');save(STORE/'early-fia-indexes.json',indexes)
    docs={d['url']:d for ix in indexes for d in ix['documents']};save(STORE/'early-fia-documents.json',list(docs.values()));print('Early FIA decision documents',len(docs),flush=True)
    def doc(d):
        src=fetch(d['archive_url'])
        if src.get('kind')!='pdf':src=fetch(d['url'])
        out={**d,'source':src};save(STORE/'raw'/(hashlib.sha256(d['url'].encode()).hexdigest()+'.resolved.json'),out);return out
    out=pooled(docs.values(),doc,'Early FIA PDFs');save(STORE/'early-fia-downloaded.json',out)


def ocr_scans():
    from tempfile import TemporaryDirectory
    from build_incident_registry import document_jobs
    jobs={d['source']['sha256']:d['source'] for d in document_jobs() if d.get('source',{}).get('kind')=='pdf'}
    scans=[s for s in jobs.values() if not s.get('text_file') or len((STORE/s['text_file']).read_text(errors='replace').strip())<60]
    print('Image-only PDFs requiring OCR',len(scans),flush=True)
    def ocr(src):
        meta=STORE/'raw'/('content-text-'+src['sha256']+'.json')
        if meta.exists():return json.loads(meta.read_text())
        info=subprocess.run(['pdfinfo',str(STORE/src['file'])],capture_output=True,text=True)
        match=re.search(r'^Pages:\s*(\d+)',info.stdout,re.M);pages=int(match[1]) if match else 1
        last=min(pages,12);parts=[]
        with TemporaryDirectory(prefix='f1-ocr-') as temp:
            rendered=subprocess.run(['pdftoppm','-f','1','-l',str(last),'-r','160','-png',str(STORE/src['file']),temp+'/page'],stderr=subprocess.PIPE,text=True)
            if rendered.returncode:
                out={'text_method':'extraction_failed','text_extraction_error':rendered.stderr[:1000]};save(meta,out);return out
            for image in sorted(Path(temp).glob('page-*.png')):
                run=subprocess.run(['tesseract',str(image),'stdout','-l','eng','--psm','3'],capture_output=True,text=True,env={**__import__('os').environ,'OMP_THREAD_LIMIT':'1'})
                parts.append(run.stdout)
        text=STORE/'raw'/(src['sha256']+'.ocr.txt');text.write_text('\n\f\n'.join(parts))
        out={'text_file':str(text.relative_to(STORE)),'text_method':'tesseract_ocr','ocr_pages':last,'pdf_pages':pages,'ocr_truncated':last<pages};save(meta,out);return out
    out=pooled(scans,ocr,'OCR FIA scans');save(STORE/'ocr-audit.json',out)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('step',choices=['index','legacy','retained','documents','results','wayback','early','ocr','all']);args=ap.parse_args()
    if args.step in ('index','all'):index_fia()
    if args.step in ('legacy','all'):legacy_fia()
    if args.step=='retained':retained_fia()
    if args.step=='results':results_notes()
    if args.step=='wayback':wayback()
    if args.step=='early':early_directories()
    if args.step=='ocr':ocr_scans()
    if args.step in ('documents','all'):documents()
