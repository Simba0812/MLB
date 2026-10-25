"""Rebuild the site from template.html + the player pools.

    python3 source/build.py

Writes:
  ../index.html        多人版: single-player, same device, and online play (Firebase)
  ../大聯盟盲標對決單機.html  單機版: single-player and same device only; one file, no Firebase, opens by double-click
  claude-artifact.html the claude.ai version (online play through claude.ai)
"""
import os

SRC = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(SRC)

t = open(os.path.join(SRC, 'template.html'), encoding='utf-8').read()
page = t.replace('/*POOL*/[]', open(os.path.join(SRC, 'pool.json'), encoding='utf-8').read())
cpbl = os.path.join(SRC, 'pool_cpbl.json')
page = page.replace('/*POOL_CPBL*/[]', open(cpbl, encoding='utf-8').read() if os.path.exists(cpbl) else '[]')
open(os.path.join(SRC, 'claude-artifact.html'), 'w', encoding='utf-8').write(page)


def standalone(flags):
    # real document skeleton, the reset the artifact viewer normally adds, and the build's own flags
    head, body = page.split('</style>', 1)
    body = body.replace('<script>\nconst POOL', flags + '\n<script>\nconst POOL', 1)
    assert flags in body
    return ('<!doctype html>\n<html lang="zh-Hant">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            '<style>[hidden]{display:none!important}body{margin:0}img{max-width:100%}</style>\n'
            + head + '</style>\n</head>\n<body>' + body + '\n</body>\n</html>\n')


open(os.path.join(SITE, 'index.html'), 'w', encoding='utf-8').write(
    standalone('<script>window.STANDALONE=true</script>\n<script src="firebase-config.js"></script>'))
open(os.path.join(SITE, '大聯盟盲標對決單機.html'), 'w', encoding='utf-8').write(
    standalone('<script>window.STANDALONE=true;window.OFFLINE=true</script>'))
print('built index.html (多人版), 大聯盟盲標對決單機.html (單機版) and source/claude-artifact.html,', len(page) // 1024, 'KB')
