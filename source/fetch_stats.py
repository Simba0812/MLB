"""Download a season's MLB.com + Baseball Savant stats and rebuild pool.json.

    python3 source/fetch_stats.py 2027

Then run source/build.py to put the new players into the site.
"""
import json, csv, sys, os, tempfile, urllib.request

YEAR = sys.argv[1] if len(sys.argv) > 1 else '2026'
SRC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SRC, 'pool.json')
D = tempfile.mkdtemp(prefix='mlb-stats-')
URLS = {
  'hit.json': f'https://statsapi.mlb.com/api/v1/stats?stats=season&group=hitting&season={YEAR}&sportId=1&playerPool=ALL&limit=2000',
  'pit.json': f'https://statsapi.mlb.com/api/v1/stats?stats=season&group=pitching&season={YEAR}&sportId=1&playerPool=ALL&limit=2000',
  'xbat.csv': f'https://baseballsavant.mlb.com/leaderboard/expected_statistics?type=batter&year={YEAR}&position=&team=&filterType=pa&min=100&csv=true',
  'xpit.csv': f'https://baseballsavant.mlb.com/leaderboard/expected_statistics?type=pitcher&year={YEAR}&position=&team=&filterType=bip&min=50&csv=true',
  'sprint.csv': f'https://baseballsavant.mlb.com/leaderboard/sprint_speed?year={YEAR}&position=&team=&min=10&csv=true',
  'barrel.csv': f'https://baseballsavant.mlb.com/leaderboard/statcast?type=batter&year={YEAR}&position=&team=&min=100&csv=true',
  'oaa.csv': f'https://baseballsavant.mlb.com/leaderboard/outs_above_average?type=Fielder&startYear={YEAR}&endYear={YEAR}&split=no&team=&range=year&min=10&pos=&roles=&viz=hide&csv=true',
  'framing.csv': f'https://baseballsavant.mlb.com/leaderboard/catcher-framing?type=catcher&seasonStart={YEAR}&seasonEnd={YEAR}&team=&min=q&sortColumn=rv_tot&sortDirection=asc&csv=true',
  'velo.csv': f'https://baseballsavant.mlb.com/leaderboard/pitch-arsenals?year={YEAR}&min=50&type=avg_speed&hand=&csv=true',
}
for name, url in URLS.items():
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as r, open(os.path.join(D, name), 'wb') as f:
        f.write(r.read())
    print('downloaded', name)
def L(f): return json.load(open(os.path.join(D,f)))['stats'][0]['splits']
def C(f):
    with open(os.path.join(D,f), encoding='utf-8-sig') as fh: return {int(r['player_id']): r for r in csv.DictReader(fh)}
def best(splits, key):
    m = {}
    for s in splits:
        pid = s['player']['id']
        if pid not in m or s['stat'].get(key,0) > m[pid]['stat'].get(key,0): m[pid] = s
    return m
H = best(L('hit.json'), 'plateAppearances'); P = best(L('pit.json'), 'battersFaced')
xb, xp, sp, br = C('xbat.csv'), C('xpit.csv'), C('sprint.csv'), C('barrel.csv')
oa = C('oaa.csv')
with open(os.path.join(D,'framing.csv'), encoding='utf-8-sig') as fh: fr = {int(r['id']): r for r in csv.DictReader(fh)}
with open(os.path.join(D,'velo.csv'), encoding='utf-8-sig') as fh: ve = {int(r['pitcher']): r for r in csv.DictReader(fh)}
def velo(pid):
    r = ve.get(pid, {})
    v = [f(r.get(k)) for k in ('ff_avg_speed','si_avg_speed')]
    v = [x for x in v if x] or [f(r.get('fc_avg_speed'))]
    return max(v) if v and v[0] else None  # fastest of four-seam / sinker, else cutter
ZH = {'Shohei Ohtani':'大谷翔平','Yoshinobu Yamamoto':'山本由伸','Seiya Suzuki':'鈴木誠也','Shota Imanaga':'今永昇太',
 'Masataka Yoshida':'吉田正尚','Yusei Kikuchi':'菊池雄星','Yu Darvish':'達比修有','Roki Sasaki':'佐佐木朗希','Kodai Senga':'千賀滉大',
 'Jung Hoo Lee':'李政厚','Hyeseong Kim':'金慧成','Munetaka Murakami':'村上宗隆','Kazuma Okamoto':'岡本和真','Tatsuya Imai':'今井達也',
 'Ha-Seong Kim':'金河成','Tomoyuki Sugano':'菅野智之','Lars Nootbaar':'努特巴','Kenta Maeda':'前田健太','Tyler Glasnow':'葛拉斯諾',
 'Aaron Judge':'賈吉','Juan Soto':'索托','Mookie Betts':'貝茲','Freddie Freeman':'佛里曼','Bryce Harper':'哈波','Mike Trout':'楚奧特',
 'Paul Skenes':'史基恩斯','Tarik Skubal':'史庫鮑','Cal Raleigh':'羅禮','Bobby Witt Jr.':'小威特','Vladimir Guerrero Jr.':'小葛雷諾',
 'Fernando Tatis Jr.':'小塔提斯','Ronald Acuña Jr.':'阿庫尼亞','Francisco Lindor':'林多','Pete Alonso':'阿隆索','Kyle Schwarber':'舒瓦伯'}
f = lambda v, d=None: (float(v) if v not in (None,'','null') else d)
pool = []
for pid, s in H.items():
    st = s['stat']; pa = st['plateAppearances']; pos = s['position']['abbreviation']
    if pa < 250 or pos not in ('C','1B','2B','3B','SS','LF','CF','RF','DH'): continue
    hits=st['hits']; d2=st['doubles']; d3=st['triples']; hr=st['homeRuns']
    x = xb.get(pid, {}); woba = f(x.get('woba')); xw = f(x.get('est_woba'))
    pool.append(dict(id=pid, n=s['player']['fullName'], zh=ZH.get(s['player']['fullName']), t=s['team']['name'], pos=pos, type='H', age=st['age'],
      pa=pa, avg=st['avg'], obp=st['obp'], slg=st['slg'], ops=st['ops'], hr=hr, rbi=st['rbi'], sb=st['stolenBases'],
      r=dict(k=st['strikeOuts']/pa, bb=(st['baseOnBalls']+st['hitByPitch'])/pa, s1=(hits-d2-d3-hr)/pa, s2=d2/pa, s3=d3/pa, hr=hr/pa,
             gidp=st['groundIntoDoublePlay']/pa, sbr=st['stolenBases']/max(1,pa)),
      woba=woba, xwoba=xw, xba=f(x.get('est_ba')), xslg=f(x.get('est_slg')),
      spd=f(sp.get(pid,{}).get('sprint_speed'), 27.0), brl=f(br.get(pid,{}).get('brl_percent')), ev=f(br.get(pid,{}).get('avg_hit_speed')),
      oaa=f(oa.get(pid,{}).get('outs_above_average')), frp=f(oa.get(pid,{}).get('fielding_runs_prevented')), frm=f(fr.get(pid,{}).get('rv_tot'))))
for pid, s in P.items():
    st = s['stat']; bf = st['battersFaced']; gs = st['gamesStarted']; g = st['gamesPitched']; ip = float(st['inningsPitched'])
    sv = st['saves']
    if gs >= 10 and ip >= 60: role = 'SP'
    elif sv >= 12: role = 'CL'
    elif gs <= 3 and ip >= 40: role = 'RP'
    else: continue
    hits=st['hits']; d2=st['doubles']; d3=st['triples']; hr=st['homeRuns']
    x = xp.get(pid, {})
    p = dict(id=pid, n=s['player']['fullName'], zh=ZH.get(s['player']['fullName']), t=s['team']['name'], pos=role, type='P', age=st['age'],
      g=g, gs=gs, ip=st['inningsPitched'], era=st['era'], whip=st['whip'], w=st['wins'], l=st['losses'], sv=sv, hld=st['holds'], so=st['strikeOuts'],
      r=dict(k=st['strikeOuts']/bf, bb=(st['baseOnBalls']+st['hitBatsmen'])/bf, s1=(hits-d2-d3-hr)/bf, s2=d2/bf, s3=d3/bf, hr=hr/bf),
      bfg=bf/max(1,g), np=st['numberOfPitches']/max(1,g), ppa=st['numberOfPitches']/max(1,bf), velo=velo(pid), xera=f(x.get('xera')), xwoba=f(x.get('est_woba')), woba=f(x.get('woba')))
    pool.append(p)
# two-way: attach pitching line to hitter entries
byid = {}
for p in pool: byid.setdefault(p['id'], []).append(p)
for pid, ps in byid.items():
    if len(ps) == 2:
        h = [p for p in ps if p['type']=='H'][0]; pp = [p for p in ps if p['type']=='P'][0]
        h['twp'] = {k: pp[k] for k in ('pos','g','gs','ip','era','whip','w','l','sv','hld','so','r','bfg','np','ppa','velo','xera','xwoba','woba')}
        pool.remove(pp)
json.dump(pool, open(OUT,'w'), ensure_ascii=False, separators=(',',':'))
import collections; print(len(pool), collections.Counter(p['pos'] for p in pool), [p['n'] for p in pool if p.get('twp')])
