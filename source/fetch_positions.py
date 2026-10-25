"""Add every fielding position each hitter played, and how well he fielded there, to pool.json and pool_cpbl.json.

    python3 source/fetch_positions.py 2026

Only the "poss" and "pdef" fields of each hitter are written; the batting, pitching and
fielding numbers already in the pools stay exactly as they are. Then run source/build.py.

  poss  {position: games}
        MLB:  MLB Stats API, season fielding by position.
        CPBL: 中華職棒官網 stats/recordall, games by defensive position. That site turns away
              connections from outside Taiwan (GitHub's servers get a 404), so if it can't be reached
              the games come from 野球革命's innings by position instead, 9 innings to a game.
  pdef  {position: fielding runs at that position}, for positions other than his main one,
        in the same units the pools already use for the main position:
        MLB:  Baseball Savant fielding runs prevented (from OAA) by position; catcher framing runs.
        CPBL: 野球革命 UZR by position; catcher framing runs.

The game counts a position as a secondary position from 30 games, in both leagues.
"""
import csv, io, json, os, re, sys, urllib.parse, urllib.request, http.cookiejar

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


POSNUM = {'1B': '3', '2B': '4', '3B': '5', 'SS': '6', 'LF': '7', 'CF': '8', 'RF': '9'}


def savant_csv(url):
    return list(csv.DictReader(io.StringIO(get(url).lstrip('\ufeff'))))


def mlb_fielding_runs():
    """{player id: {position: fielding runs}} from Baseball Savant, one position at a time."""
    out, sizes = {}, {}
    for pos, code in POSNUM.items():
        url = (f'https://baseballsavant.mlb.com/leaderboard/outs_above_average?type=Fielder&startYear={YEAR}&endYear={YEAR}'
               f'&split=no&team=&range=year&min=1&pos={code}&roles=&viz=hide&csv=true')
        rows = savant_csv(url)
        sizes[pos] = len(rows)
        for r in rows:
            v = r.get('fielding_runs_prevented')
            if v not in (None, ''):
                out.setdefault(int(r['player_id']), {})[pos] = float(v)
        print('  savant OAA', pos, len(rows))
    if len(set(sizes.values())) == 1:
        # every position came back the same size: the position filter was ignored, so these aren't per-position numbers
        print('  warning: Savant ignored the position filter; skipping per-position fielding')
        return {}
    url = (f'https://baseballsavant.mlb.com/leaderboard/catcher-framing?type=catcher&seasonStart={YEAR}&seasonEnd={YEAR}'
           '&team=&min=1&sortColumn=rv_tot&sortDirection=asc&csv=true')
    try:
        for r in savant_csv(url):
            if r.get('rv_tot') not in (None, ''):
                out.setdefault(int(r['id']), {})['C'] = float(r['rv_tot'])
    except Exception as e:
        print('  framing skipped:', e)
    return out


def rebas_rows(kind):
    league = json.loads(get('https://www.rebas.tw/api/leagues/CPBL'))['data']
    sid = next(s for s in league['seasons'] if s['year'] == int(YEAR) and s['type'] == 'LEAGUE_MATCHES')['uniqid']
    return json.loads(get(f'https://www.rebas.tw/api/{kind}?season_id={sid}'))['data']


def cpbl_fielding_runs():
    """{rebas player id: {position: runs}} and {rebas player id: {position: games}}:
    UZR by position, framing runs for catchers, and innings at each position turned into games."""
    name = {v: k for k, v in POSNUM.items()}
    runs, games = {}, {}
    for r in rebas_rows('uzr'):
        pos = name.get(str(r['position']))
        if not pos:
            continue
        if r.get('UZR') is not None:
            runs.setdefault(r['id'], {})[pos] = r['UZR']
        if r.get('innings'):
            games.setdefault(r['id'], {})[pos] = round(float(r['innings']) / 9)
    for r in rebas_rows('catcher_framing'):
        if r.get('framingRuns') is not None:
            runs.setdefault(r['id'], {})['C'] = r['framingRuns']
        inn = r.get('innings') or r.get('IP')
        if inn:
            games.setdefault(r['id'], {})['C'] = round(float(inn) / 9)
    print('  rebas: fielding by position for', len(runs), 'players')
    return runs, games


def update(fname, key, table, runs=None, runs_key=None, games_by=None):
    path = os.path.join(SRC, fname)
    pool = json.load(open(path, encoding='utf-8'))
    hit = [p for p in pool if p.get('type') == 'H']
    n = 0
    for p in hit:
        d = games_by(p) if games_by else table.get(p[key])
        if d:
            p['poss'] = dict(sorted(d.items(), key=lambda kv: -kv[1]))
            n += 1
        else:
            p.pop('poss', None)
        r = (runs or {}).get(runs_key(p) if runs_key else p[key], {})
        pd = {k: round(v, 1) for k, v in r.items() if k != p['pos'] and k in (d or {})}
        if pd:
            p['pdef'] = pd
        else:
            p.pop('pdef', None)
    json.dump(pool, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'{fname}: positions for {n} of {len(hit)} hitters, fielding at other positions for {sum(1 for p in hit if p.get("pdef"))}')
    if n < len(hit) * .8:
        print('  warning: many hitters have no position data; check the source page')
    return pool


if __name__ == '__main__':
    url = (f'https://statsapi.mlb.com/api/v1/stats?stats=season&group=fielding&season={YEAR}'
           '&sportId=1&playerPool=ALL&limit=5000')
    update('pool.json', 'id', mlb_positions(json.loads(get(url))['stats'][0]['splits']), mlb_fielding_runs())
    if os.path.exists(os.path.join(SRC, 'pool_cpbl.json')):
        rid = lambda p: p['id'][1:]   # pool ids are 'c' + the rebas id
        try:
            runs, rgames = cpbl_fielding_runs()
        except Exception as e:
            print('CPBL skipped: 野球革命 could not be reached:', e)
            sys.exit(0)
        try:
            update('pool_cpbl.json', 'n', cpbl_positions(), runs, rid)
        except Exception as e:
            print('  cpbl.com.tw could not be reached (' + str(e) + '); using 野球革命 innings, 9 innings to a game')
            update('pool_cpbl.json', 'rid', {}, runs, rid, games_by=lambda p: rgames.get(rid(p)))
