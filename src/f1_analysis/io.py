from __future__ import annotations
import csv, gzip, hashlib, json, time, unicodedata, subprocess
from datetime import datetime, timezone
from pathlib import Path
import requests


def public_api_slot(root, interval):
    """Share OpenF1's request spacing across simultaneous season builders."""
    import fcntl
    target=Path(root)/'cache/openf1-request.lock';target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('a+') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX)
        handle.seek(0);previous=handle.read().strip()
        delay=max(0,float(interval)-(time.time()-float(previous or 0)))
        if delay:time.sleep(delay)
        handle.seek(0);handle.truncate();handle.write(str(time.time()));handle.flush()


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def read_json(path):
    path=Path(path)
    if path.exists():return json.loads(path.read_text(encoding='utf-8'))
    return json.loads(gzip.decompress(path.with_name(path.name+'.gz').read_bytes()))


def slug(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii','ignore').decode().lower()
    return '-'.join(value.split())


def write_csv(path, rows):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text('event_id\n'); return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fields); writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()})


class Client:
    """URL-geadresseerde cache; fouten blijven fouten en worden niet als [] gecachet."""
    def __init__(self, root, config, offline=False, refresh=False):
        self.root = Path(root); self.config=config; self.offline=offline; self.refresh=refresh
        self.sources=[]; self.last_request=0; self.session=requests.Session()
        self.session.headers['User-Agent']='LocalF1Analysis/0.1 (historical research)'

    def fetch(self, url, params=None, kind='json', title=None, publisher='OpenF1', claims=None):
        full = requests.Request('GET', url, params=sorted((params or {}).items())).prepare().url
        key=hashlib.sha256(full.encode()).hexdigest()
        target=self.root/'cache'/key
        metadata=target.with_suffix('.meta.json'); body=target.with_suffix('.body')
        entry={'title':title or full, 'url':full, 'publisher':publisher, 'claims':claims or [], 'kind':kind}
        if body.exists() and metadata.exists() and (self.offline or not self.refresh):
            entry.update(read_json(metadata)); entry['cache_used']=True
            data=body.read_bytes()
            self.sources.append(entry)
            return json.loads(data) if kind=='json' else data
        if self.offline:
            entry.update(status='ontbreekt in cache', fetched_at=None); self.sources.append(entry)
            raise ValueError('Bron ontbreekt in cache: '+full)
        for attempt in range(self.config.get('retries',4)):
            elapsed=time.monotonic()-self.last_request
            time.sleep(max(0,self.config.get('request_interval_seconden',1.1)-elapsed))
            try:
                if full.startswith('https://api.openf1.org/'):
                    public_api_slot(self.root,max(2.1,self.config.get('request_interval_seconden',2.1)))
                self.last_request=time.monotonic()
                response=self.session.get(full,timeout=(15,90))
                if response.status_code in [429,500,502,503,504]:
                    delay=response.headers.get('Retry-After','')
                    time.sleep(min(45,float(delay) if delay.isdigit() else 2**(attempt+1)))
                    response.raise_for_status()
                response.raise_for_status()
                data=response.content
                parsed=json.loads(data) if kind=='json' else data
                body.parent.mkdir(parents=True,exist_ok=True); body.write_bytes(data)
                entry.update(fetched_at=utcnow(), sha256=hashlib.sha256(data).hexdigest(),status='opgehaald')
                write_json(metadata,entry); self.sources.append(entry)
                return parsed
            except (requests.RequestException, ValueError) as exc:
                error=str(exc)
                # A second ordinary HTTP implementation can recover protocol resets; never use it for access denials.
                if isinstance(exc,requests.ConnectionError):
                    try:
                        fallback=subprocess.run(['curl','--silent','--show-error','--fail','--location','--max-time','60',full],capture_output=True,timeout=65)
                        if fallback.returncode==0:
                            data=fallback.stdout
                            parsed=json.loads(data) if kind=='json' else data
                            body.parent.mkdir(parents=True,exist_ok=True);body.write_bytes(data)
                            entry.update(fetched_at=utcnow(),sha256=hashlib.sha256(data).hexdigest(),status='opgehaald',access_method='openbare HTTP-download via curl na verbindingsfout')
                            write_json(metadata,entry);self.sources.append(entry);return parsed
                    except (OSError,subprocess.TimeoutExpired,ValueError):pass
                if getattr(getattr(exc,'response',None),'status_code',None) in [400,401,403,404]:break
                if attempt+1<self.config.get('retries',4):time.sleep(2**attempt)
        entry.update(status='onbereikbaar',error=error,fetched_at=utcnow());self.sources.append(entry)
        raise ValueError('Bron niet opgehaald: '+full+' — '+error)

    def api(self, endpoint, **params):
        return self.fetch('https://api.openf1.org/v1/'+endpoint,params,title='OpenF1: '+endpoint)


ALIASES={'nederland':'netherlands','dutch gp':'netherlands','dutch':'netherlands','zandvoort':'netherlands',
         'singapore':'singapore','singapur':'singapore','marina bay':'singapore',
         'belgie':'belgium','spa':'belgium','groot-brittannie':'united kingdom','silverstone':'united kingdom',
         'monza':'monza','italie':'monza','imola':'imola','las vegas':'las vegas','miami':'miami','austin':'austin'}


def select_race(sessions, query):
    normalized=lambda value:slug(str(value)).replace('-',' ')
    aliases={normalized(k):normalized(v) for k,v in ALIASES.items()}
    needle=aliases.get(normalized(query),normalized(query))
    races=[s for s in sessions if s['session_name']=='Race' and not s.get('is_cancelled')]
    exact=[s for s in races if normalized(s.get('circuit_short_name',''))==normalized(query)]
    if len(exact)==1:return exact[0]
    matches=[s for s in races if needle in ' '.join(normalized(s.get(k,'')) for k in ['country_name','location','circuit_short_name','meeting_name'])]
    if not matches:raise ValueError('Geen hoofdrace gevonden voor '+query+'. Gebruik races --year voor beschikbare namen.')
    if len(matches)>1:raise ValueError('Dubbelzinnige Grand Prix: '+', '.join(s['location'] for s in matches))
    return matches[0]
