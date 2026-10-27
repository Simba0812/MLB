"""Download an NBA season and rebuild pool.json.

    python3 nba/source/fetch_stats.py 2025-26

Season totals for every player: NBA.com's stats API first (through the nba_api package);
if NBA.com turns the request away (it often blocks cloud servers), Basketball Reference.
Both give the same counting stats; the game works from per-36-minute rates built from them.
Then run nba/source/build.py.
"""
import io, json, os, re, sys, time, urllib.request

SEASON = sys.argv[1] if len(sys.argv) > 1 else '2025-26'
MIN_GP, MIN_MIN = 20, 500        # enough games and minutes that the rates mean something
SRC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SRC, 'pool.json')
# 台灣常見譯名; everyone else keeps his English name in the Chinese interface too
ZH = {'LeBron James': '詹姆斯', 'Stephen Curry': '柯瑞', 'Kevin Durant': '杜蘭特', 'Giannis Antetokounmpo': '字母哥',
      'Nikola Jokić': '約基奇', 'Luka Dončić': '唐西奇', 'Shai Gilgeous-Alexander': 'SGA', 'Jayson Tatum': '塔圖姆',
      'Joel Embiid': '恩比德', 'Anthony Davis': '戴維斯', 'Victor Wembanyama': '溫班亞馬', 'Anthony Edwards': '愛德華茲',
      'Devin Booker': '布克', 'Kawhi Leonard': '雷納德', 'Jimmy Butler': '巴特勒', 'Jimmy Butler III': '巴特勒',
      'Damian Lillard': '里拉德', 'Kyrie Irving': '厄文', 'James Harden': '哈登', 'Donovan Mitchell': '米契爾',
      'Jalen Brunson': '布朗森', 'Ja Morant': '莫蘭特', 'Trae Young': '楊恩', 'Zion Williamson': '錫安',
      'Paul George': '喬治', 'Karl-Anthony Towns': '唐斯', 'Jaylen Brown': '布朗', 'Tyrese Haliburton': '哈利伯頓',
      'Domantas Sabonis': '沙波尼斯', 'Bam Adebayo': '阿德巴約', 'De\'Aaron Fox': '福克斯', 'Chet Holmgren': '霍姆格倫',
      'Paolo Banchero': '班切羅', 'Cade Cunningham': '康寧漢', 'Jamal Murray': '莫瑞', 'Rudy Gobert': '戈貝爾',
      'Klay Thompson': '湯普森', 'Draymond Green': '格林', 'Zach LaVine': '拉文', 'DeMar DeRozan': '德羅展',
      'Jaren Jackson Jr.': '小傑克森', 'Lauri Markkanen': '馬卡寧', 'Alperen Şengün': '申京', 'Tyrese Maxey': '馬克西',
      'Evan Mobley': '莫布里', 'Pascal Siakam': '席亞康', 'Franz Wagner': '法蘭茲·華格納', 'Scottie Barnes': '巴恩斯',
      'Cooper Flagg': '弗拉格', 'Rui Hachimura': '八村壘', 'Yuki Kawamura': '河村勇輝'}
FIELDS = ['gp', 'min', 'fgm', 'fga', 'fg3m', 'fg3a', 'ftm', 'fta', 'oreb', 'dreb', 'ast', 'stl', 'blk', 'tov', 'pf', 'pts']


def from_nba_api():
    from nba_api.stats.endpoints import leaguedashplayerstats, playerindex
    kw = dict(season=SEASON, timeout=60)
    tot = leaguedashplayerstats.LeagueDashPlayerStats(per_mode_detailed='Totals', **kw).get_data_frames()[0]
    time.sleep(2)
    adv = leaguedashplayerstats.LeagueDashPlayerStats(measure_type_detailed_defense='Advanced', **kw).get_data_frames()[0]
    time.sleep(2)
    idx = playerindex.PlayerIndex(**kw).get_data_frames()[0]
    pos = {r.PERSON_ID: (r.POSITION or '') for r in idx.itertuples()}
    advd = {r.PLAYER_ID: r for r in adv.itertuples()}
    out = []
    for r in tot.itertuples():
        a = advd.get(r.PLAYER_ID)
        out.append(dict(id=int(r.PLAYER_ID), n=r.PLAYER_NAME, t=r.TEAM_ABBREVIATION, age=int(r.AGE or 0), pos=pos.get(r.PLAYER_ID, ''),
                        **{f: float(getattr(r, f.upper())) for f in FIELDS},
                        usg=float(a.USG_PCT) if a is not None else None, drtg=float(a.DEF_RATING) if a is not None else None,
                        ortg=float(a.OFF_RATING) if a is not None else None))
    return out, 'NBA.com'


def from_bbref():
    import pandas as pd
    year = int(SEASON[:4]) + 1
    def table(kind):
        req = urllib.request.Request(f'https://www.basketball-reference.com/leagues/NBA_{year}_{kind}.html', headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=60).read().decode('utf-8')
        df = pd.read_html(io.StringIO(html))[0]
        return df[df['Player'] != 'Player']
    tot = table('totals'); time.sleep(4); adv = table('advanced')
    team_col = 'Team' if 'Team' in tot.columns else 'Tm'
    # a traded player has one row per team plus a combined row (2TM, 3TM or TOT); keep the combined one
    tot = tot.drop_duplicates('Player', keep='first'); adv = adv.drop_duplicates('Player', keep='first')
    advd = {r['Player']: r for _, r in adv.iterrows()}
    num = lambda v: float(v) if str(v) not in ('', 'nan') else 0.0
    bpos = {'PG': 'G', 'SG': 'G', 'SF': 'F', 'PF': 'F', 'C': 'C'}
    out = []
    for i, r in tot.iterrows():
        a = advd.get(r['Player'])
        p = '-'.join(dict.fromkeys(bpos.get(x, '') for x in str(r['Pos']).split('-') if x in bpos))
        out.append(dict(id=f"b{i}", n=r['Player'].replace('*', ''), t=r[team_col], age=int(num(r['Age'])), pos=p,
                        gp=num(r['G']), min=num(r['MP']), fgm=num(r['FG']), fga=num(r['FGA']), fg3m=num(r['3P']), fg3a=num(r['3PA']),
                        ftm=num(r['FT']), fta=num(r['FTA']), oreb=num(r['ORB']), dreb=num(r['DRB']), ast=num(r['AST']),
                        stl=num(r['STL']), blk=num(r['BLK']), tov=num(r['TOV']), pf=num(r['PF']), pts=num(r['PTS']),
                        usg=num(a['USG%']) / 100 if a is not None else None, drtg=None, ortg=None,
                        bpm=num(a['BPM']) if a is not None and 'BPM' in a else None))
    return out, 'Basketball Reference'


rows, source = None, None
for fn in (from_nba_api, from_bbref):
    try:
        rows, source = fn()
        print('source:', source, len(rows), 'rows')
        break
    except Exception as e:
        print(fn.__name__, 'failed:', repr(e)[:300])
if not rows:
    sys.exit('no source could be reached')

pool = []
for r in rows:
    if r['gp'] < MIN_GP or r['min'] < MIN_MIN:
        continue
    # positions as a set of G / F / C, from "Guard-Forward", "F-C", "G" and the like
    p = r['pos'] or ''
    ps = [k for k in 'GFC' if k in re.sub(r'Guard', 'G', re.sub(r'Forward', 'F', re.sub(r'Center', 'C', p)))]
    r['pos'] = '-'.join(ps) or 'F'
    r['zh'] = ZH.get(r['n'])
    for k in FIELDS:
        r[k] = round(r[k], 1)
    pool.append(r)
json.dump({'season': SEASON, 'source': source, 'players': pool}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
from collections import Counter
print('wrote', OUT, len(pool), Counter(p['pos'] for p in pool))
