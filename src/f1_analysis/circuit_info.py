"""Wikipedia discovery, cached source text, and conservative circuit annotations."""
import re
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup
from .io import slug, write_json


def table_names(document):
    """Read explicitly paired number/name columns; never infer names from street names."""
    found=[]
    for table in document.select('table'):
        rows=table.find_all('tr')
        if not rows:continue
        headers=[c.get_text(' ',strip=True).lower() for c in rows[0].find_all(['th','td'],recursive=False)]
        number=next((i for i,h in enumerate(headers) if h in ['turn','corner','number','turn number','bocht','nummer']),None)
        name=next((i for i,h in enumerate(headers) if h in ['name','corner name','turn name','naam']),None)
        if number is None or name is None:continue
        for row in rows[1:]:
            cells=[c.get_text(' ',strip=True) for c in row.find_all(['td','th'],recursive=False)]
            if len(cells)<=max(number,name):continue
            match=re.fullmatch(r'(?:T|Turn\s*)?(\d{1,2})',cells[number],re.I)
            value=re.sub(r'\[\d+\]','',cells[name]).strip()
            if match and value and value not in ['—','–','-']:
                found.append({'number':int(match[1]),'name':value,'status':'kandidaat; jaarvariant nog controleren'})
    return found


def acquire_wikipedia(client,data,raw,source_config,warnings):
    circuit=data['session']['circuit_short_name']
    registry=next((v for k,v in source_config.get('circuit_annotations',{}).items() if slug(k)==slug(circuit)),{})
    data['circuit_annotation_config']=registry
    url=registry.get('wikipedia_url') or data.get('jolpica_circuit',{}).get('url')
    if url and urlparse(url).hostname in ['en.wikipedia.org','nl.wikipedia.org']:
        # Jolpica may still reference an http Wikipedia URL.
        url='https://'+urlparse(url).netloc+urlparse(url).path
    else:
        url=None
    try:
        if not url:
            results=client.fetch('https://en.wikipedia.org/w/api.php',params={'action':'query','list':'search','srsearch':circuit+' circuit','srlimit':5,'format':'json'},publisher='Wikipedia',title='Wikipedia: circuit zoeken')['query']['search']
            candidates=[r for r in results if any(w in r['title'].lower() for w in ['circuit','raceway','autodrom'])]
            if len(candidates)!=1:raise ValueError('Wikipedia-circuitzoekopdracht is niet eenduidig; geen artikel automatisch geselecteerd.')
            from urllib.parse import quote
            url='https://en.wikipedia.org/wiki/'+quote(candidates[0]['title'].replace(' ','_'))
        payload=client.fetch(url,kind='bytes',publisher='Wikipedia',title='Wikipedia: '+unquote(url.rsplit('/',1)[-1]).replace('_',' '),claims=['Bochtnamen en geschiedenis; jaarvariant moet afzonderlijk gecontroleerd worden'])
        target=raw/'supplementary'/'wikipedia-circuit.html';target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(payload)
        document=BeautifulSoup(payload,'html.parser')
        containers=document.select('.mw-parser-output')
        content=max(containers,key=lambda tag:len(tag.get_text())) if containers else document
        for tag in content.select('.navbox,.reflist,script,style'):tag.decompose()
        data['wikipedia_circuit']={'url':url,'available':True,'title':document.h1.get_text(' ',strip=True) if document.h1 else circuit,'text':content.get_text(' ',strip=True),'candidate_names':table_names(content)}
    except (ValueError,KeyError,TypeError) as exc:
        data['wikipedia_circuit']={'url':url,'available':False};warnings.append('Wikipedia-circuitcontrole: '+str(exc))
    write_json(raw/'supplementary'/'wikipedia-circuit.json',data['wikipedia_circuit'])


def annotate_reference(data,track,reference,warnings):
    """Apply only year-reviewed names to the corresponding numbered geometry."""
    wiki=data.get('wikipedia_circuit',{});year=data['session']['year']
    variant=next((v for v in data.get('circuit_annotation_config',{}).get('variants',[]) if v['first_year']<=year<=v['last_year']),None)
    anchors=reference.get('reference_corners',[])
    if not anchors:
        from .location import validated_corners
        anchors=validated_corners(track,data.get('circuit',{}),year)
        reference={**reference,'reference_corners':anchors}
    reference={**reference,'wikipedia_url':wiki.get('url'),'wikipedia_available':wiki.get('available',False),'pit_markers':[]}
    if not (variant and len(anchors)==variant['corner_count']):
        warnings.append('Geen gecontroleerde koppeling van Wikipedia-bochtnamen en pit-in/out aan deze jaarvariant; beschikbare bochtnummers blijven zichtbaar.')
        return reference
    if wiki.get('available'):
        names={n['number']:n for n in variant.get('names',[]) if n['name'].casefold() in wiki.get('text','').casefold()}
        reference['reference_corners']=[{**c,**({'name':names[c['number']]['name'],'historical':names[c['number']].get('historical',False),'name_source_url':wiki['url']} if c['number'] in names else {})} for c in anchors]
    pit_url=variant.get('pit_source_url')
    available=any(s.get('available') and s['url']==pit_url and s.get('year')==year for s in data.get('evidence',[]))
    if available:
        numbered={c['number']:c for c in anchors}
        for zone in variant.get('pit_zones',[]):
            a=numbered.get(zone['after_turn']);b=numbered.get(zone['before_turn'])
            if not a or not b:continue
            progress=(a['progress']+((b['progress']-a['progress'])%1)*zone['fraction'])%1
            point=track[int(round(progress*(len(track)-1)))%(len(track)-1)]
            reference['pit_markers'].append({**point,'progress':progress,**zone,'source_url':pit_url,'source_title':variant['pit_source_title'],'accuracy':'indicatieve zone op hoofdbaan; geen gemeten pitlane-geometrie'})
    return reference
