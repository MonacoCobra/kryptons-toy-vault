"""Generate curated DC gap wave17 rows from the AF411 checklist snapshot.

Picks were hand-verified against oneshot.json (company + line + character +
year/variant) on 2026-10-07; only AF411 figure ids listed below are emitted.
"""
from pathlib import Path
import json, re, unicodedata
HERE = Path(__file__).parent
af = json.load(open(HERE / '_af411_dc_checklists_wave17.json'))

def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')

def money(s):
    m = re.search(r'[\d.]+', (s or '').replace(',', ''))
    return float(m.group()) if m else 0.0

DCC_SKIP = {'Batman and Phantasm (Mask of the Phantasm)', 'Etrigan and Klarion (The New Batman Adventures)',
            'Batman and Bruce Wayne (Batman Beyond)'}
DCC_PICK_FIDS = {'11996','11997','11945','11952','11953','11954','11956','11959','11960','11961','11962','11964','11966','11980','11981','11987','11988','11989','11990','11991','11992','11993','11994','11999','7812','11998','12000','12001','12002'}  # AF411 ids verified missing from catalog
PP_PICK = {'Batman Beyond (Neo-Year)', 'Batman Who Laughs & Red Death (Dark Nights Metal #1)',
    'Batman & Mutant Leader (The Dark Knight Returns)', 'Batman of Earth-44 & Batman of Earth-11 (Dark Nights Metal)',
    'The Dark Knight Returns 4 Pack (Gold Label - The Dark Knight Returns)', 'Green Arrow (Injustice 2)',
    'Captain Cold (The Flash)', 'Heat Wave (The Flash)', 'Captain Cold (Gold Label - The Flash)', 'Aqualad (Aquaman)',
    'Ocean Master (Aquaman)', 'Ghost of Krypton (Sketch Edition - Gold Label) 4 Pack', 'Earth-2 Superman (Ghosts of Krypton)',
    'Ghost of Zod (Ghosts of Krypton)', 'Deathstroke (DC Rebirth)', 'Extant (Zero Hour)', 'Damage (Red Platinum - Kingdom Come)',
    'Starman (Red Platinum - Kingdom Come)', 'Supergirl (Woman of Tomorrow)', 'Steve Trevor (Red Platinum - Wonder Woman #1)',
    'Superboy (Superboy #1)', 'Mr. Bones (Gold Label Infinity Inc #16 - Lithograph)', 'Obsidian (Gold Label Infinity Inc #16 - Lithograph)'}
SP_PICK = {'Batman, Superman & Wonder Woman (Gold Label - Black & White Accent Edition)', 'Black Manta (Crowdfund)',
    'Superman Movie 5 Pack (Gold Label - Superman Movie)', 'Batman with Batwing and Whirlybat (Gold Label)',
    'The Bat Multicraft (Batman\'s Multi Terrain)', 'Fortress of Solitude with Robot (Gold Label - Superman Movie)',
    'T-Craft (Superman Movie)', 'T-Craft with Mr. Terrific (Gold Label - Superman Movie)'}
DCUC_PICK = {'Mary Batson (White)', 'Mary Batson (Red)', 'Martian Manhunter (Blade Hand)', 'El Acertijo (Riddler)',
    'Mr Mxyzptlk', 'Gold Superman'}

out = []
def add(prefix, a, name, sub, line, company, kind, scale, extra_tags):
    out.append(dict(id=f"{prefix}-w17-{slug(name)}-{a['fid']}", name=name, subtitle=sub, line=line, company=company,
        kind=kind, releaseDate=f"{a['year']}-01-01", msrp=money(a['retail']), scale=scale, demand=1.3,
        tags=['dc', 'af-checklist', 'wave17'] + extra_tags + (['vehicle'] if kind == 'vehicle' else []) + ['af411:' + a['fid']],
        source='curated-dc-gap-wave17'))

for a in af['dc-collectibles']:
    n = a['name'].replace('’', "'")
    if a['fid'] not in DCC_PICK_FIDS or n in DCC_SKIP or int(a['year']) >= 2026:
        continue
    kind = 'vehicle' if a['cat'] == 'vehicles-and-playsets' else 'figure'
    m = re.search(r'\(([^()]*)\)\s*$', n)
    inner = m.group(1) if m else ''
    base = re.sub(r'\s*\([^()]*\)\s*$', '', n).strip() if inner in (
        'The New Batman Adventures', 'Batman: The Animated Series') else n
    if 'New Batman Adventures' in inner:
        line, sub = 'DC Collectibles New Batman Adventures', 'The New Batman Adventures'
    else:
        line, sub = 'DC Collectibles Batman Animated', 'Batman The Animated Series'
    if a['num']:
        sub += f" #{a['num']}"
    add('dcc-btas', a, base, sub, line, 'dcdirect', kind, '6"', ['dc-collectibles', 'batman-animated'])

for a in af['page-punchers']:
    n = a['name'].replace('’', "'")
    if n not in PP_PICK:
        continue
    size = '3"' if a['cat'].startswith('3-') else '7"'
    w = a['wave']
    sub = f"Page Punchers {size}" + (f" Wave {w}" if w.isdigit() else (f" {w}" if w else ''))
    add('mcf-pp', a, n, sub, 'Page Punchers', 'mcfarlane', 'figure', size, ['mcfarlane', 'page-punchers'])

for a in af['mcfarlane-super-powers']:
    n = a['name'].replace('’', "'")
    if n not in SP_PICK:
        continue
    kind = 'vehicle' if a['cat'] == 'vehicles-and-playsets' else 'figure'
    w = a['wave']
    sub = 'Super Powers' + (f" Wave {w}" if w.isdigit() else (f" {w} Exclusive" if w and w != 'Crowdfund' else (' Crowdfund' if w else '')))
    add('mcf-sp', a, n, sub, 'DC Super Powers', 'mcfarlane', kind, '4.5"', ['mcfarlane', 'super-powers'])

for a in af['dc-universe-classics']:
    n = a['name'].replace('’', "'")
    if n not in DCUC_PICK:
        continue
    w = a['wave']
    cc = a['cat'].replace('-collect-connect', '').replace('-', ' ').title()
    sub = (f"Wave {w} ({cc} C&C)" if w.isdigit() else f"{w} Exclusive ({cc} C&C)")
    add('mat-dcuc', a, n, sub, 'DC Universe Classics', 'mattel', 'figure', '6"', ['mattel', 'dcuc'])

ids = [o['id'] for o in out]; assert len(ids) == len(set(ids))
json.dump(out, open(HERE / '_dc_gap_wave17_data.json', 'w'), indent=1, ensure_ascii=False)
from collections import Counter
print(len(out), Counter(o['line'] for o in out))
for o in out: print(o['company'], '|', o['line'], '|', o['name'], '|', o['subtitle'], o['releaseDate'][:4], o['msrp'])
