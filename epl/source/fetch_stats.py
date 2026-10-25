"""Download a Premier League season and rebuild pool.json.

    python3 epl/source/fetch_stats.py 2025-26

The numbers are the official Fantasy Premier League (FPL) season totals, which
include Opta's xG / xA / xGC. The FPL site only serves the current season, so
finished seasons come from the vaastav/Fantasy-Premier-League archive on GitHub,
which saves the FPL data at the end of every season. Then run epl/source/build.py.
"""
import csv, io, json, os, sys, urllib.request
from datetime import date

SEASON = sys.argv[1] if len(sys.argv) > 1 else '2025-26'
MIN_MINUTES = 900          # about ten full games; fewer than that and the per-90 numbers are noise
SRC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SRC, 'pool.json')
BASE = f'https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{SEASON}'
# ages are taken on the season's last day
SEASON_END = date(int(SEASON[:4]) + 1, 5, 31)


def rows(name):
    req = urllib.request.Request(f'{BASE}/{name}', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return list(csv.DictReader(io.StringIO(r.read().decode('utf-8'))))


teams = {t['id']: t['name'] for t in rows('teams.csv')}
POS = {'1': 'GK', '2': 'DEF', '3': 'MID', '4': 'FWD'}   # type 5 is the FPL "assistant manager", not a player
i = lambda v: int(float(v or 0))
f = lambda v: round(float(v or 0), 2)
pool = []
for p in rows('players_raw.csv'):
    if p['element_type'] not in POS or i(p['minutes']) < MIN_MINUTES:
        continue
    age = None
    if p.get('birth_date') and p['birth_date'] != 'None':
        b = date.fromisoformat(p['birth_date'])
        age = SEASON_END.year - b.year - ((SEASON_END.month, SEASON_END.day) < (b.month, b.day))
    po = p.get('penalties_order')
    pool.append(dict(
        id=i(p['id']), n=f"{p['first_name']} {p['second_name']}".strip(), w=p['web_name'], t=teams[p['team']],
        pos=POS[p['element_type']], age=age,
        min=i(p['minutes']), st=i(p['starts']), g=i(p['goals_scored']), a=i(p['assists']),
        xg=f(p['expected_goals']), xa=f(p['expected_assists']), xgc=f(p['expected_goals_conceded']),
        gc=i(p['goals_conceded']), cs=i(p['clean_sheets']), sv=i(p['saves']), ps=i(p['penalties_saved']),
        pm=i(p['penalties_missed']), og=i(p['own_goals']), yc=i(p['yellow_cards']), rc=i(p['red_cards']),
        dc=i(p['defensive_contribution']), tk=i(p['tackles']), rec=i(p['recoveries']),
        cbi=i(p['clearances_blocks_interceptions']), bonus=i(p['bonus']), pts=i(p['total_points']),
        cost=i(p['now_cost']) / 10, pk=1 if po not in (None, '', 'None') and i(po) == 1 else 0))

json.dump(pool, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
from collections import Counter
print('wrote', OUT, len(pool), dict(Counter(p['pos'] for p in pool)))
