#!/usr/bin/env python3
"""review/index.py ROOT : write ROOT/INDEX.html from every ROOT/<file>/*.json pair record (+ ROOT/viewer 3D pairs listed in ROOT/pairs3d.json if present).
Thumbnail grid grouped by type; click opens a viewer with Revit | Ours | Swipe | Diff | Side-by-side, space toggles Revit/Ours, arrows move to the next pair."""
import sys, os, json, glob, html
root = sys.argv[1]; recs = []
for p in sorted(glob.glob(os.path.join(root, '*', '*.json'))):
    try: m = json.load(open(p))
    except Exception: continue
    if 'path' in m and 'type' in m: recs.append(m)
extra = os.path.join(root, 'pairs3d.json')
seen = {m['path'] for m in recs}
if os.path.exists(extra): recs += [m for m in json.load(open(extra)) if m['path'] not in seen]
ORDER = ['sheet', 'plan', 'section', 'elevation', 'detail', 'schedule', '3d', 'other']
TITLE = dict(sheet='Sheets', plan='Plans', section='Sections', elevation='Elevations', detail='Details / drafting', schedule='Schedules / legends', other='Other')
TITLE['3d'] = '3D views'
recs.sort(key=lambda m: (ORDER.index(m['type']) if m['type'] in ORDER else 99, m['file'], int(m['id'])))
data = json.dumps(recs)
cards = []
for i, m in enumerate(recs):
    flag = (' <b class=ap>framing approx</b>' if m.get('approx') else '') + (' <b class=fn>fonts: %d</b>' % len(m['fontcrops']) if m.get('fontcrops') else '')
    sc = '' if m.get('score') is None else ' QA %s' % m['score']
    cards.append((m['type'], '<a class=card href="#" onclick="openPair(%d);return false"><img loading=lazy src="%s__thumb.jpg"><div><b>%s</b> <i>%s</i><br>%s #%s%s%s</div></a>' % (i, html.escape(m['path']), html.escape(str(m['name'])), m['type'], html.escape(m['file']), m['id'], sc, flag)))
body = []
for t in ORDER:
    c = [x for ty, x in cards if ty == t]
    if c: body.append('<h2 id="%s">%s (%d)</h2><div class=grid>%s</div>' % (t, TITLE.get(t, t), len(c), ''.join(c)))
nav = ' '.join('<a href="#%s">%s</a>' % (t, TITLE.get(t, t)) for t in ORDER if any(ty == t for ty, _ in cards))
page = '''<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Revit vs ours review</title>
<style>body{font:14px system-ui,sans-serif;margin:16px;background:#fafafa;color:#222}h1{margin:0 0 6px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:10px}
.card{display:block;background:#fff;border:1px solid #ccc;border-radius:6px;padding:6px;text-decoration:none;color:inherit}.card img{width:100%%;height:auto;display:block;background:#fff}.card div{margin-top:4px;font-size:12px}
.ap{color:#b60}.fn{color:#a2a}nav a{margin-right:12px}#v{position:fixed;inset:0;background:#222;display:none;flex-direction:column}#bar{padding:6px 10px;background:#111;color:#eee;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
#bar button{padding:4px 10px}#bar button.on{background:#7af}#st{flex:1;overflow:auto;position:relative}#st img{display:block;max-width:none}
#sw{position:relative;display:inline-block}#sw img.top{position:absolute;left:0;top:0}
@media(prefers-color-scheme:dark){body{background:#181818;color:#ddd}.card{background:#222;border-color:#444}}</style>
<h1>Revit vs rvt-viewer (ours): review pairs</h1><p>Legend of the Diff view: cyan = only in Revit, red = only in ours, grey = both. Space toggles Revit/Ours, arrows go to the next/previous pair, Esc closes. Local use only (Autodesk-derived).</p>
<nav>%s</nav>%s
<div id=v><div id=bar><b id=ttl></b><button data-m=revit>Revit</button><button data-m=ours>Ours</button><button data-m=swipe>Swipe</button><button data-m=diff>Diff</button><button data-m=side>Side by side</button><button data-m=fonts>Fonts</button>
<label>fit <input type=checkbox id=fit checked></label><input type=range id=rng min=0 max=100 value=50 style="width:240px"><span id=info></span><button onclick="closeV()">close</button></div><div id=st></div></div>
<script>
const D=%s;let cur=0,mode='revit';const st=document.getElementById('st'),fit=document.getElementById('fit'),rng=document.getElementById('rng');
function img(s,cls){const i=new Image();i.src=D[cur].path+'__'+s+'.png';if(fit.checked){i.style.maxWidth='100%%';i.style.maxHeight='calc(100vh - 60px)';i.style.objectFit='contain'}if(cls)i.className=cls;return i}
function show(){const m=D[cur];document.getElementById('ttl').textContent=m.file+' / '+m.name+' ('+m.id+')';
document.getElementById('info').textContent=(m.score==null?'':'QA '+m.score+'  ')+'reg '+m.reg_score+(m.approx?'  FRAMING APPROX':'')+'  '+m.size[0]+'x'+m.size[1]+(m.camera?'  camera '+m.camera:'');
document.querySelectorAll('#bar button[data-m]').forEach(b=>b.classList.toggle('on',b.dataset.m==mode));st.innerHTML='';
if(mode=='swipe'){const w=document.createElement('div');w.id='sw';const a=img('revit'),b=img('ours','top');w.append(a,b);st.append(w);const f=()=>{b.style.clipPath='inset(0 0 0 '+rng.value+'%%)'};rng.oninput=f;f()}
else if(mode=='fonts'){const fc=m.fontcrops||[];if(!fc.length){st.textContent='No font differences recorded for this pair (run a QA sweep with the font check, then rebuild).';st.style.color='#eee'}else fc.forEach(c=>{const x=new Image();x.src=m.path.split('/').slice(0,-1).join('/')+'/'+c.img;x.style.maxWidth='100%%';x.style.display='block';x.style.margin='6px 0';st.append(x)})}
else st.append(img(mode))}
function openPair(i){cur=i;document.getElementById('v').style.display='flex';show()}function closeV(){document.getElementById('v').style.display='none'}
document.querySelectorAll('#bar button[data-m]').forEach(b=>b.onclick=()=>{mode=b.dataset.m;show()});fit.onchange=show;
addEventListener('keydown',e=>{if(document.getElementById('v').style.display!='flex')return;if(e.key==' '){e.preventDefault();mode=mode=='revit'?'ours':'revit';show()}
else if(e.key=='ArrowRight'){cur=(cur+1)%%D.length;show()}else if(e.key=='ArrowLeft'){cur=(cur+D.length-1)%%D.length;show()}else if(e.key=='Escape')closeV()});
</script>''' % (nav, ''.join(body), data)
open(os.path.join(root, 'INDEX.html'), 'w').write(page); print('INDEX.html', len(recs), 'pairs')
