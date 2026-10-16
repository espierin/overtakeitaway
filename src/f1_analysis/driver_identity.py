"""Explicit identity aliases: spelling/name order must not split one career.

Do not infer identity from three-letter codes or by sorting name tokens: both
can also be shared by different people. Original source archives stay intact.
"""
from copy import deepcopy
import re
import unicodedata

ALIASES={'zhou-guanyu':'guanyu-zhou'}
NAMES={'guanyu-zhou':'Zhou Guanyu'}


def identity(name):
    text=unicodedata.normalize('NFKD',str(name)).encode('ascii','ignore').decode().lower()
    text=re.sub(r'\b(jnr|jr|junior)\b','',text)
    value=re.sub(r'[^a-z0-9]+','-',text).strip('-')
    return ALIASES.get(value,value)


def display_name(name):
    return NAMES.get(identity(name),name)


def _combine(a,b):
    """Deduplicate identical observations; merge missing fields, reject conflicts."""
    if a==b:return deepcopy(a)
    if a is None:return deepcopy(b)
    if b is None:return deepcopy(a)
    if isinstance(a,dict) and isinstance(b,dict):
        out=deepcopy(a)
        for k,v in b.items():out[k]=_combine(out[k],v) if k in out else deepcopy(v)
        return out
    raise ValueError('Conflicting observations for one driver/race; refusing to discard data')


def merge_profiles(data):
    """Canonicalise profile IDs and references, preserving every race datapoint."""
    groups={};race_meta={r['id']:r for r in data.get('races',[])}
    def order(row):
        race=race_meta.get(row['race'],{})
        return row.get('year',race.get('year',0)),race.get('date') or '',race.get('round') or 0,row['race']
    for profile in data.get('drivers',[]):
        p=deepcopy(profile);key=ALIASES.get(p['id'],p['id']);p.update(id=key,name=NAMES.get(key,p['name']))
        if key not in groups:groups[key]=p
        else:
            current=groups[key];rows={r['race']:r for r in current['races']}
            for row in p['races']:rows[row['race']]=_combine(rows[row['race']],row) if row['race'] in rows else row
            current['races']=list(rows.values())
    for p in groups.values():
        p['races'].sort(key=order)
        if p['races'] and p['id'] in NAMES:
            latest=p['races'][-1]
            p.update(number=latest.get('number',p.get('number')),color=latest.get('color',p.get('color')))
        for row in p['races']:
            comparison=row.get('comparison') or {}
            if comparison.get('teammate'):comparison['teammate']=display_name(comparison['teammate'])
            for key in ('retired_drivers','limiting_drivers'):
                if key in comparison:comparison[key]=[display_name(n) for n in comparison[key]]
            evidence=row.get('retirement_evidence')
            if evidence:evidence['id']=row['race']+':'+p['id']
    for cycle in data.get('cycles',[]):
        for key in ('driver','opponent'):
            if key in cycle:cycle[key]=ALIASES.get(cycle[key],cycle[key])
    data['drivers']=sorted(groups.values(),key=lambda p:p['name'])
    data['driver_aliases']={**data.get('driver_aliases',{}),**ALIASES}
    return data
