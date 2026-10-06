from pathlib import Path
import json,re,unicodedata
af=json.load(open(Path(__file__).with_name('_af411_dc_checklists_wave16.json')))
rows=json.load(open(Path(__file__).resolve().parents[2]/'src/data/figure-archive/oneshot.json'))
def slug(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+','-',s).strip('-')
def money(s):
    m=re.search(r'[\d.]+',s or ''); return float(m.group()) if m else 0.0
out=[]
SUB={'action-figures':None,'deluxe':'Deluxe','crime-squad':'Crime Squad','duo-force':'Duo Force','vehicles-playsets':'Vehicles'}
SKIP_PLAY={'Batcave Command Center','Rogues Gallery'}
for r in af['kenner-batman-animated-series']:
    cat=r['cat']; name=r['name'].replace('’',"'")
    if name in SKIP_PLAY: continue
    if cat=='mask-of-the-phantasm': line,sub='Kenner Batman Mask of the Phantasm','Mask of the Phantasm'
    elif cat=='adventures-of-batman-robin': line,sub='Kenner Adventures of Batman & Robin','The Adventures of Batman & Robin'
    else:
        line='Kenner Batman The Animated Series'
        if cat=='action-figures': sub='Mail-Away' if r['wave']=='MailAway' else f"Series {r['wave']}"
        else: sub=SUB[cat]
    kind='vehicle' if cat=='vehicles-playsets' else 'figure'
    out.append(dict(id=f"ken-btas-w16-{slug(name)}-{r['fid']}",name=name,subtitle=sub,line=line,company='kenner',kind=kind,
        releaseDate=f"{r['year']}-01-01",msrp=money(r['retail']),scale='5"',demand=1.4,
        tags=['dc','af-checklist','wave16','kenner','batman-animated',slug(sub)]+(['vehicle'] if kind=='vehicle' else []),
        source='curated-dc-gap-wave16'))
    out[-1]['tags'].append('af411:'+r['fid'])
# McFarlane DC Retro
existing=[(slug(re.sub(r'\(.*?\)','',x['name'])),x['releaseDate'][:4]) for x in rows if x.get('company')=='mcfarlane' and x.get('line')=='DC Retro']
print('existing retro',existing)
SKIP_R={'Batman Lunch Box 4 Pack',"Villian's Lair Playset (Retro 66)",'Wayne Manor Library (Retro 66)','Batcave (Retro 66)'}
for r in af['retro-66']:
    if int(r['year'])>=2026 or r['name'] in SKIP_R: continue
    raw=r['name']; cat=r['cat']
    base=re.sub(r'\s*\((.*)\)\s*$','',raw).strip()
    m=re.search(r'\((.*)\)\s*$',raw); inner=m.group(1) if m else ''
    parts=[p.strip() for p in inner.split(' - ') if p.strip() and p.strip() not in ('Retro 66','DC Retro: Super Friends','The New Adventures of Batman','Retro','Gold Label - Retro 66')]
    parts=[p.replace('Retro 66','').strip() for p in parts if p.replace('Retro 66','').strip()]
    if 'Gold Label' in inner and 'Gold Label' not in parts: parts.append('Gold Label')
    base=base.replace('Bizzaro','Bizarro')
    name=base+(f" ({', '.join(parts)})" if parts else '')
    if cat=='super-friends': show='Super Friends'
    elif cat=='the-new-adventures-of-batman-action-figures': show='The New Adventures of Batman'
    elif 'Nightwing Comic' in raw or 'Comic' in inner: show="Batman '66 Comic"
    else: show="Batman '66"
    w=r['wave']
    sub=f"{show} " + (f"Wave {w}" if w.isdigit() else (f"{w} Exclusive" if w else '')).strip()
    sub=sub.strip()
    ch=slug(base); yr=r['year']
    if (ch,yr) in existing and cat=='super-friends' and 'Platinum' not in inner and 'Universe of Evil' not in inner:
        continue
    if base=='Nightwing Comic' and ('nightwing',yr) in existing: continue
    kind='vehicle' if cat=='vehicles-and-playsets' else 'figure'
    out.append(dict(id=f"mcf-dcretro-w16-{slug(name)}-{r['fid']}",name=name,subtitle=sub,line='DC Retro',company='mcfarlane',kind=kind,
        releaseDate=f"{yr}-01-01",msrp=money(r['retail']),scale='6"',demand=1.3,
        tags=['dc','af-checklist','wave16','mcfarlane','dc-retro',slug(show)]+(['vehicle'] if kind=='vehicle' else []),
        source='curated-dc-gap-wave16'))
    out[-1]['tags'].append('af411:'+r['fid'])
ids=[o['id'] for o in out]; assert len(ids)==len(set(ids))
keys=[(o['line'],o['name'],o['subtitle']) for o in out]; 
from collections import Counter
print([k for k,v in Counter(keys).items() if v>1])
json.dump(out,open(Path(__file__).with_name('_dc_gap_wave16_data.json'),'w'),indent=1,ensure_ascii=False)
print(len(out))
for o in out:
    if o['company']=='mcfarlane': print(o['name'],'|',o['subtitle'],o['releaseDate'],o['msrp'])
