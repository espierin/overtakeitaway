"""Persistent broadcast-style race driver selector shared by both dashboards."""
import html
from .io import slug

CSS='''
body{max-width:none!important;margin:0!important;padding:30px 30px 30px 224px!important}
.driver-sidebar{position:fixed;left:18px;top:18px;bottom:18px;width:176px;z-index:50;display:flex;flex-direction:column;background:#07090ded;border:1px solid #343f50;border-top:3px solid #ff4b56;box-shadow:0 8px 24px #0005;border-radius:3px;overflow:hidden}
.driver-sidebar h2{border:0;padding:12px 10px 8px;margin:0;text-align:center;font-size:18px;font-weight:900;font-style:italic;letter-spacing:.06em}
.driver-sidebar .driver-picker-list{min-height:0;overflow-y:auto;flex:1;scrollbar-width:thin}
.driver-sidebar .driver-row{display:grid;grid-template-columns:38px 5px 1fr;align-items:center;gap:10px;width:100%;height:clamp(24px,calc((100dvh - 156px)/var(--driver-count)),34px);margin:0;padding:0 10px 0 0;border:0;border-bottom:1px solid #ffffff16;border-radius:0;background:#080a10;text-align:left;cursor:pointer;outline:0;font-style:normal;color:#fff;opacity:.38;transition:opacity .12s,background .12s}
.driver-sidebar .driver-code{white-space:nowrap;overflow-wrap:normal;word-break:normal}
.driver-sidebar .driver-row[aria-pressed=true]{opacity:1;background:#10131b;outline:0}
.driver-sidebar .driver-row:hover,.driver-sidebar .driver-row:focus-visible{background:#26303e;outline:2px solid #51d6dd;outline-offset:-2px}
.driver-sidebar .driver-row[aria-pressed=false]{opacity:.38!important;filter:grayscale(1);background:#080a10!important}
.driver-sidebar .driver-number{height:calc(100% - 4px);min-width:0;display:grid;place-items:center;background:#fff;color:#080a10;font-size:19px;font-weight:900;font-style:italic;border-radius:2px;margin:2px 0 2px 3px;font-variant-numeric:tabular-nums}
.driver-sidebar .team-stripe{width:5px;height:68%;background:var(--team-color)}
.driver-sidebar .driver-code{font-size:21px;font-weight:900;letter-spacing:.025em;line-height:1}
.driver-sidebar .sidebar-teams{flex:none;max-height:40%;overflow:auto;border-top:1px solid #343f50}.driver-sidebar .sidebar-teams summary{padding:10px;font-size:13px;cursor:pointer;font-weight:800}.driver-sidebar .team-chip{display:block;width:calc(100% - 12px);margin:6px;border:0;border-left:4px solid var(--team-color);text-align:left;padding:8px;background:#151b26;color:#fff;font-size:12px}.driver-sidebar .team-chip[aria-pressed=true]{background:#344154;outline:1px solid var(--team-color)}.driver-sidebar footer{flex:none;border-top:2px solid #343f50;padding:8px;display:grid;grid-template-columns:1fr 1fr;gap:6px;background:#080a10}
.driver-sidebar footer button{font-size:13px;font-weight:800;font-style:italic;background:#151b26;color:#fff;border:1px solid #596273;border-radius:2px;padding:8px 2px;cursor:pointer}
body.has-highlight .driver-sidebar [data-driver]{opacity:1}body.has-highlight .driver-sidebar .driver-row[aria-pressed=false]{opacity:.38}
@media(max-width:850px){body{padding:16px 12px 16px 158px!important}.driver-sidebar{left:8px;top:8px;bottom:8px;width:134px}.driver-sidebar .driver-row{grid-template-columns:31px 4px 1fr;gap:7px}.driver-sidebar .driver-number{font-size:16px}.driver-sidebar .driver-code{font-size:18px}.driver-sidebar h2{font-size:14px}.driver-sidebar .sidebar-teams{flex:none;max-height:40%;overflow:auto;border-top:1px solid #343f50}.driver-sidebar .sidebar-teams summary{padding:10px;font-size:13px;cursor:pointer;font-weight:800}.driver-sidebar .team-chip{display:block;width:calc(100% - 12px);margin:6px;border:0;border-left:4px solid var(--team-color);text-align:left;padding:8px;background:#151b26;color:#fff;font-size:12px}.driver-sidebar .team-chip[aria-pressed=true]{background:#344154;outline:1px solid var(--team-color)}.driver-sidebar footer{padding:5px;gap:4px}}
@media(max-width:520px){body{padding-left:126px!important}.driver-sidebar{width:106px}.driver-sidebar .driver-row{grid-template-columns:28px 4px 1fr;gap:5px}.driver-sidebar .driver-code{font-size:16px}.driver-sidebar footer button{font-size:11px}}
'''


def sidebar(drivers, all_id='select-all', none_id='select-none', archive=False):
    esc=lambda v:html.escape(str(v),quote=True)
    rows=sorted(drivers,key=lambda d:(d.get('surname') or d['name'].split(' ')[-1]).casefold())
    content=f'<aside class="driver-sidebar" aria-label="Rijdersfilter" style="--driver-count:{max(1,len(rows))}"><h2>COUREURS</h2><div id="'+('drivers' if archive else 'driver-picker')+'" class="driver-picker-list">'
    for d in rows:
        number=d.get('display_number',d.get('number',d.get('driver_number')));value=d['id'] if archive else d['driver_number']
        code=d.get('code') or slug(d.get('surname') or d['name'].split(' ')[-1]).replace('-','')[:3].upper()
        color=d.get('color') or '#B3BECE'
        attrs=f'data-entry-filter="{esc(value)}"' if archive else f'data-action="driver" data-value="{esc(value)}" data-driver="{esc(value)}"'
        content+=f'<button class="driver-chip driver-row" {attrs} aria-pressed="true" title="{esc(d["name"])} · {esc(d.get("team",""))}" aria-label="{esc(d["name"])} selecteren" style="--team-color:{esc(color)}"><span class="driver-number">{esc(number if number is not None else "?")}</span><span class="team-stripe" aria-hidden="true"></span><span class="driver-code">{esc(code)}</span></button>'
    content+='</div><details class="sidebar-teams"><summary>Teams selecteren</summary><div id="team-picker">'
    teams={}
    for d in rows:teams.setdefault(d.get('team') or 'Onbekend',[]).append(d)
    for team,members in sorted(teams.items()):
        key=members[0].get('team_id',team)
        attr=f'data-team-filter="{esc(key)}"' if archive else f'data-action="team" data-value="{esc(",".join(str(d["driver_number"]) for d in members))}"'
        content+=f'<button class="team-chip" {attr} aria-pressed="false" style="--team-color:{esc(members[0].get("color") or "#B3BECE")}">{esc(team)}</button>'
    content+='</div></details>'
    content+=f'<footer><button id="{all_id}"'+('' if archive else ' data-action="drivers-all"')+'>ALLES</button><button id="'+none_id+'"'+('' if archive else ' data-action="drivers-none"')+'>NIETS</button></footer></aside>'
    return '<style>'+CSS+'</style>'+content
