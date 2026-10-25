"""Add every fielding position each hitter played to pool.json and pool_cpbl.json.

    python3 source/fetch_positions.py 2026

Only the "poss" field of each hitter is written; the batting, pitching and fielding
numbers already in the pools stay exactly as they are. Then run source/build.py.

  MLB:  MLB Stats API, season fielding by position: games played at each position.
  CPBL: 中華職棒官網 stats/recordall, games by defensive position
        (the same page fetch_cpbl.py uses to find each hitter's main position).

The game counts a position as a secondary position from 30 games, in both leagues.
"""
import json, os, re, sys, urllib.parse, urllib.request, http.cookiejar

YEAR = sys.argv[1] if len(sys.argv) > 1 else '2026'
SRC = os.path.dirname(os.path.abspath(__file__))
FIELD = ('C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36'
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={'User-Agent': UA})
    with opener.open(req, timeout=120) as r:
        return r.read().decode('utf-8')


def mlb_positions(splits):
    """{player id: {position: games}} from the Stats API's season fielding splits.
    A player has one split per position (and per team, if he was traded)."""
    out = {}
    for s in splits:
        st = s.get('stat', {})
        pos = (s.get('position') or st.get('position') or {}).get('abbreviation')
        if pos not in FIELD:
            continue
        g = st.get('gamesPlayed', st.get('games', 0)) or 0
        d = out.setdefault(s['player']['id'], {})
        d[pos] = d.get(pos, 0) + int(g)
    return out


def cpbl_positions():
    """{player name: {position: games}} from cpbl.com.tw, one defensive position at a time."""
    page = get('https://www.cpbl.com.tw/stats/recordall')
    tok = re.search(r'name="__RequestVerificationToken" type="hidden" value="([^"]+)"', page).group(1)
    code_of = {'2': 'C', '3': '1B', '4': '2B', '5': '3B', '6': 'SS', '7': 'LF', '8': 'CF', '9': 'RF'}
    out = {}
    for code, pos in code_of.items():
        seen = set()
        for idx in range(1, 20):
            form = urllib.parse.urlencode({'__RequestVerificationToken': tok, 'Year': YEAR, 'KindCode': 'A', 'Position': '01',
                                           'Online': '01', 'DefenceType': code, 'Sortby': '', 'PageSize': '60',
                                           'IndexOfPages': str(idx), 'ExecAction': 'Q'}).encode()
            rows = re.findall(r'<tr.*?</tr>', get('https://www.cpbl.com.tw/stats/recordall', form), re.S)[1:]
            new = 0
            for r in rows:
                m = re.search(r'<span class="name"><a[^>]*>([^<]+)</a>', r)
                cells = [re.sub(r'<[^>]+>', '', c).strip() for c in re.findall(r'<td class="num">(.*?)</td>', r, re.S)]
                if not m or len(cells) < 3 or m.group(1).strip() in seen:   # numeric cells: AVG, G, PA, ...
                    continue
                name = m.group(1).strip()
                seen.add(name)
                out.setdefault(name, {})[pos] = int(cells[1])
                new += 1
            if len(rows) < 60 or new == 0:
                break
        print('  cpbl', pos, len(seen))
    return out


def update(fname, key, table):
    path = os.path.join(SRC, fname)
    pool = json.load(open(path, encoding='utf-8'))
    hit = [p for p in pool if p.get('type') == 'H']
    n = 0
    for p in hit:
        d = table.get(p[key])
        if d:
            p['poss'] = dict(sorted(d.items(), key=lambda kv: -kv[1]))
            n += 1
        else:
            p.pop('poss', None)
    json.dump(pool, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'{fname}: positions for {n} of {len(hit)} hitters')
    if n < len(hit) * .8:
        print('  warning: many hitters have no position data; check the source page')
    return pool


if __name__ == '__main__':
    url = (f'https://statsapi.mlb.com/api/v1/stats?stats=season&group=fielding&season={YEAR}'
           '&sportId=1&playerPool=ALL&limit=5000')
    update('pool.json', 'id', mlb_positions(json.loads(get(url))['stats'][0]['splits']))
    if os.path.exists(os.path.join(SRC, 'pool_cpbl.json')):
        update('pool_cpbl.json', 'n', cpbl_positions())
