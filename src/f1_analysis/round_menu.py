"""Shared sticky timing-style toolbar with an accessible two-thumb lap range."""
CSS='''
.dash-controls{position:sticky!important;top:0;z-index:40;background:#080a10f5!important;border:1px solid #343f50!important;border-top:3px solid #ff4758!important;border-radius:3px!important;padding:12px 16px!important;display:flex;flex-wrap:wrap;align-items:center!important;gap:12px;box-shadow:0 5px 18px #0004}
.dash-controls button,.dash-controls select{background:#151b26;color:#fff;border:1px solid #596273;border-radius:2px;font-weight:800;font-size:13px;padding:9px 12px}
.dash-controls button:disabled{color:#626b79;background:#10141b;border-color:#303743;cursor:default;opacity:.55;outline:0}
.lap-range{width:clamp(230px,30vw,430px);flex:1 1 260px;max-width:500px}.range-heading{display:flex;justify-content:space-between;font-size:14px;font-weight:900;font-style:italic}.range-heading output{color:#fff;font-variant-numeric:tabular-nums}
.range-slider{height:34px;position:relative;margin-top:3px;--low:0%;--high:100%}.range-rail{position:absolute;left:10px;right:10px;top:15px;height:4px;background:linear-gradient(to right,#343f50 0%,#343f50 var(--low),#ff4758 var(--low),#ff4758 var(--high),#343f50 var(--high),#343f50 100%);border-radius:3px;pointer-events:none}
.range-slider input[type=range]{position:absolute;inset:0;width:100%;height:34px;margin:0;padding:0;border:0;appearance:none;-webkit-appearance:none;background:transparent;pointer-events:none;cursor:pointer}
.range-slider input[type=range]::-webkit-slider-runnable-track{height:4px;background:transparent}.range-slider input[type=range]::-moz-range-track{height:4px;background:transparent}
.range-slider input[type=range]::-webkit-slider-thumb{appearance:none;-webkit-appearance:none;width:20px;height:20px;border-radius:50%;background:#fff;border:3px solid #ff4758;margin-top:-8px;pointer-events:auto;box-shadow:0 2px 6px #0008}
.range-slider input[type=range]::-moz-range-thumb{width:14px;height:14px;border-radius:50%;background:#fff;border:3px solid #ff4758;pointer-events:auto;box-shadow:0 2px 6px #0008}
.range-slider input[type=range]:focus-visible{outline:0}.range-slider input[type=range]:focus-visible::-webkit-slider-thumb{outline:3px solid #51d6dd;outline-offset:2px}.range-slider input[type=range]:focus-visible::-moz-range-thumb{outline:3px solid #51d6dd;outline-offset:2px}
.range-endpoints{display:flex;justify-content:space-between;font-size:11px;color:#b3bece}.dash-controls .toolbar-actions{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
html{scroll-padding-top:150px}
.dash-controls .toolbar-actions button{box-sizing:border-box;font:800 13px system-ui;padding:9px 12px;border:1px solid #596273;border-top:3px solid #ff4758;background:#080a10f5;color:#fff;border-radius:2px;white-space:nowrap}
.dash-controls .toolbar-actions button:hover:not(:disabled),.dash-controls .toolbar-actions button:focus-visible:not(:disabled){border-color:#ff4758;outline:2px solid #ff4758}
.dash-controls .toolbar-actions button:disabled{border-top-color:#ff4758;color:#626b79;background:#080a10f5;outline:0}

'''


def toolbar(last, archive=False):
    last=max(1,int(last));left,right=('from','to') if archive else ('round-min','round-max')
    extra='' if archive else '<button id="zoom-out">Uitzoomen</button>'
    return f'''<style>{CSS}</style><section class="dash-controls" aria-label="Racefilters"><div class="lap-range"><div class="range-heading"><span>RONDE</span><output id="range-value" aria-live="polite">1–{last}</output></div><div class="range-slider" id="range-slider"><div class="range-rail"></div><input id="{left}" type="range" min="1" max="{last}" step="1" value="1" aria-label="Vanaf ronde"><input id="{right}" type="range" min="1" max="{last}" step="1" value="{last}" aria-label="Tot en met ronde"></div><div class="range-endpoints"><span>1</span><span>{last}</span></div></div><div class="toolbar-actions"><button id="reset">RESET</button><button id="previous-range" aria-label="Vorige rondereeks">← REEKS</button><button id="next-range" aria-label="Volgende rondereeks">REEKS →</button>{extra}</div></section>'''
