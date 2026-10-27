"""Rebuild the NBA page from template.html + pool.json.

    python3 nba/source/build.py

Writes ../index.html: single player, same device, and online play (Firebase, using the
firebase-config.js at the top of the site, which the baseball page uses too).
"""
import os

SRC = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(SRC)

page = open(os.path.join(SRC, 'template.html'), encoding='utf-8').read()
page = page.replace('/*POOL*/{"season":"","source":"","players":[]}', open(os.path.join(SRC, 'pool.json'), encoding='utf-8').read(), 1)
head, body = page.split('</style>', 1)
flags = '<script>window.STANDALONE=true</script>\n<script src="../firebase-config.js"></script>'
body = body.replace('<script>\nconst DATA', flags + '\n<script>\nconst DATA', 1)
assert flags in body
html = ('<!doctype html>\n<html lang="zh-Hant">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<style>[hidden]{display:none!important}body{margin:0}img{max-width:100%}</style>\n'
        + head + '</style>\n</head>\n<body>' + body + '\n</body>\n</html>\n')
open(os.path.join(SITE, 'index.html'), 'w', encoding='utf-8').write(html)
print('built nba/index.html,', len(html) // 1024, 'KB')
