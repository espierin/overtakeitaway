"""Build the small offline subtitle font and deterministic, bitmap-preserving logo layout."""
from pathlib import Path
from base64 import b64encode
from io import BytesIO
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

root=Path(__file__).resolve().parents[1]
source=root/'storage/vector-wordmark/fonts/Montserrat-Italic.ttf'
font=instantiateVariableFont(TTFont(source),{'wght':600},inplace=True)
options=subset.Options();options.name_IDs=['*'];options.name_languages=['*']
subsetter=subset.Subsetter(options=options)
subsetter.populate(text='Geen fabels maar feitenA reality check on heroic stories.')
subsetter.subset(font)
# Use a project name for the subset, preserving the original copyright/licence metadata.
for record in font['name'].names:
    if record.nameID in (1,4,6,16):
        name='OvertakeTagline' if record.nameID==6 else 'Overtake Tagline'
        record.string=name.encode(record.getEncoding(),errors='replace')
font.flavor='woff';buffer=BytesIO();font.save(buffer)
css='''/* Montserrat SemiBold Italic, subset under SIL OFL 1.1; original bitmap stays unchanged. */
@font-face{font-family:"Overtake Tagline";src:url(data:font/woff;base64,FONT_DATA) format("woff");font-weight:600;font-style:italic;font-display:block}
.race-hero .site-brand>.site-home-link{width:min(600px,100%)!important;max-width:100%;container-type:inline-size}.home-hero.race-hero .site-brand>.site-home-link{width:min(600px,100%)!important}.logo-link:has(.site-wordmark-window){width:540px;max-width:100%;container-type:inline-size;text-decoration:none}
.site-wordmark-window{display:block;width:100%;aspect-ratio:2172/263.5;overflow:hidden;background:#000;box-shadow:0 0 18px 12px #000}
.site-wordmark-window>img{display:block!important;width:100%!important;max-width:100%!important;height:auto!important;aspect-ratio:6.4!important;object-fit:cover!important;object-position:center!important;background:#000;box-shadow:none!important;filter:none!important;transform:translateX(-2.95%);clip-path:polygon(0 0,100% 0,100% 77.4%,70.44% 77.4%,70.44% 73%,0 73%)}
.site-brand .site-home-link>.site-tagline,.logo-link>.site-tagline{position:static!important;display:block!important;width:auto!important;height:auto!important;padding:0!important;margin:-.8cqw 0 0 0!important;overflow:visible!important;clip-path:none!important;white-space:nowrap;font-family:"Overtake Tagline",sans-serif!important;font-weight:600!important;font-style:italic!important;font-size:4.4cqw!important;line-height:1!important;letter-spacing:-.015em;color:#b7c0d0!important;text-align:left;text-shadow:none!important;transform:scaleX(.86);transform-origin:left center}
.race-hero h1,.race-hero .dash-header h1{margin-left:0!important;max-width:100%!important}.race-hero .race-metadata,.race-hero #lab-subtitle{margin-left:0!important}
@media(max-width:1400px){.race-hero .site-brand>.site-home-link{width:min(600px,100%)!important}}
'''.replace('FONT_DATA',b64encode(buffer.getvalue()).decode())
for dest in [root/'src/f1_analysis/site-branding.css',root/'assets/site-branding.css']:
    dest.write_text(css)
license_text=(root/'storage/vector-wordmark/fonts/OFL.txt').read_text()
license_text=license_text[license_text.index('This Font Software'):]
license_text='Copyright 2011 The Montserrat Project Authors (https://github.com/JulietaUla/Montserrat)\n\n'+license_text
for directory in [root/'assets/fonts',root/'src/f1_analysis/assets']:
    directory.mkdir(exist_ok=True,parents=True)
    (directory/'Montserrat-OFL.txt').write_text(license_text)
print(f'Offline subtitle font: {len(buffer.getvalue())} bytes; shared CSS: {len(css)} bytes')
