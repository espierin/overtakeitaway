from __future__ import annotations
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import html, json, math
from urllib.parse import unquote, urlparse, quote
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.ticker import MaxNLocator
from .driver_style import driver_styles
import numpy as np
from bs4 import BeautifulSoup
from .analysis import ts, Context
from .io import write_json, read_json

BG='#10141d';PANEL='#181f2c';TEXT='#f5f7fa';MUTED='#b3bece';RED='#ff4b56';CYAN='#51d6dd'
COMPOUND_LABELS={'SOFT':'zacht','MEDIUM':'middel','HARD':'hard','INTERMEDIATE':'intermediate','WET':'regen'}
COMPOUNDS={'SOFT':RED,'MEDIUM':'#edc65b','HARD':'#e4e9ef','INTERMEDIATE':'#66cc8e','WET':'#579cf1'}
plt.rcParams.update({'figure.facecolor':BG,'axes.facecolor':PANEL,'axes.edgecolor':'#596273','axes.labelcolor':TEXT,
                    'text.color':TEXT,'xtick.color':MUTED,'ytick.color':MUTED,'grid.color':'#596273','grid.alpha':.23,
                    'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                    'savefig.facecolor':BG,'svg.fonttype':'none'})
CSS='''body{background:#10141d;color:#f5f7fa;font:16px/1.65 system-ui,sans-serif;max-width:1350px;margin:auto;padding:38px}a{color:#51d6dd}h1{font-size:40px}h2{border-top:1px solid #343f50;padding-top:24px}p,li{max-width:1050px}.tag{color:#ff737c}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:24px}.card{background:#181f2c;padding:24px;border-radius:10px}img{width:100%;height:auto}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:9px;border-bottom:1px solid #343f50;text-align:left}pre{white-space:pre-wrap}nav{display:flex;flex-wrap:wrap;gap:18px}.muted{color:#b3bece}code{background:#181f2c;padding:2px 6px}button,input,select{background:#181f2c;color:white;padding:8px;border:1px solid #596273;border-radius:4px}svg{max-height:650px;width:100%}'''


def page(title,body):return '<!doctype html><html lang="nl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>'+CSS+'</style><body>'+body+'</body></html>'


def compound_label(value):return COMPOUND_LABELS.get(value,str(value))


def val(v,digits=2):
    if isinstance(v,str):
        for code,label in COMPOUND_LABELS.items():v=v.replace(code,label)
        return v.replace('_',' ')
    return 'onbekend' if v is None else f'{v:.{digits}f}'.replace('.',',') if isinstance(v,float) else str(v)


def table(headers,rows):
    return '\n|'+'|'.join(headers)+'|\n|'+'|'.join(['---']*len(headers))+'|\n'+''.join('|'+'|'.join(str(val(x)).replace('|','/').replace('\n',' ') for x in row)+'|\n' for row in rows)+'\n'


def markdown_html(text):
    # Small offline Markdown subset used by these factual report templates.
    lines=text.splitlines();out=[];i=0
    import re
    def inline(s):
        s=html.escape(s)
        return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',s)
    while i<len(lines):
        line=lines[i]
        if line.startswith('|'):
            block=[]
            while i<len(lines) and lines[i].startswith('|'):block.append(lines[i]);i+=1
            out.append('<div style="overflow:auto"><table><thead><tr>'+''.join('<th>'+inline(x.strip())+'</th>' for x in block[0].strip('|').split('|'))+'</tr></thead><tbody>')
            for row in block[2:]:out.append('<tr>'+''.join('<td>'+inline(x.strip())+'</td>' for x in row.strip('|').split('|'))+'</tr>')
            out.append('</tbody></table></div>');continue
        if line.startswith('#'):
            n=len(line)-len(line.lstrip('#'));out.append(f'<h{n}>'+inline(line[n:].strip())+f'</h{n}>')
        elif line.startswith('- '):out.append('<p>• '+inline(line[2:])+'</p>')
        elif line:out.append('<p>'+inline(line)+'</p>')
        i+=1
    return ''.join(out)


def save_figure(run,name,fig,method='OpenF1 • eigen lopende ronde • ronde 1 apart'):
    fig.text(.015,.012,method,color=MUTED,fontsize=8)
    for ext in ['png','svg']:
        p=run/'figures'/ext/(name+'.'+ext);p.parent.mkdir(parents=True,exist_ok=True)
        fig.savefig(p,dpi=180)
    plt.close(fig)


def plotting(run,b,only=None):
    s=b['stats'];events=b['events'];ds=b['drivers'];data=b['data'];names={d['driver_number']:d['code'] for d in ds}
    styles=driver_styles(data['drivers']);names={d:style['label'] for d,style in styles.items()}
    def integer_axis(ax,axis='both'):
        if axis in ['x','both']:ax.xaxis.set_major_locator(MaxNLocator(integer=True,min_n_ticks=1))
        if axis in ['y','both']:
            ax.yaxis.set_major_locator(MaxNLocator(integer=True,min_n_ticks=1));ax.set_ylim(0,max(1,ax.get_ylim()[1]))
    def badges(labels,rows):
        for label,row in zip(labels,rows):
            label.set_color(styles[row['driver_number']]['color']);label.set_fontweight('bold');label.set_fontstyle('italic')
            label.set_bbox(dict(boxstyle='round,pad=.2',facecolor=BG,edgecolor=styles[row['driver_number']]['color'],linewidth=.8))
    ctx=Context(data,b['config']);selected=[e for e in events if e['counts']['analytical']]
    n=s['lap_count'];plots=[]
    def make(name,title,draw,size=(14,7)):
        if only is not None and name not in only:return
        fig,ax=plt.subplots(figsize=size);draw(ax)
        is_map=name in ['circuitheatmap','startacties-kaart']
        if is_map:fig.suptitle(title.replace(' • ','\n'),x=.04,ha='left',fontsize=19)
        else:ax.set_title(title,loc='left',fontsize=19,pad=18)
        fig.tight_layout(rect=[0,.12 if is_map else .04,1,.88 if is_map else .97]);save_figure(run,name,fig,method=data.get('timing_source','OpenF1')+' • eigen lopende ronde • ronde 1 apart');plots.append((name,title))
    def perlap(ax):
        if n<2:
            ax.text(.5,.5,'Geen geclassificeerde ronden vanaf ronde 2',ha='center',va='center',transform=ax.transAxes);ax.set_axis_off();return
        ax.bar([int(k) for k in s['per_lap']],[v for v in s['per_lap'].values()],color=RED,width=.85)
        ax.axvspan(s['late_start']-.5,n+.5,color=CYAN,alpha=.08,label=f"Slotfase {s['late_start']}–{n}")
        ax.set(xlabel='Eigen ronde inhalende coureur',ylabel='Analytisch geselecteerde acties',xlim=(1.5,n+.5));ax.grid(axis='y');ax.legend();integer_axis(ax)
    make('acties-per-ronde','Inhaalacties vanaf ronde 2',perlap)
    def bydriver(ax):
        codes=[names[d['driver_number']] for d in ds];x=np.arange(len(codes));colors=[styles[d['driver_number']]['color'] for d in ds]
        ax.bar(x-.18,[s['made'].get(d['driver_number'],s['made'].get(str(d['driver_number']),0)) for d in ds],width=.36,color=colors,label='Uitgevoerd')
        ax.bar(x+.18,[s['received'].get(d['driver_number'],s['received'].get(str(d['driver_number']),0)) for d in ds],width=.36,facecolor='none',edgecolor=colors,hatch='...',linewidth=1.2,label='Ondergaan')
        ax.set_xticks(x,[]);ax.set_ylabel('Acties vanaf ronde 2');ax.legend();ax.grid(axis='y');integer_axis(ax,'y')
        tops=[]
        for i,row in enumerate(ds):
            d=row['driver_number'];top=max(s['made'].get(d,s['made'].get(str(d),0)),s['received'].get(d,s['received'].get(str(d),0)));tops.append(top)
            label=f"{d} {row['name'].split()[-1].title()}"
            ax.annotate(label,(i,top),xytext=(0,6),textcoords='offset points',ha='left',va='bottom',rotation=90,fontsize=8,fontweight='bold',fontstyle='italic',color=styles[d]['color'])
        ax.set_ylim(0,max(tops,default=0)+max(3,max(tops,default=0)*.35))
    make('acties-per-coureur','Acties uitgevoerd en ondergaan per coureur',bydriver)
    def bypair(ax):
        pairs=Counter((e['overtaker'],e['overtaken']) for e in selected)
        ordered=sorted(pairs,key=lambda pair:(-pairs[pair],pair))
        if not ordered:ax.text(.5,.5,'Geen geselecteerde inhaalparen',ha='center',transform=ax.transAxes);ax.set_axis_off();return
        labels=[f"{a} {next(d['name'].split()[-1].title() for d in ds if d['driver_number']==a)} → {z} {next(d['name'].split()[-1].title() for d in ds if d['driver_number']==z)}" for a,z in ordered]
        ax.bar(range(len(ordered)),[pairs[p] for p in ordered],color=[styles[a]['color'] for a,z in ordered])
        ax.set_xticks(range(len(ordered)),labels,rotation=90);ax.set_ylabel('Geselecteerde acties vanaf ronde 2');integer_axis(ax,'y');ax.grid(axis='y')
        for label,(a,z) in zip(ax.get_xticklabels(),ordered):label.set_color(styles[a]['color']);label.set_fontweight('bold')
    make('wie-passeert-wie','Wie passeert wie • inhaler → ingehaalde',bypair,size=(max(15,len(Counter((e['overtaker'],e['overtaken']) for e in selected))*.48),10))
    def positions(ax):
        for row in ds:
            d=row['driver_number'];x=[];y=[]
            if row['grid']:x.append(0);y.append(row['grid'])
            for l in ctx.laps.get(d,[]).rows:
                if l.get('date_start') and l.get('lap_duration'):
                    p=ctx.position(d,ts(l['date_start'])+l['lap_duration']-.001)
                    if p:x.append(l['lap_number']);y.append(p)
            ax.plot(x,y,lw=1.7,alpha=.95,color=styles[d]['color'],linestyle=styles[d]['linestyle'],label=names[d])
        ax.invert_yaxis();ax.set(xlabel='Eigen voltooide ronde',ylabel='Gemeten racepositie');ax.set_yticks(range(1,len(ds)+1));integer_axis(ax,'x');ax.grid();ax.legend(ncol=5,fontsize=8,loc='upper center',bbox_to_anchor=(.5,-.1))
    make('positieverloop','Posities door de race',positions,size=(16,9))
    def firstlap(ax):
        y=np.arange(len(ds));grid=[d['grid'] or np.nan for d in ds];end=[d['lap1_position'] or np.nan for d in ds]
        colors=[styles[d['driver_number']]['color'] for d in ds]
        ax.hlines(y,grid,end,color=colors);ax.scatter(grid,y,c=colors,s=55,marker='s',label='Startgrid');ax.scatter(end,y,facecolors='none',edgecolors=colors,s=55,marker='o',label='Einde eigen ronde 1')
        ax.set_yticks(y,[names[d['driver_number']]+(' • pitlane' if d['pitlane_start'] else '') for d in ds]);ax.invert_yaxis();ax.set_xticks(range(1,len(ds)+1));ax.set_xlabel('Positie — pitlanestarters hebben geen numerieke gridplek');ax.grid(axis='x');ax.legend();badges(ax.get_yticklabels(),ds)
    make('ronde-1','Start versus einde ronde 1',firstlap,size=(13,10))
    def stints(ax):
        for i,d in enumerate(ds):
            for st in b['tyres']['stints']:
                if st['driver_number']==d['driver_number'] and st.get('length'):
                    ax.barh(i,st['length'],left=st['lap_start']-.5,color=COMPOUNDS.get(st['compound'],CYAN),height=.65,edgecolor=BG)
                    if st['length']>=6:ax.text(st['lap_start']+st['length']/2-.5,i,st['compound'][0],ha='center',va='center',color=BG,fontsize=9,fontweight='bold')
        ax.set_yticks(range(len(ds)),[names[d['driver_number']] for d in ds]);badges(ax.get_yticklabels(),ds);ax.invert_yaxis();integer_axis(ax,'x');ax.set(xlabel='Ronde',xlim=(.5,n+.5));ax.grid(axis='x')
        from matplotlib.patches import Patch
        ax.legend(handles=[Patch(color=c,label=compound_label(k).capitalize()) for k,c in COMPOUNDS.items() if k in [st['compound'] for st in b['tyres']['stints']]],ncol=3)
    make('bandenstints','Bandenstrategie per coureur',stints,size=(15,10))
    def pace(ax):
        for row in ds[:8]:
            d=row['driver_number'];clean=[r for r in b['tyres']['clean_laps'] if r['driver']==d]
            ordered=sorted(clean,key=lambda r:r['lap'])
            ax.plot([r['lap'] for r in ordered],[r['duration'] for r in ordered],lw=.9,color=styles[d]['color'],linestyle=styles[d]['linestyle'],alpha=.55)
            ax.scatter([r['lap'] for r in ordered],[r['duration'] for r in ordered],s=13,color=styles[d]['color'],marker=styles[d]['marker'],alpha=.9,label=names[d])
        ax.set(xlabel='Ronde',ylabel='Geschikte rondetijd (seconden)');integer_axis(ax,'x');ax.grid();ax.legend(ncol=4)
    make('rondetijden','Tempo op geschikte ronden • eerste acht in de uitslag',pace)
    def cycles(ax):
        cs=b['cycles']
        if not cs:ax.text(.5,.5,'Geen afgeronde, vergelijkbare pitstopcycli vastgesteld',ha='center',transform=ax.transAxes);ax.set_axis_off();return
        labels=[f"{names.get(c['early_driver'])}/{names.get(c['late_driver'])}\n{c['early_stop_lap']}→{c['late_stop_lap']}" for c in cs]
        ax.bar(range(len(cs)),[c['gain_early_driver'] for c in cs],color=[styles[c['early_driver']]['color'] for c in cs]);ax.axhline(0,color=MUTED,lw=.8)
        ax.set_xticks(range(len(cs)),labels,rotation=40,ha='right',fontsize=8);ax.set_ylabel('Netto tijdwinst vroegst stoppende coureur (s)');ax.grid(axis='y')
    make('undercut-overcut','Pitstopcycli na beide stops én outlaps',cycles,size=(max(14,min(40,len(b['cycles'])*.65)),8))
    for c in b['cycles']:
        if c['cycle_id'] not in b['exported_cycle_ids']:continue
        def detail(ax,c=c):
            ax.plot([r['lap'] for r in c['trace']],[r['gap'] for r in c['trace']],color=styles[c['early_driver']]['color'],linestyle=styles[c['early_driver']]['linestyle'],marker=styles[c['early_driver']]['marker'],ms=4,label=names[c['early_driver']]+' — tijdsverschil')
            ax.axvline(c['early_stop_lap'],color=styles[c['early_driver']]['color'],ls=styles[c['early_driver']]['linestyle'],label='Stop '+names[c['early_driver']]);ax.axvline(c['late_stop_lap'],color=styles[c['late_driver']]['color'],ls=styles[c['late_driver']]['linestyle'],label='Stop '+names[c['late_driver']]);ax.axvline(c['completed_lap'],color=CYAN,ls=':',label='Beoordeling na outlaps');ax.axhline(0,color=TEXT,lw=.6)
            ax.set(xlabel='Gelijke voltooide ronde',ylabel=f"{names[c['early_driver']]} achter {names[c['late_driver']]} (s)");integer_axis(ax,'x');ax.grid();ax.legend()
        make('pitcyclus-'+c['cycle_id'],f"{names[c['early_driver']]} / {names[c['late_driver']]} • {c['status']}",detail)
    for is_lap1,name,title in [(False,'circuitheatmap','Inhaalzones vanaf ronde 2'),(True,'startacties-kaart','Startacties in ronde 1')]:
        def mapdraw(ax,is_lap1=is_lap1):
            track=b['track'];es=[e for e in events if e['counts']['lap1'] if is_lap1] if is_lap1 else selected
            loc=[e for e in es if e.get('location')]
            if track:
                from .location import display_point
                reference=data.get('circuit_reference',{})
                display=[display_point(p,reference) for p in track]
                xy=np.array([[p['x'],p['y']] for p in display]);segments=np.stack([xy[:-1],xy[1:]],axis=1)
                bins=np.zeros(b['config']['heatmap_segmenten'])
                for e in loc:bins[min(len(bins)-1,int(e['location']['progress']*len(bins)))]+=1
                heat=np.array([bins[min(len(bins)-1,int(i/(len(track)-1)*len(bins)))] for i in range(len(track)-1)])
                ax.plot(xy[:,0],xy[:,1],lw=7,color='#526179');lc=LineCollection(segments,cmap='hot',linewidths=5);lc.set_array(np.ma.masked_where(heat==0,heat));lc.set_clim(0,max(1,float(max(heat))));ax.add_collection(lc);ax.autoscale();ax.set_aspect('equal');ax.set_axis_off()
                # Samples retain chronological lap order, so arrow direction follows the race.
                for progress in [.18,.46,.73]:
                    i=int(progress*(len(xy)-1));j=min(i+7,len(xy)-1)
                    ax.annotate('',xy=xy[j],xytext=xy[i],arrowprops=dict(arrowstyle='->',color=TEXT,lw=2,mutation_scale=15))
                tangent=xy[2]-xy[0];normal=np.array([-tangent[1],tangent[0]])/np.linalg.norm(tangent)*130
                ax.plot([xy[0,0]-normal[0],xy[0,0]+normal[0]],[xy[0,1]-normal[1],xy[0,1]+normal[1]],color=CYAN,lw=3)
                from .map_labels import annotations
                labels=annotations(display,reference)
                for marker in reference.get('pit_markers',[]):
                    p=display_point(marker,reference)
                    ax.scatter([p['x']],[p['y']],marker='D',s=35,color='#bd9cff',zorder=6)
                for label in labels:
                    pos=label['text_position'];edge=label['leader_end']
                    ax.plot([label['x'],edge['x']],[label['y'],edge['y']],color=label['color'],lw=.6,alpha=.65,zorder=2)
                    ax.text(pos['x'],pos['y'],label['text'],ha='center',va='center',fontsize=10,color=label['color'],zorder=7)
                bounds=[label['display_box'] for label in labels]
                margin=max(np.ptp(xy[:,0]),np.ptp(xy[:,1]))*.04
                ax.set_xlim(min([xy[:,0].min()]+[q['xmin'] for q in bounds])-margin,max([xy[:,0].max()]+[q['xmax'] for q in bounds])+margin)
                ax.set_ylim(min([xy[:,1].min()]+[q['ymin'] for q in bounds])-margin,max([xy[:,1].max()]+[q['ymax'] for q in bounds])+margin)
                ax.figure.text(.03,.035,'Pijlen: rijrichting · cyaan: start/finish · paars ≈: indicatieve pit-in/out-zone · namen: Wikipedia indien beschikbaar',color=MUTED,fontsize=8)
                cb=ax.figure.colorbar(lc,ax=ax,shrink=.6,pad=.02);cb.set_label('Aantal per booglengtesegment');cb.locator=MaxNLocator(integer=True,min_n_ticks=1);cb.update_ticks()
            else:ax.text(.5,.5,'Circuitlocatiegegevens ontbreken',ha='center',transform=ax.transAxes);ax.set_axis_off()
            ax.figure.text(.03,.065,f'{len(loc)} van {len(es)} acties met bruikbare zone • {len(es)-len(loc)} onbekend\nGemeten baanvorm; officiële jaarvariant gecontroleerd indien vermeld; zones, geen exacte punten',color=MUTED,fontsize=9)
        make(name,title+(' • officiële jaarvariant '+str(data['session']['year']) if data.get('circuit_reference',{}).get('source_url') else ' • jaarvariant niet officieel gecontroleerd'),mapdraw,size=(14,9))
    # Exact requested export: 19.2 × 10.8 inches at 200 DPI.
    fig=plt.figure(figsize=(19.2,10.8));gs=fig.add_gridspec(2,3,height_ratios=[2,1.5],hspace=.4,wspace=.27)
    fig.text(.045,.94,f"{data['session']['circuit_short_name'].upper()}  {data['session']['year']}",fontsize=31 if len(data['session']['circuit_short_name'])<24 else 20,fontweight='bold')
    fig.text(.045,.887,'GRAND PRIX • CONTROLEERBARE RACEANALYSE',fontsize=13,color=MUTED)
    fig.text(.71,.943,f"{s['analytical']}  ACTIES",fontsize=31,color=RED,fontweight='bold')
    fig.text(.71,.899,f"Vanaf ronde 2 • {s['on_track']} in basistelling • {s.get('timing_original',s['openf1_original'])} bronregistraties",fontsize=10,color=MUTED)
    axes=[fig.add_subplot(gs[0,i]) for i in range(3)]
    podium=ds[:3]
    axes[0].set_axis_off();axes[0].set_title('PODIUM',loc='left',fontsize=16)
    for i,d in enumerate(podium):axes[0].text(.04,.78-i*.25,f"{i+1}   {names[d['driver_number']]}  {d['name'].title()}\n     {d['team']}",transform=axes[0].transAxes,fontsize=16 if i==0 else 13,color=styles[d['driver_number']]['color'])
    perlap(axes[1]);axes[1].set_title('ACTIES PER RONDE',loc='left',fontsize=16);axes[1].legend(fontsize=8)
    axes[2].set_axis_off();axes[2].set_title('DEKKING & SLOTFASE',loc='left',fontsize=16)
    late_percent=f"{s['late_fraction']*100:.1f}%" if s['late_fraction'] is not None else 'onbekend'
    text=f"{s['late_count']} van {s['analytical']} acties\nRonde {s['late_start']}–{s['late_end']} • {late_percent}\n\n{s['lap1_changes']} startregistraties apart\n{s['laps_with']} ronden met acties / {s['denominator']}\n\nKaart: {b['mapping']['located']} zones; {b['mapping']['unknown']} onbekend\nF1gures: {str(s['f1gures_original'])+' bronpassages' if data.get('f1gures') else 'gebeurtenissen ontbreken'}\nBronvariant na technische uitsluiting: {s.get('f1gures_comparison',{}).get('excluding_technical','onbekend') if data.get('f1gures') else 'onbekend'}\nStatus: gedeeltelijk"
    axes[2].text(.02,.83,text,transform=axes[2].transAxes,fontsize=13,va='top',linespacing=1.6)
    ax=fig.add_subplot(gs[1,:2]);bydriver(ax);ax.set_title('UITGEVOERD EN ONDERGAAN',loc='left',fontsize=15)
    ax=fig.add_subplot(gs[1,2]);ax.set_axis_off();ax.set_title('METHODE',loc='left',fontsize=15)
    ax.text(.02,.85,'Eén gebeurtenissenlijst voor alle totalen.\nPitlane, neutralisatie en timingruis apart.\nRonde van inhalende coureur gebruikt.\nTeamwisselingen zichtbaar uitgesloten.\nTechnisch positieverlies blijft in basis.\nLocaties zijn zones uit tijdvensters.\n\nBronnen: '+data.get('timing_source','OpenF1')+'; aanvullende bronnen\nin het bronregister. Zie de gebeurtenissenlijst.',transform=ax.transAxes,va='top',fontsize=11,linespacing=1.7)
    fig.subplots_adjust(left=.045,right=.965,bottom=.075,top=.80)
    p=run/'figures/png/hoofdinfographic.png';fig.savefig(p,dpi=200);fig.savefig(run/'figures/svg/hoofdinfographic.svg');plt.close(fig)
    plots.insert(0,('hoofdinfographic','Hoofdinfographic • 3840 × 2160'))
    return plots


def reports(b):
    s=b['stats'];data=b['data'];ds=b['drivers'];events=b['events'];names={d['driver_number']:d['code'] for d in ds}
    selected=[e for e in events if e['counts']['analytical']]
    session=data['session'];prefix=f"{session['circuit_short_name']} {session['year']}"
    source_links='\n'.join('- ['+r['title']+']('+r['url']+') — '+r['publisher']+'; '+r['type']+'; '+('opgehaald' if r['available'] else 'niet lokaal opgehaald') for r in data.get('evidence',[]))
    winner=ds[0]['name'].title() if ds else 'onbekend'
    header=f"# Raceanalyse — {prefix}\n\nStatus: gedeeltelijk. Datum: {session['date_start'][:10]}. Circuit: {session['location']}. Hoofdrace, sessie {session['session_key']}.\n"
    start=datetime.fromtimestamp(b['start'],timezone.utc).isoformat() if b['start'] else 'onbekend'
    header+=f"\nGecontroleerde racestart: {start}. Sessiestatus en rondegegevens {'stemmen overeen' if b['start_confirmed'] else 'geven geen onafhankelijke startbevestiging'}. Geplande sessiestart is geen startbewijs.\n"
    header+=f"\n## Uitslag en positieontwikkeling\n\n{winner} staat eerste in de opgeslagen eindclassificatie. {s['lap_count']} ronden voor de winnaar. Netto verandering meet grid versus classificatie; pitlane en straffen vragen aparte context.\n"
    header+=table(['Coureur','Team','Grid','Ronde 1','Uitslag','Netto winst','Startband','Status'],[[d['name'].title(),d['team'],'pitlane' if d['pitlane_start'] else d['grid'],d['lap1_position'],d['finish'],d['net_gain'],d['start_compound'],'uitgevallen' if d['result'].get('dnf') else 'niet gestart' if d['result'].get('dns') else 'geclassificeerd'] for d in ds])
    gains=sorted([d for d in ds if d['net_gain'] is not None],key=lambda d:d['net_gain'],reverse=True)
    if gains:header+=f"\nGrootste netto gridwinst: {gains[0]['code']} ({gains[0]['net_gain']:+d}); grootste netto verlies: {gains[-1]['code']} ({gains[-1]['net_gain']:+d}). Dit zijn geen aantallen inhaalmanoeuvres.\n"
    header+=f"\n## Racefasen en gevechten\n\nDe feed registreert {s.get('timing_original',s['openf1_original'])} wisselingen inclusief start en pitcontext. De basistelling op de baan vanaf ronde 2 is {s['on_track']}; de aanvullende telling selecteert {s['analytical']}. De slotfase omvat ronde {s['late_start']}–{s['late_end']} ({s['late_count']} geselecteerde acties). De noemer van gemiddelde acties is {s['denominator']} ronden.\n"
    thirds=[(2,max(2,math.ceil(s['lap_count']/3))), (max(2,math.ceil(s['lap_count']/3)+1),math.ceil(2*s['lap_count']/3)),(math.ceil(2*s['lap_count']/3)+1,s['lap_count'])]
    header+=table(['Fase (eigen ronde)','Acties','Betrokken inhalers'],[[f'{a}–{z}',sum(a<=e['lap']<=z for e in selected),', '.join(sorted({names.get(e['overtaker'],str(e['overtaker'])) for e in selected if a<=e['lap']<=z})) or 'geen'] for a,z in thirds])
    header+='\n## Banden en pitstrategie\n\n'+f"Er zijn {len(data['pit'])} geregistreerde pitlane-bezoeken en {len(data['stints'])} stints. De stints en geschiktheidsfilters staan in het afzonderlijke bandenrapport. {len(b['cycles'])} afgeronde vergelijkingssituaties voldoen aan de grens van {b['config']['strategie_gap_grens_seconden']} seconden vóór de eerste stop. De uitkomst omvat alle bijdragen, niet alleen banden.\n"
    header+=table(['Startcompound','Coureurs'],[[compound,', '.join(d['code'] for d in ds if d['start_compound']==compound)] for compound in sorted({d['start_compound'] for d in ds if d['start_compound']})])
    header+='\n## Neutralisaties, incidenten en straffen\n\n'+f"{sum(d['result'].get('dnf',False) for d in ds)} coureurs met DNF-vlag in de einddata. {len(Context(data,b['config']).neutral_windows)} neutralisatievensters herkend. Afwezigheid in een feed is geen zelfstandig bewijs van volledige afwezigheid.\n"
    rc=[r for r in data['race_control'] if b['start'] and ts(r['date'])>=b['start'] and (r.get('flag') in ['YELLOW','DOUBLE YELLOW','RED','BLACK AND WHITE'] or r.get('category')=='SafetyCar' or any(k in r.get('message','') for k in ['INCIDENT','PENALTY']))]
    header+=table(['UTC','Feedronde','Betekenis','Ruwe registratie'],[[r['date'],r.get('lap_number'),translate_control(r['message']),r['message']] for r in rc])
    header+='\n## Bewijs en interpretatie\n\nVastgesteld door gegevens: opgeslagen uitslag, gridvelden, posities, pitbezoeken en compounds. Bronbevestigde context wordt per gebeurtenis gekoppeld. Tempo- en strategische verklaringen zijn interpretaties waar oorzaak niet geïsoleerd is. Volledige manoeuvrevolgorde, remtelemetrie en teamintentie zijn niet uit alleen positiegegevens vast te stellen.\n'
    for e in events:
        for claim in e.get('evidence',[]):header+=f"\n- {names.get(e['overtaker'])}–{names.get(e['overtaken'])}, {'eigen ronde '+str(e['lap']) if e['lap'] is not None else 'na de race'}: {claim['claim']} [{claim['source']}]({claim['url']}).\n"
    header+='\n## Datadekking en grenzen\n\n'+'\n'.join('- '+w for w in b['warnings'])
    header+='\n\n[Gebeurtenissenlijst](../exports/gebeurtenissen.json) · [Bandenstrategie](bandenstrategie.html) · [Pitstopcycli](undercut-overcut.html) · [Bronnen en methode](bronnen-en-methode.html)\n'
    first=f"# Ronde 1 — {prefix}\n\nWerkelijke start: {start}. Pitlanestarters behouden een aparte aanduiding. Einde ronde 1 gebruikt de laatste positie vóór de eigen ronde-2-start, waarvan het tijdstip benaderd is. Dit is geen exact gelijktijdige klassering op het moment dat de leider de lijn passeert.\n"
    first+=table(['Coureur','Grid','Einde eigen ronde 1','Netto winst','Startband'],[[d['code'],'pitlane' if d['pitlane_start'] else d['grid'],d['lap1_position'],d['lap1_net_gain'],d['start_compound']] for d in sorted(ds,key=lambda d:d['lap1_position'] or 99)])
    first+='\n## Voorin, middenveld en achteraan\n'
    for name,lo,hi in [('Vooraan',1,5),('Middenveld',6,14),('Achteraan',15,99)]:
        group=[d for d in ds if lo<=(d['grid'] or 99)<=hi]
        first+='\n'+name+': '+('; '.join(f"{d['code']}: {'pitlane' if d['pitlane_start'] else 'P'+str(d['grid'])} → P{val(d['lap1_position'])}" for d in group) or 'geen beschikbare gegevens')+'.\n'
    first+=f"\n## Tijdlijn van startwisselingen\n\n{s['lap1_changes']} startregistraties afzonderlijk. Netto winst is het verschil van twee posities. De tabel hieronder bevat bronwisselingen; meerdere registraties kunnen dezelfde gevechtsfase beschrijven. Startactie betekent hier geen automatisch bewezen inhaalmanoeuvre.\n"
    first+=table(['UTC','Inhaler','Gepasseerde','Positie volgens bron','Classificatie','Gebeurtenis-ID'],[[e['date'],names.get(e['overtaker']),names.get(e['overtaken']),e['source_position'],e['type'],e['event_id']] for e in events if e['counts']['lap1']])
    lap1rc=[r for r in data['race_control'] if b['start'] and ts(r['date'])>=b['start'] and ('LAP 1 ' in r['message'] or r.get('lap_number') in [1,2] and 'INCIDENT' in r['message'])]
    first+='\n## Incidenten en latere beoordeling\n'+table(['Registratietijd UTC','Toelichting','Originele bronregistratie'],[[r['date'],translate_control(r['message']),r['message']] for r in lap1rc])
    first+='\nDe meldingsronde is niet altijd de incidentronde: een incident in ronde 1 kan later worden beoordeeld. Schade en oorzaak worden niet afgeleid uit een positieverschil. De latere eindpositie toont het uiteindelijke verloop, maar bewijst geen causaal effect van de start. Formatieronde wordt door het gecontroleerde starttijdstip uitgesloten.\n'
    overtakes=f"# Inhaalacties — {prefix}\n\n## Drie gescheiden tellingen\n\n{data.get('timing_source','OpenF1')} oorspronkelijk: {s.get('timing_original',s['openf1_original'])} registraties over de volledige feed. F1gures oorspronkelijk: {s['f1gures_original'] if data.get('f1gures') else 'onbekend; gebeurtenissen ontbreken'}. Op de baan vanaf ronde 2: {s['on_track']}. Aanvullende analytische telling: {s['analytical']}. Ronde 1: {s['lap1_changes']} afzonderlijke startwisselingen.\n"
    overtakes+=f"\nAnalytische teamorderuitsluiting: {b['config']['analytisch_teamorders_uitsluiten']}. Uitsluiting van technisch positieverlies: {b['config']['analytisch_technisch_verlies_uitsluiten']}. Technisch verlies wordt niet stilzwijgend verwijderd. Pitwisselingen en onbewezen timingfluctuaties staan in de volledige export.\n"
    overtakes+=table(['Classificatie','Aantal gebeurtenissen'],list(s['types'].items()))
    overtakes+=f"\n## Ronden en concentratie\n\n{s['laps_with']} ronden met en {s['laps_without']} ronden zonder geselecteerde acties; samen {s['denominator']}. Gemiddelde {val(s['mean'],3)} acties per geanalyseerde ronde. Drukste eigen ronden: {', '.join(map(str,s['busiest_laps'])) or 'geen'}. Slotfase: laatste {val(b['config']['slotfase_fractie']*100)}%, afgerond naar boven tot ronde {s['late_start']}–{s['late_end']}. Daarin {s['late_count']} acties, {val(s['late_fraction']*100 if s['late_fraction'] is not None else None)}% van {s['analytical']}.\n"
    overtakes+=table(['Eigen ronde','Acties'],list(s['per_lap'].items()))
    overtakes+='\n## Uitgevoerd en ondergaan\n'+table(['Coureur','Uitgevoerd','Ondergaan'],[[d['code'],s['made'].get(d['driver_number'],s['made'].get(str(d['driver_number']),0)),s['received'].get(d['driver_number'],s['received'].get(str(d['driver_number']),0))] for d in ds])
    overtakes+='\n## Compoundcombinaties\n'+table(['Inhaler → gepasseerde','Acties'],list(s['compound_pairs'].items()))
    overtakes+='\n## Geselecteerde gebeurtenissen en bewijs\n'+table(['ID','Eigen ronde','Andere ronde','Inhaler','Gepasseerde','Bronpositie','Banden','Bandenleeftijden','Type','Locatie'],[[e['event_id'],e['lap'],e['overtaken_lap'],names.get(e['overtaker']),names.get(e['overtaken']),e['source_position'],str(e['tyre_overtaker']['compound'])+' / '+str(e['tyre_overtaken']['compound']),str(e['tyre_overtaker']['age'])+' / '+str(e['tyre_overtaken']['age']),e['type'],'bocht '+str(e['confirmed_turn'])+' bronbevestigd; kaart geschat' if e.get('confirmed_turn') else e['location_confidence']] for e in selected])
    overtakes+=f"\n## Bronnenvergelijking\n\n{ s['source_matches']} eenduidige matches met F1gures-regels op coureurpaar en eigen ronde. Zonder brongegevens is dit geen uitspraak over overeenstemming. OpenF1-only en F1gures-only registraties staan met bronrecords in de export. Een bronregel met meerdere kandidaten blijft onzeker en wordt niet automatisch meegeteld. De openbare F1gures-weergavedefinitie noemt netto passages, inclusief ronde 1, met uitsluiting van pitstopwisselingen en safetycarronden. De telling wordt gereconstrueerd uit openbare ronde-einddata volgens de weergaveregel; het is geen apart gedocumenteerde gebeurtenissen-API. FastF1 en OpenF1 verwerken deels dezelfde oorspronkelijke timingfeed.\n"
    if data.get('f1gures'):
        overtakes+='\n### Controleerbare bronverschillen\n'+table(['Gebeurtenis-ID','Ronde','Coureurs','Bronnen','Classificatie','Mogelijke matches'],[[e['event_id'],e['lap'],str(names.get(e['overtaker']))+'/'+str(names.get(e['overtaken'])),', '.join(sorted({r['source'] for r in e['source_records']})),e['type'],', '.join(e.get('possible_matches',[])) or 'geen'] for e in events if any(r['source']=='F1gures' for r in e['source_records'])])
        first+='\n## Vergelijking met F1gures ronde-eindregistraties\n'+table(['Inhaler','Gepasseerde','Bronronde','Definitie'],[[names.get(r['overtaking_driver_number']),names.get(r['overtaken_driver_number']),r['lap_number'],'netto omkering tussen grid en ronde-einde'] for r in data['f1gures'] if r['lap_number']==1])
    if session['year']==2025 and session['circuit_short_name']=='Singapore':
        ant=[e for e in events if e['overtaker']==12 and e['overtaken']==16 and e['type']=='inhaalactie']
        overtakes+=f"\n## Controle van de eerdere Singapore-claims\n\nDe claim van 27 acties is geen testverwachting. Deze configuratie resulteert in {s['analytical']} analytische acties. De claim van 21 acties in ronde 47–62 wordt getoetst aan dezelfde eigen-rondeconventie: {sum(47<=e['lap']<=62 for e in selected)}. Ronde 53 telt {s['per_lap'].get('53',0)} geselecteerde acties. Verschil kan zowel uit definitie, timingfilter als rondeconventie komen; zonder de oorspronkelijke chatlijst kan het verschil niet één-op-één worden bewezen.\n"
        comparison=s.get('f1gures_comparison',{})
        if data.get('f1gures'):
            overtakes+=f"\n### Reconstructie van een bronvariant met uitsluitend technische correctie\n\nF1gures registreert {comparison['lap1']} netto passages in ronde 1 en {comparison['from_lap2']} vanaf ronde 2; samen {s['f1gures_original']}. In de slotfase liggen {comparison['late_count']} oorspronkelijke F1gures-passages. Uitsluitend de brononderbouwde technische wisseling verwijderen resulteert in {comparison['excluding_technical']} vanaf ronde 2 en {comparison['excluding_technical_late']} in ronde {s['late_start']}–{s['late_end']} ({val(comparison['excluding_technical_late_fraction']*100 if comparison['excluding_technical_late_fraction'] is not None else None)}%). Gebeurtenis-ID van de uitsluiting: {', '.join(comparison['excluded_event_ids']) or 'geen'}.\n"
            overtakes+=f"\nDeze afzonderlijke bronvariant reproduceert de combinatie 27 / 21 uit de eerdere claim als de berekende waarden daarmee overeenkomen, maar bewijst niet dat de eerdere chat dezelfde gebeurtenissenlijst gebruikte. De primaire analytische telling blijft {s['analytical']}. Die gebruikt OpenF1-tijdvensters, sluit de brononderbouwde teamwisseling uit en behoudt technisch verlies. F1gures sluit hele pitgerelateerde ronden uit; dat kan ook echte baanacties op zo'n ronde verwijderen. De verschillen zijn geen bewijs dat één volledige telling vaststaat.\n"
        for e in ant:overtakes+=f"\nAntonelli–Leclerc: eigen ronde {e['lap']}, Leclerc eigen ronde {e['overtaken_lap']}, registratie {e['date']}. Bocht 16: {'bevestigd door Mercedes, onafhankelijk van de rondebepaling' if e.get('confirmed_turn') else 'niet door opgehaalde bron bevestigd'}. Het verslag noemt zelf geen ronde.\n"
        for e in events:
            if e['overtaker']==16 and e['overtaken']==44 and (e['lap'] or 0)>=59:overtakes+=f"\nLeclerc–Hamilton: {e['type']}, ronde {e['lap']}. {e['reason']} In de basistelling: {e['counts']['on_track']}; analytisch: {e['counts']['analytical']}.\n"
    tyres=f"# Bandenstrategie — {prefix}\n\nCompound en bandenleeftijd komen uit stints; bandenleeftijd is leeftijd vóór de lopende ronde. Beginleeftijd nul betekent nieuw volgens deze feed. Grip, slijtage en graining worden niet gemeten met deze gegevens.\n"
    tyres+=table(['Coureur','Stint','Compound','Ronden','Beginleeftijd','Nieuw/gebruikt','Lengte','Geschikte ronden','Tempo begin/midden/eind (s)','Robuuste trend s/ronde'],[[names.get(st['driver_number']),st['stint_number'],st['compound'],f"{st['lap_start']}–{st['lap_end']}",st.get('tyre_age_at_start'),st['new_or_used'],st['length'],st['clean_laps'],' / '.join(val(x,3) for x in st['phase_medians']),st['robust_trend_seconds_per_lap']] for st in b['tyres']['stints']])
    tyres+='\n## Tempo, opwarming en degradatie\n\nTempo per fase is de mediaan van drie even grote delen van geschikte stintwaarnemingen. De trend is de mediaan van alle paarsgewijze hellingen (minimaal zes geschikte ronden). Een negatieve trend betekent sneller worden en is geen bewijs dat slijtage ontbreekt. Brandstofafname en baanontwikkeling worden niet geïsoleerd. Opwarming is zichtbaar in eerste geschikte ronden na de outlap, maar zonder verkeers- en brandstofmodel volgt geen zuivere opwarmtijd.\n'
    for d in ds:
        stints=[st for st in b['tyres']['stints'] if st['driver_number']==d['driver_number']]
        es=[e for e in selected if e['overtaker']==d['driver_number'] or e['overtaken']==d['driver_number']]
        tyres+=f"\n### {d['name'].title()}\n\nStrategie: "+' → '.join(f"{compound_label(st['compound'])} ({st['length']} ronden, beginleeftijd {val(st.get('tyre_age_at_start'))})" for st in stints)+f". Betrokken bij {len(es)} geselecteerde passages. Verschillen in beschikbare grip zijn interpretaties; koppeling per gebeurtenis staat in de export.\n"
        cs=[c for c in b['cycles'] if d['driver_number'] in [c['early_driver'],c['late_driver']]]
        if cs:tyres+='\nVergelijkbare tegenstanders rond pitstops: '+ '; '.join(f"{names[c['early_driver']]}/{names[c['late_driver']]}: {c['status']}" for c in cs)+'. Langer doorrijden wordt pas na beide stops beoordeeld.\n'
    exclusions=Counter(reason for row in b['tyres']['excluded_laps'] for reason in row['reasons'])
    tyres+='\n## Uitgesloten ronden\n'+table(['Reden (kan overlappen)','Ronden'],list(exclusions.items()))
    tyres+='\n[Alle uitgesloten ronden en redenen](../data/derived/tyre-exclusions.json). Verkeer gebruikt het interval halverwege de ronde en kan niet alle verkeer herkennen. Vlagronden worden conservatief voor het hele veld uitgesloten.\n'
    under=f"# Undercut en overcut — {prefix}\n\nAlleen coureurs binnen {b['config']['strategie_gap_grens_seconden']} seconden op dezelfde voltooide ronde vóór de eerste stop; stops maximaal {b['config']['strategie_max_stopafstand_ronden']} ronden uit elkaar. Beide stops en outlaps moeten voltooid zijn. Tijdwinst vroegst stoppende coureur = tijdachterstand vóór minus tijdachterstand na. Positiewinst betekent omkering van de onderlinge volgorde, niet winst op andere coureurs. Intentie is onbekend: daarom situaties, geen bewezen teamplannen.\n"
    under+=table(['Coureurs vroeg/laat','Stops','Referentie → beoordeling','Voor (s)','Na (s)','Winst vroege (s)','Situatie','Resultaat','Volgorde gewijzigd'],[[names[c['early_driver']]+'/'+names[c['late_driver']],f"{c['early_stop_lap']} / {c['late_stop_lap']}",f"{c['baseline_lap']} → {c['completed_lap']}",c['gap_before'],c['gap_after'],c['gain_early_driver'],c['strategy'],c['status'],c['order_changed']] for c in b['cycles']])
    under+=f"\nAlle {len(b['cycles'])} vergelijkingen zijn interactief beschikbaar; {len(b['exported_cycle_ids'])} hebben ook een losse PNG/SVG-detailgrafiek.\n"
    for c in b['cycles']:
        under+=f"\n## {names[c['early_driver']]} / {names[c['late_driver']]} — {c['status']}\n\nEerste stop ronde {c['early_stop_lap']}, tweede ronde {c['late_stop_lap']}; beoordeling op gelijke ronde {c['completed_lap']}. Tijdwinst vroegst gestopte: {val(c['gain_early_driver'],3)} s. Pitlane vroeg/laat: {val(c['pit_lane_early'],3)} / {val(c['pit_lane_late'],3)} s; stilstand vroeg/laat: {val(c['stationary_early'])} / {val(c['stationary_late'])} s. {c['attribution']}\n"
        under+=table(['Coureur','Ronde','Rondetijd (s)','Outlap','Compound','Leeftijd'],[[names[r['driver']],r['lap'],r['duration'],r['outlap'],r['tyre']['compound'],r['tyre']['age']] for r in c['lap_details']])
        target='../figures/png/pitcyclus-'+c['cycle_id']+'.png' if c['cycle_id'] in b['exported_cycle_ids'] else '../overzicht.html#'+quote(json.dumps({'cycle':c['cycle_id'],'min':c['trace'][0]['lap'],'max':c['trace'][-1]['lap'],'drivers':[c['early_driver'],c['late_driver']]}),safe='')
        under+=f"\n[Detailgrafiek]({target}). Verkeer, bandentemperatuur en teamintentie worden niet causaal gekwantificeerd; pitlaneverschil is wel gemeten. Geen uitspraak dat een alternatief zeker beter was.\n"
    method=f"# Bronnen en methode — {prefix}\n\n## Gegevens en verklaringen\n\n"+source_links
    method+='\n## Bronregister en reproduceerbaarheid\n\n[Manifest met URL, uitgever, ophaaltijd en hashes](../manifest.json). Ruwe gegevens, genormaliseerde input en afgeleide analyse zijn apart opgeslagen. Een heranalyse gebruikt dezelfde correcties; een nieuwe uitvoering overschrijft de oude niet.\n'
    method+='\n## Classificatie en rondeconventie\n\nDe eigen lopende ronde van de inhaler bepaalt de statistische ronde; beide eigen ronden blijven bewaard. Identieke richting/ronde binnen het ingestelde tijdvenster wordt samengevoegd met behoud van bronregels. Een snelle tegengestelde registratie blijft als timingfluctuatie zichtbaar. Bij start-finish kan een rondeverschil normaal zijn; afstand in tijd op dezelfde ronde helpt dubbelen onderscheiden. Onvoldoende bewijs blijft onzeker.\n'
    method+=f"\nPitcontext: registratie vóór het OpenF1-pittijdstip binnen de pitlane-duur, plus/min {b['config']['pit_marge_seconden']} s. Volgordecontrole: {b['config']['registratievenster_seconden']} s voor en na. Het tijdstip wordt als exitregistratie geïnterpreteerd; Singapore is getoetst aan de FIA-entrytabel, met enkele seconden verschil. Dit zijn conservatieve heuristieken, geen gekalibreerde kansen. Een inhaalclassificatie vanuit timing is een duurzame wisseling buiten deze vensters, geen videobewijs van de manoeuvre. Teamorders en technische oorzaken vereisen aanvullende bronclaims.\n"
    method+='\n## Circuitkaart\n\nBaanvorm uit een volledige gemeten ronde van de winnaar, in sequentiële meetvolgorde. OpenF1-coördinaten hebben arbitraire oorsprong; geen geografische oriëntatie of meters worden geclaimd. Booglengtesegmenten blijven gescheiden bij nabijgelegen baanstukken. Voor en na de registratie moeten beide coureurs locatiepunten hebben voor een timingschatting. Een bronbevestigde bocht mag afzonderlijk op gevalideerde jaargeometrie worden verankerd. Te ver van de baan of te grote spreiding leidt tot onbekend. Bochtbevestiging uit een verslag bewijst geen exact inhaalpunt. Jaargeometrie wordt alleen gekoppeld wanneer alle bochtankers aansluiten op de gemeten baanvorm.\n'
    reference=data.get('circuit_reference',{})
    if reference.get('source_url'):
        method+=f"\nOfficiële jaarvariant {reference['year']} gecontroleerd aan [{reference['source_title']}]({reference['source_url']}). {reference['note']} {reference['verification']} De onderliggende bochtcoördinaten komen uit {reference['coordinate_basis_year']}; dit vormt geen extra bewijs voor de plaats van een manoeuvre.\n"
    else:
        method+='\nGeen gecontroleerde officiële circuitkaart voor dit racejaar. De kaart is een gemeten benadering; mogelijke tunnels, bruggen en hoogteverschillen zijn niet zelfstandig uit XY-data vast te stellen.\n'
    method+='\nWikipedia wordt bij iedere nieuwe raceanalyse opgezocht via de circuitlink in Jolpica of een Wikipedia-zoekopdracht, met cache voor offline gebruik. Namen worden alleen aan een gecontroleerde jaarvariant gekoppeld; kandidaten uit tabellen blijven ongebruikt tot deze koppeling is gecontroleerd. Historische namen krijgen een aanduiding. De pijlen volgen de chronologische meetvolgorde van de ronde. Start/finish is de gemeten rondestart. Pit-in/out-markers tonen brongetoetste indicatieve aftak- en aansluitzones op de hoofdbaan, geen exacte pitlijn of ingetekende pitlane. Ontbrekende broncontrole levert geen verzonnen markers op.\n'
    method+=f"\nKaartdekking: {b['mapping']['located']} van {b['mapping']['included']} analytische gebeurtenissen, {b['mapping']['unknown']} onbekend. Heatmap: aantallen per {b['config']['heatmap_segmenten']} gelijke booglengtesegmenten, geen genormaliseerde dichtheid en geen ruimtelijke smoothing. Een zone krijgt één representatief segment; tijdvenster-spreiding blijft in de export.\n"
    quality=f"# Datakwaliteit — {prefix}\n\nStatus: gedeeltelijk. Deze versie certificeert geen volledige reconstructie van alle manoeuvres of causale bandenwerking.\n"
    quality+=table(['Dataset','Registraties','Dekking'],[[ep,len(data.get(ep,[])),'beschikbaar' if data.get(ep) else 'ontbreekt'] for ep in ['drivers','starting_grid','session_result','laps','position','intervals','overtakes','pit','stints','race_control','weather','team_radio','f1gures']])
    quality+='\n## Grenzen\n\n'+'\n'.join('- '+w for w in b['warnings'])
    quality+='\n\nTeamradio is alleen een register van audiolinks; geen automatische transcriptie of conclusies uit ongehoorde radio. DRS-activering in race control bewijst niet dat een specifieke manoeuvre DRS gebruikte. Autotelemetrie wordt in deze versie niet verwerkt. Bronverschillen vereisen een F1gures-import. Aanvullende bronnen buiten de eerste proefrace worden via config/sources.yaml toegevoegd.\n'
    quality+=f"\n## Automatische controles\n\nSom per ronde = {sum(s['per_lap'].values())} = geselecteerd totaal {s['analytical']}. Ronden met/zonder = {s['laps_with']} + {s['laps_without']} = {s['denominator']}. Kaart gelokaliseerd/onbekend = {b['mapping']['located']} + {b['mapping']['unknown']} = {s['analytical']}. Alle lokale HTML-links worden na het renderen gecontroleerd.\n"
    tyre_source=next((source for source in data.get('evidence',[]) if source.get('id')=='singapore-banden' and source.get('available')),None)
    if tyre_source:
        tyres+='\n## Toets aan Pirelli en teamverklaringen\n\nPirelli beoordeelt medium als de meest evenwichtige keuze voor consistentie en prestaties; ook hard leverde een bruikbaar tempo. Dit ondersteunt de compoundkeuze, maar valideert geen causale degradatiehelling per coureur. [Pirelli en teamreacties]('+tyre_source['url']+').\n'
    result={'raceanalyse':header,'ronde-1':first,'inhaalacties':overtakes,'bandenstrategie':tyres,'undercut-overcut':under,'bronnen-en-methode':method,'datakwaliteit':quality}
    if data.get('timing_source')=='FastF1':
        result={k:v.replace('OpenF1','FastF1').replace('FastF1 en FastF1 verwerken deels dezelfde oorspronkelijke timingfeed.','FastF1 verwerkt de oorspronkelijke F1-timingfeed; andere bronvarianten kunnen dezelfde timing gebruiken.') for k,v in result.items()}
        result['bronnen-en-methode']=result['bronnen-en-methode'].replace('Singapore is getoetst aan de FIA-entrytabel, met enkele seconden verschil.','Bij historische races worden PitInTime en de eerstvolgende PitOutTime gebruikt; stilstandduur wordt niet ingevuld.')
        for k in result:result[k]+='\n\nHistorische bron: '+data['timing_method']+' FastF1 bewerkt ronde- en sessietijdstippen; synthetische ronden zijn uitgesloten. De originele timingarchiefbestanden en URL-hashes zijn bewaard.\n'
    return result


def translate_control(message):
    if 'NO FURTHER INVESTIGATION' in message:return 'Beoordeeld: geen verder onderzoek'
    if 'WILL BE INVESTIGATED' in message:return 'Onderzoek na de race aangekondigd'
    if 'INCIDENT' in message:return 'Incident gemeld; meldingstijd is niet automatisch incidenttijd'
    if 'DOUBLE YELLOW' in message:return 'Dubbel geel gemeld'
    if 'YELLOW' in message:return 'Geel gemeld'
    if 'BLACK AND WHITE' in message:return 'Zwart-witte waarschuwing wegens baanlimieten'
    return 'Ruwe race-controlmelding; zie originele tekst'


def interactive(run,b):
    from .location import display_point
    reference=b['data'].get('circuit_reference',{})
    mapped_events=[{**e,'location':display_point(e['location'],reference) if e.get('location') else None} for e in b['events']]
    from .map_labels import annotations
    displayed_track=[display_point(p,reference) for p in b['track']]
    labels=annotations(displayed_track,reference)
    payload={'driver_styles':driver_styles(b['data']['drivers']),'labels':labels,'reference':reference,'track':[display_point(p,reference) for p in b['track']],'events':mapped_events,'drivers':b['drivers'],'lap_count':b['stats']['lap_count']}
    script=r'''
const D=JSON.parse(document.getElementById('gegevens').textContent);
const E=id=>document.getElementById(id),esc=s=>String(s??'onbekend').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
for(const d of D.drivers)E('driver').add(new Option(D.driver_styles[d.driver_number]?.label||d.code,d.driver_number));
for(const t of [...new Set(D.events.map(e=>e.type))])E('type').add(new Option(t.replaceAll('_',' '),t));
E('max').value=D.lap_count;
const driverInfo=number=>{const d=D.drivers.find(d=>d.driver_number===number);return `${number} · ${d?.name||D.driver_styles[number]?.label||'onbekende coureur'}`;};
function popupHtml(events){return (events.length>1?'<p class="muted">Meerdere acties bij deze kaartzone</p>':'')+events.map(e=>`<div class="popup-event"><strong>Ronde ${esc(e.lap)}</strong><div><span class="muted">Haalt in:</span> <b style="color:${D.driver_styles[e.overtaker]?.color||'#f5f7fa'}">${esc(driverInfo(e.overtaker))}</b></div><div><span class="muted">Ingehaald:</span> <b style="color:${D.driver_styles[e.overtaken]?.color||'#f5f7fa'}">${esc(driverInfo(e.overtaken))}</b></div><small class="muted">${esc(e.confirmed_location_label||e.location_confidence)}</small></div>`).join('');}
const tooltip=E('overtake-popup');
function hidePopup(){tooltip.hidden=true;}
function showPopup(events,anchor,event){
 tooltip.innerHTML=popupHtml(events);tooltip.hidden=false;
 const rect=anchor.getBoundingClientRect(),x=event?.clientX??rect.left+rect.width/2,y=event?.clientY??rect.top+rect.height/2;
 const width=tooltip.offsetWidth,height=tooltip.offsetHeight;
 tooltip.style.left=Math.max(12,Math.min(x+16,window.innerWidth-width-12))+'px';
 tooltip.style.top=Math.max(12,Math.min(y+16,window.innerHeight-height-12))+'px';
}

function draw(){
 hidePopup();
 const driver=E('driver').value,type=E('type').value,phase=E('phase').value,conf=E('confidence').value,compound=E('compound').value;
 let events=D.events.filter(e=>(!driver||e.overtaker==driver||e.overtaken==driver)&&(!type||e.type==type)&&(!phase||(phase==='start'?e.lap===1:e.lap>=2))&&(!conf||e.location_confidence===conf)&&(!compound||e.tyre_overtaker.compound===compound||e.tyre_overtaken.compound===compound)&&(e.lap||0)>=+E('min').value&&(e.lap||0)<=+E('max').value&&(!E('analytical').checked||phase==='start'||e.counts.analytical));
 const loc=events.filter(e=>e.location),T=D.track;E('coverage').textContent=`${events.length} gebeurtenissen · ${loc.length} bruikbare kaartzones · ${events.length-loc.length} zonder coördinaten. Bochtbevestiging uit bronnen staat los van kaartcoördinaten.`;
 if(T.length){
 const labels=D.labels||[],xs=T.map(p=>p.x).concat(labels.flatMap(l=>[l.display_box.xmin,l.display_box.xmax])),ys=T.map(p=>p.y).concat(labels.flatMap(l=>[l.display_box.ymin,l.display_box.ymax])),xmin=Math.min(...xs),ymin=Math.min(...ys),w=Math.max(...xs)-xmin,h=Math.max(...ys)-ymin;
 const scale=800/Math.max(Math.max(...T.map(p=>p.x))-Math.min(...T.map(p=>p.x)),Math.max(...T.map(p=>p.y))-Math.min(...T.map(p=>p.y)));
 const unit=800/Math.max(Math.max(...T.map(p=>p.x))-Math.min(...T.map(p=>p.x)),Math.max(...T.map(p=>p.y))-Math.min(...T.map(p=>p.y))),X=p=>60+(p.x-xmin)*unit,Y=p=>60+(ymin+h-p.y)*unit;
 let counts=Array(100).fill(0);for(const e of loc)counts[Math.min(99,Math.floor(e.location.progress*100))]++;
 const A=(D.reference.display_rotation_degrees||0)*Math.PI/180,rotate=p=>({x:p.x*Math.cos(A)-p.y*Math.sin(A),y:p.x*Math.sin(A)+p.y*Math.cos(A)});
 let svg=`<svg viewBox="0 0 ${120+w*scale} ${120+h*scale}" role="group" aria-label="Circuitkaart met bochten, start/finish, rijrichting en indicatieve pit-in/out"><defs><marker id="richting" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="#f5f7fb"/></marker></defs>`;
 for(let i=0;i<T.length-1;i++){let c=counts[Math.min(99,Math.floor(i/(T.length-1)*100))],color=c?`hsl(${Math.max(0,45-c*10)} 90% 60%)`:'#414e64';svg+=`<line x1="${X(T[i])}" y1="${Y(T[i])}" x2="${X(T[i+1])}" y2="${Y(T[i+1])}" stroke="${color}" stroke-width="6" stroke-linecap="round"/>`;}
 for(const f of [.18,.46,.73]){const i=Math.floor(f*(T.length-1)),j=Math.min(i+7,T.length-1);svg+=`<line x1="${X(T[i])}" y1="${Y(T[i])}" x2="${X(T[j])}" y2="${Y(T[j])}" stroke="#f5f7fb" stroke-width="2" marker-end="url(#richting)"/>`;}
 const tangent={x:X(T[2])-X(T[0]),y:Y(T[2])-Y(T[0])},norm=Math.hypot(tangent.x,tangent.y),nx=-tangent.y/norm*10,ny=tangent.x/norm*10;
 svg+=`<line x1="${X(T[0])-nx}" y1="${Y(T[0])-ny}" x2="${X(T[0])+nx}" y2="${Y(T[0])+ny}" stroke="#51d6dd" stroke-width="3"/>`;
 for(const marker of (D.reference.pit_markers||[])){const p=rotate(marker),x=X(p),y=Y(p);svg+=`<path d="M${x},${y-6} L${x+6},${y} L${x},${y+6} L${x-6},${y} Z" fill="#bd9cff"><title>${esc(marker.note)} ${esc(marker.accuracy)}</title></path>`;}
 for(const label of labels){svg+=`<line x1="${X(label)}" y1="${Y(label)}" x2="${X(label.leader_end)}" y2="${Y(label.leader_end)}" stroke="${label.color}" stroke-width="1" opacity="0.65"/><text x="${X(label.text_position)}" y="${Y(label.text_position)}" text-anchor="middle" dominant-baseline="central" fill="${label.color}" font-size="14">${esc(label.text)}</text>`;}

 for(const [index,e] of loc.entries()){svg+=`<circle class="overtake-marker" data-event-index="${index}" tabindex="0" role="button" aria-describedby="overtake-popup" aria-label="Ronde ${esc(e.lap)}: ${esc(driverInfo(e.overtaker))} haalt ${esc(driverInfo(e.overtaken))} in" cx="${X(e.location)}" cy="${Y(e.location)}" r="7" fill="${D.driver_styles[e.overtaker]?.color||'#51d6dd'}"/>`;}
 E('map').innerHTML=svg+'</svg><p>Pijlen: rijrichting · cyaan: start/finish · paars ≈: indicatieve pit-in/out-zone.</p>'+(D.reference.wikipedia_url?`<p>Bochtnamen: <a href="${esc(D.reference.wikipedia_url)}">Wikipedia</a>. Namen ontbreken wanneer niet aangetroffen of niet aan deze jaarvariant gekoppeld.</p>`:'')+(D.reference.source_url?`<p>Officiële jaarvariant ${esc(D.reference.year)} gecontroleerd: <a href="${esc(D.reference.source_url)}">${esc(D.reference.source_title)}</a>. ${esc(D.reference.note)} Bochtnummers hebben benaderde coördinaten.</p>`:'<p>Geen gecontroleerde officiële circuitkaart voor dit racejaar.</p>');
 for(const marker of E('map').querySelectorAll('.overtake-marker')){
   const selected=loc[Number(marker.dataset.eventIndex)];
   const nearby=loc.filter(e=>Math.hypot(X(e.location)-X(selected.location),Y(e.location)-Y(selected.location))<12).sort((a,b)=>a.lap-b.lap);
   for(const type of ['pointerenter','pointermove','focus','click'])marker.addEventListener(type,event=>showPopup(nearby,marker,event));
   for(const type of ['pointerleave','blur'])marker.addEventListener(type,hidePopup);
   marker.addEventListener('keydown',event=>{if(event.key==='Escape'){hidePopup();}else if(event.key==='Enter'||event.key===' '){event.preventDefault();showPopup(nearby,marker);}});
 }
 }else E('map').textContent='Geen gemeten volledige circuitronde beschikbaar; geen verzonnen kaartpunten.';
 E('list').innerHTML='<table><tr><th>ID</th><th>Ronde</th><th>Coureurs</th><th>Type</th><th>Locatie / bewijs</th></tr>'+events.map(e=>`<tr><td>${esc(e.event_id)}</td><td>${esc(e.lap)}</td><td>${esc(e.overtaker)} → ${esc(e.overtaken)}</td><td>${esc(e.type)}</td><td>${esc(e.confirmed_location_label||e.location_confidence)}</td></tr>`).join('')+'</table>';
}
window.addEventListener('scroll',hidePopup,{passive:true});window.addEventListener('resize',hidePopup);
for(const input of document.querySelectorAll('input,select'))input.addEventListener('input',draw);draw();
'''
    body='<a href="../overzicht.html">← Analyseoverzicht</a><h1>Circuitkaart en gebeurtenissen</h1><p class="muted">Gemeten circuitvorm in arbitraire coördinaten. Heatmap telt gebeurtenissen per booglengtesegment. Markers vertegenwoordigen geschatte zones uit beide tijdvensters; geen exacte inhaalpunten of geografische oriëntatie. Geen externe assets nodig.</p>'
    body+='''<div class="card"><label>Coureur <select id="driver"><option value="">Alle coureurs</option></select></label> <label>Ronde <input id="min" type="number" value="1" min="1" style="width:65px"> tot <input id="max" type="number" min="1" style="width:65px"></label> <label>Fase <select id="phase"><option value="">Hele race</option><option value="start">Ronde 1</option><option value="race">Vanaf ronde 2</option></select></label> <label>Type <select id="type"><option value="">Alle typen</option></select></label> <label>Locatie <select id="confidence"><option value="">Alle niveaus</option><option>bevestigde zone</option><option>geschatte zone</option><option>onbekend</option></select></label> <label>Compound <select id="compound"><option value="">Alle compounds</option><option value="SOFT">Zacht</option><option value="MEDIUM">Middel</option><option value="HARD">Hard</option><option value="INTERMEDIATE">Intermediate</option><option value="WET">Regen</option></select></label> <label><input id="analytical" type="checkbox" checked> Alleen analytische telling</label></div><p id="coverage"></p><div id="map" class="card"></div><p>Bronbevestigde bocht: tekstueel niveau; geschatte zone: timing en locatie; onbekend: geen verantwoorde kaartplaatsing. Onbekende gebeurtenissen blijven in de tabel.</p><div id="list" style="overflow:auto"></div>'''
    body+='<style>#overtake-popup{position:fixed;z-index:1000;width:340px;max-width:calc(100vw - 48px);padding:16px;background:#181f2c;border:1px solid #51d6dd;border-radius:10px;box-shadow:0 8px 30px #0009;pointer-events:none;font-size:14px;line-height:1.5}#overtake-popup[hidden]{display:none}.popup-event+.popup-event{border-top:1px solid #596273;margin-top:12px;padding-top:12px}.overtake-marker{cursor:help;stroke:#10141d;stroke-width:1.5}.overtake-marker:hover,.overtake-marker:focus{stroke:white;stroke-width:3;outline:none}</style><div id="overtake-popup" role="tooltip" hidden></div><p class="muted">Beweeg over een inhaalmarker, gebruik Tab of tik op een marker voor ronde en betrokken coureurs.</p>'
    body+='<script id="gegevens" type="application/json">'+json.dumps(payload,ensure_ascii=False).replace('<','\\u003c')+'</script><script>'+script+'</script>'
    target=run/'interactive/circuitkaart.html';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(page('Interactieve circuitkaart',body))


def render(run,b,manifest):
    limit=b['config'].get('max_pit_detail_exports',len(b['cycles']))
    b['exported_cycle_ids']=[c['cycle_id'] for c in sorted(b['cycles'],key=lambda c:abs(c['gain_early_driver']),reverse=True)[:limit]]
    write_json(run/'data/derived/analysis.json',b)
    write_json(run/'data/derived/driver-styles.json',driver_styles(b['data']['drivers']))
    plots=[];reportdir=run/'reports';reportdir.mkdir(parents=True,exist_ok=True)
    docs=reports(b)
    for name,text in docs.items():
        if name!='bronnen-en-methode':continue
        (reportdir/(name+'.md')).write_text(text,encoding='utf-8')
        from .branding import language_controls,language_script
        (reportdir/(name+'.html')).write_text(page(text.splitlines()[0].lstrip('# '),language_controls()+'<nav><a href="../overzicht.html">← Overzicht</a><a href="'+name+'.md">Markdown</a></nav>'+markdown_html(text)+language_script()),encoding='utf-8')
    interactive(run,b)
    body='<a href="../../../..//index.html">← Alle analyses</a><h1>'+html.escape(b['data']['session']['circuit_short_name'])+' '+str(b['data']['session']['year'])+'</h1><p class="tag">Status: '+manifest['status']+' • '+manifest['created_at']+'</p>'
    body+='<nav>'+''.join('<a href="reports/'+name+'.html">'+html.escape(name.replace('-',' ').capitalize())+'</a>' for name in docs)+'</nav>'
    body+='<p><a href="interactive/circuitkaart.html">Interactieve circuitkaart</a> · <a href="exports/gebeurtenissen.csv">Gebeurtenissen CSV</a> · <a href="exports/gebeurtenissen.json">Gebeurtenissen JSON</a> · <a href="exports/kerncijfers.json">Kerncijfers</a> · <a href="exports/pitstopstrategie.csv">Pitstopcycli CSV</a> · <a href="manifest.json">Manifest en bronnen</a></p>'
    body+='<div class="grid">'+''.join('<div class="card"><h2>'+html.escape(title)+'</h2><a href="figures/png/'+name+'.png"><img loading="lazy" src="figures/png/'+name+'.png" alt="'+html.escape(title)+'"></a><a href="figures/svg/'+name+'.svg">SVG-export</a></div>' for name,title in plots)+'</div>'
    from .dashboard import dashboard
    dashboard(run,b,body)
    logs=run/'logs';logs.mkdir(exist_ok=True);(logs/'waarschuwingen.txt').write_text('\n'.join(b['warnings']))


def check_links(run):
    for p in [run/'overzicht.html', * (run/'reports').glob('*.html'), * (run/'interactive').glob('*.html')]:
        soup=BeautifulSoup(p.read_text(),'html.parser')
        for node in soup.find_all(['a','img']):
            url=node.get('href') or node.get('src')
            if not url or url.startswith(('#','http:','https:','data:')):continue
            target=(p.parent/unquote(urlparse(url).path)).resolve()
            if target.name=='index.html' and not target.exists():continue # global index is built after successful run
            if not target.exists():raise ValueError(f'Ontbrekende lokale link: {p.name} → {url}')


def update_index(root):
    """One successful latest pointer per year/race; no history in the catalogue."""
    root=Path(root);base=root/'analyses';base.mkdir(parents=True,exist_ok=True);rows=[]
    for pointer in sorted(base.glob('*/*/latest.json')):
        latest=read_json(pointer);run=pointer.parent/latest['run']
        if not (run/'manifest.json').is_file() or not (run/'overzicht.html').is_file():continue
        m=read_json(run/'manifest.json')
        if m['status'] not in ['volledig','gedeeltelijk']:continue
        rows.append({'year':m['input']['year'],'gp':m.get('session',{}).get('circuit_short_name',m['input']['gp']),
                     'race_date':m.get('session',{}).get('date_start',''),'created_at':m['created_at'],'status':m['status'],
                     'path':str(run.relative_to(base)),'meeting':m.get('meeting',{}).get('meeting_name',''),
                     'coverage_label':m.get('coverage_label','Uitgebreide timinganalyse'),'analysis_kind':m.get('analysis_kind','timinganalyse')})
    rows.sort(key=lambda r:(r['year'],r['race_date'],r['gp']))
    write_json(base/'index.json',rows)
    from .branding import branding,language_script,ensure_banner,with_hero_flag
    ensure_banner(root)
    from .catalogue import catalogue_body
    def body(prefix):
        return catalogue_body(root,rows,prefix)
    (base/'index.html').write_text(with_hero_flag(page('Overtake It Away · raceanalyses',body('')),base/'index.html',root))
    (root/'races.html').write_text(with_hero_flag(page('Overtake It Away · raceanalyses',body('analyses/')),root/'races.html',root))
    from .homepage import build as build_homepage
    build_homepage(root)
