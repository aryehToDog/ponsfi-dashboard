svg = open('logo.svg', encoding='utf-8').read()
for size in (16, 32, 180, 512):
    s = svg.replace('width="64" height="64"', 'width="%d" height="%d"' % (size, size))
    html = ('<!DOCTYPE html><html><head><meta charset="utf-8">'
            '<style>html,body{margin:0;padding:0;background:transparent;overflow:hidden}'
            'svg{display:block}</style></head><body>' + s + '</body></html>')
    open('render-%d.html' % size, 'w', encoding='utf-8').write(html)
print('ok')
