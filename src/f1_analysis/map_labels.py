"""Shared collision-free label placement in an 800-unit display coordinate system."""
import math
import numpy as np


def segment_hits_box(a,b,box):
    lo=np.array(box[:2]);hi=np.array(box[2:]);a=np.array(a);delta=np.array(b)-a
    enter,leave=0.,1.
    for axis in range(2):
        if abs(delta[axis])<1e-12:
            if a[axis]<lo[axis] or a[axis]>hi[axis]:return False
        else:
            first,last=sorted(((lo[axis]-a[axis])/delta[axis],(hi[axis]-a[axis])/delta[axis]))
            enter=max(enter,first);leave=min(leave,last)
            if enter>leave:return False
    return True


def boxes_overlap(a,b):
    return a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]


def place_labels(track,items):
    """Reserve padded whole text rectangles, checking every track segment, not anchors."""
    xy=np.array([[p['x'],p['y']] for p in track]);minimum=xy.min(axis=0)
    scale=800/max(np.ptp(xy[:,0]),np.ptp(xy[:,1]),1)
    line=(xy-minimum)*scale
    placed=[]
    # Long labels first so short numbers can fit around them.
    for item in sorted(items,key=lambda item:-len(item['text'])):
        anchor=(np.array([item['x'],item['y']])-minimum)*scale
        width=max(34,len(item['text'])*11+16);height=34
        candidates=[]
        for radius in [35,55,80,110,150,210,290,400,550,750,1000,1400]:
            for step in range(24):
                angle=step*math.pi/12;direction=np.array([math.cos(angle),math.sin(angle)])
                # Position the nearest text edge beyond the anchor, with width-aware spacing.
                center=anchor+direction*(radius+abs(direction[0])*width/2+abs(direction[1])*height/2)
                box=[center[0]-width/2,center[1]-height/2,center[0]+width/2,center[1]+height/2]
                padded=[box[0]-12,box[1]-12,box[2]+12,box[3]+12]
                if any(boxes_overlap(padded,p['box']) for p in placed):continue
                if any(segment_hits_box(a,b,padded) for a,b in zip(line[:-1],line[1:])):continue
                candidates.append((float(np.linalg.norm(center-anchor)),center,box))
            if candidates:break
        if not candidates:raise ValueError('Geen vrije ruimte voor kaartannotatie: '+item['text'])
        _,center,box=min(candidates,key=lambda c:c[0])
        edge=np.clip(anchor,[box[0],box[1]],[box[2],box[3]])
        def raw(p):return {'x':float(p[0]/scale+minimum[0]),'y':float(p[1]/scale+minimum[1])}
        placed.append({**item,'text_position':raw(center),'leader_end':raw(edge),'box':box,
                       'display_box':{'xmin':raw(box[:2])['x'],'ymin':raw(box[:2])['y'],'xmax':raw(box[2:])['x'],'ymax':raw(box[2:])['y']}})
    return placed


def annotations(track,reference):
    from .location import display_point
    items=[]
    for c in reference.get('reference_corners',[]):
        label=str(c['number'])+(' · '+c['name']+(' (historisch)' if c.get('historical') else '') if c.get('name') else '')
        items.append({**display_point(c,reference),'text':label,'kind':'corner','color':'#f5f7fb'})
    for p in reference.get('pit_markers',[]):
        items.append({**display_point(p,reference),'text':p['label']+' ≈','kind':'pit','color':'#bd9cff'})
    if track:items.append({**track[0],'text':'Start / finish','kind':'start','color':'#51d6dd'})
    return place_labels(track,items) if track else []
