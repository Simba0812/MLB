"""Rebuild the football site from template.html + pool.json.

    python3 epl/source/build.py

Writes ../index.html: single player and same device, one file, no Firebase, opens by double-click.
"""
import os

SRC = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(SRC)

page = open(os.path.join(SRC, 'template.html'), encoding='utf-8').read()
page = page.replace('/*POOL*/[]', open(os.path.join(SRC, 'pool.json'), encoding='utf-8').read())
head, body = page.split('</style>', 1)
html = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<style>[hidden]{display:none!important}body{margin:0}img{max-width:100%}</style>\n'
        + head + '</style>\n</head>\n<body>' + body + '\n</body>\n</html>\n')
open(os.path.join(SITE, 'index.html'), 'w', encoding='utf-8').write(html)
print('built epl/index.html,', len(html) // 1024, 'KB')
