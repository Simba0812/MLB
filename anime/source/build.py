"""Rebuild the anime brawl page from template.html + roster.json.

    python3 anime/source/build.py

Writes ../index.html: single player and same device, one file, opens by double-click.
The characters, their stats and special moves are in roster.json; edit them there.
"""
import os

SRC = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(SRC)

page = open(os.path.join(SRC, 'template.html'), encoding='utf-8').read()
page = page.replace('/*ROSTER*/[]', open(os.path.join(SRC, 'roster.json'), encoding='utf-8').read())
head, body = page.split('</style>', 1)
html = ('<!doctype html>\n<html lang="zh-Hant">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<style>[hidden]{display:none!important}body{margin:0}img{max-width:100%}</style>\n'
        + head + '</style>\n</head>\n<body>' + body + '\n</body>\n</html>\n')
open(os.path.join(SITE, 'index.html'), 'w', encoding='utf-8').write(html)
print('built anime/index.html,', len(html) // 1024, 'KB')
