"""Download a CPBL season and rebuild pool_cpbl.json.

    python3 source/fetch_cpbl.py 2026

Stats and advanced stats come from 野球革命 (rebas.tw); each hitter's main fielding
position comes from the 中華職棒 official site (cpbl.com.tw), which lists plate
appearances by defensive position. Then run source/build.py.
"""
import json, os, re, sys, time, urllib.parse, urllib.request, http.cookiejar

YEAR = sys.argv[1] if len(sys.argv) > 1 else '2026'
SRC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SRC, 'pool_cpbl.json')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36'
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def get(url, data=None, tries=3):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={'User-Agent': UA})
            with opener.open(req, timeout=120) as r:
                return r.read().decode('utf-8')
        except Exception as e:
            if k == tries - 1:
                raise
            print('  retry', url[:80], e)
            time.sleep(3)


# ---------- 野球革命 ----------
league = json.loads(get('https://www.rebas.tw/api/leagues/CPBL'))['data']
season = next(s for s in league['seasons'] if s['year'] == int(YEAR) and s['type'] == 'LEAGUE_MATCHES')
SID = season['uniqid']
print('rebas season', SID, season['title'])


def leaders(kind, section):
    # pa is a fraction of the qualifying threshold; 0.01 returns nearly everyone who appeared
    url = f'https://www.rebas.tw/api/seasons/{SID}/leaders?type={kind}&section={section}&pa=0.01'
    rows = json.loads(get(url))['data']
    print(' ', kind, section, len(rows))
    return {r['player']['uniqid']: r for r in rows}


bstd, badv = leaders('batter', 'standard'), leaders('batter', 'advanced')
pstd, padv = leaders('pitcher', 'standard'), leaders('pitcher', 'advanced')
wrc = {r['id']: r for r in json.loads(get(f'https://www.rebas.tw/api/wrc_plus?season_id={SID}'))['data']}
uzr = {}  # player -> {position code: row}; a player can have rows at several positions
for r in json.loads(get(f'https://www.rebas.tw/api/uzr?season_id={SID}'))['data']:
    uzr.setdefault(r['id'], {})[r['position']] = r
frm = {r['id']: r['framingRuns'] for r in json.loads(get(f'https://www.rebas.tw/api/catcher_framing?season_id={SID}'))['data']}
POSNUM = {'1B': '3', '2B': '4', '3B': '5', 'SS': '6', 'LF': '7', 'CF': '8', 'RF': '9'}
def uzr_for(pid, pos):
    rows = uzr.get(pid, {})
    if POSNUM.get(pos) in rows:
        return rows[POSNUM[pos]]['UZR']
    return max(rows.values(), key=lambda r: r['innings'])['UZR'] if rows else None
team_rows = json.loads(get(f'https://www.rebas.tw/api/seasons/{SID}/teams'))['data']
teams = {t['origin']['abbr']: t['name'] for t in team_rows}  # player rows carry only the one-character abbreviation

# ---------- 中華職棒官網: plate appearances by defensive position ----------
page = get('https://www.cpbl.com.tw/stats/recordall')
tok = re.search(r'name="__RequestVerificationToken" type="hidden" value="([^"]+)"', page).group(1)
POSCODE = {'0': 'DH', '2': 'C', '3': '1B', '4': '2B', '5': '3B', '6': 'SS', '7': 'LF', '8': 'CF', '9': 'RF'}
pos_pa = {}  # (name) -> {pos: PA}
for code, pos in POSCODE.items():
    n_rows = 0
    for idx in range(1, 20):
        form = urllib.parse.urlencode({'__RequestVerificationToken': tok, 'Year': YEAR, 'KindCode': 'A', 'Position': '01',
                                       'Online': '01', 'DefenceType': code, 'Sortby': '', 'PageSize': '60',
                                       'IndexOfPages': str(idx), 'ExecAction': 'Q'}).encode()
        html = get('https://www.cpbl.com.tw/stats/recordall', form)
        rows = re.findall(r'<tr.*?</tr>', html, re.S)[1:]
        new = 0
        for r in rows:
            m = re.search(r'<span class="name"><a[^>]*>([^<]+)</a>', r)
            cells = [re.sub(r'<[^>]+>', '', c).strip() for c in re.findall(r'<td class="num">(.*?)</td>', r, re.S)]
            # numeric cells: AVG, G, PA, ...
            if not m or len(cells) < 3:
                continue
            name, pa = m.group(1).strip(), int(cells[2])
            key = (name, pos)
            if key in pos_pa:
                continue
            pos_pa[key] = pa
            new += 1
        n_rows += new
        if len(rows) < 60 or new == 0:
            break
    print('  cpbl', pos, n_rows)

by_name = {}
for (name, pos), pa in pos_pa.items():
    by_name.setdefault(name, {})[pos] = pa


# ---------- build pool ----------
def f3(x):
    return ('%.3f' % x).replace('0.', '.', 1) if x < 1 else '%.3f' % x


pc = lambda v: None if v is None else v / 100
pool = []
for pid, s in bstd.items():
    pa = s['PA']
    if pa < 60:
        continue
    a, w, pl = badv.get(pid, {}), wrc.get(pid, {}), s['player']
    name = pl['name']
    poss = by_name.get(name)
    pos = max(poss, key=poss.get) if poss else 'DH'
    h, d2, d3, hr = s['H'], s['Double'], s['Triple'], s['HR']
    att = (s['SB'] + s['CS']) / pa
    pool.append(dict(id='c' + pid, n=name, zh=None, t=teams.get(pl['team_abbr'], pl['team_abbr']), pos=pos, type='H',
        pa=pa, avg=f3(a.get('AVG', h / max(1, s['AB']))), obp=f3(a.get('OBP', 0)), slg=f3(a.get('SLG', 0)), ops=f3(a.get('OPS', 0)),
        hr=hr, rbi=s['RBI'], sb=s['SB'],
        r=dict(k=s['SO'] / pa, bb=(s['BB'] + s['HBP']) / pa, s1=(h - d2 - d3 - hr) / pa, s2=d2 / pa, s3=d3 / pa, hr=hr / pa,
               gidp=s['GIDP'] / pa, sbr=s['SB'] / pa),
        woba=a.get('wOBA'), wrc=w.get('wrcPlus'), opsp=a.get('OPSplus'), iso=a.get('ISO'), whiff=pc(a.get('Whiffp')), gbp=pc(a.get('GBp')),
        uzr=uzr_for(pid, pos), frm=frm.get(pid) if pos == 'C' else None,
        spd=round(26 + min(3.5, att * 70), 1)))  # no sprint data in CPBL: steal attempts stand in for speed

for pid, s in pstd.items():
    outs, bf, g, gs = s['IPOut'], s['BF'], s['games'], s['SP']
    sv = s['R_SV']
    if gs >= 8 and outs >= 120:
        role = 'SP'
    elif sv >= 8:
        role = 'CL'
    elif gs <= 3 and outs >= 45:
        role = 'RP'
    else:
        continue
    a, pl = padv.get(pid, {}), s['player']
    h, d2, d3, hr = s['H'], s['Double'], s['Triple'], s['HR']
    era, fip = s['ERA'], a.get('FIP')
    pool.append(dict(id='c' + pid, n=pl['name'], zh=None, t=teams.get(pl['team_abbr'], pl['team_abbr']), pos=role, type='P',
        g=g, gs=gs, ip=f'{outs // 3}.{outs % 3}', era='%.2f' % era, whip='%.2f' % a.get('WHIP', 0), w=s['R_W'], l=s['R_L'],
        sv=sv, hld=s['R_H'], so=s['SO'],
        r=dict(k=s['SO'] / bf, bb=s['BB'] / bf, s1=(h - d2 - d3 - hr) / bf, s2=d2 / bf, s3=d3 / bf, hr=hr / bf),
        bfg=bf / max(1, g), np=s['NP'] / max(1, g), ppa=s['NP'] / max(1, bf), velo=None, fip=fip, erap=a.get('ERAplus'), whiff=pc(a.get('Whiffp')), gbp=pc(a.get('GBp')), opsp=a.get('OPSplus'),
        # half-weight FIP regression on hits allowed, the CPBL stand-in for Statcast's expected stats
        m=max(.8, min(1.25, (.5 * era + .5 * fip) / era)) if era and fip else 1))

json.dump(pool, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
from collections import Counter
print('wrote', OUT, len(pool), dict(Counter(p['pos'] for p in pool)))
unmatched = [p['n'] for p in pool if p['type'] == 'H' and p['n'] not in by_name]
print('hitters without a CPBL position (set to DH):', unmatched)
