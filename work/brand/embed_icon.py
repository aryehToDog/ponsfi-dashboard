import base64, io, os, re, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TPL = os.path.join(ROOT, "work", "template.html")
BRAND = os.path.join(ROOT, "work", "brand")

def b64(path):
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")

svg_b64 = b64(os.path.join(BRAND, "logo.svg"))
png32 = b64(os.path.join(BRAND, "logo-32.png"))
png180 = b64(os.path.join(BRAND, "logo-180.png"))

block = (
    '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,%s">\n'
    '<link rel="icon" type="image/png" sizes="32x32" href="data:image/png;base64,%s">\n'
    '<link rel="apple-touch-icon" sizes="180x180" href="data:image/png;base64,%s">\n'
    '<meta name="theme-color" content="#0a0c11">'
) % (svg_b64, png32, png180)

tpl = open(TPL, encoding="utf-8").read()
shutil.copyfile(TPL, TPL + ".bak-icon")
if '<link rel="icon" href="data:,">' in tpl:
    tpl = tpl.replace('<link rel="icon" href="data:,">', block, 1)
elif 'rel="icon"' in tpl:
    tpl = re.sub(r'<link rel="icon"[^>]*>', block, tpl, count=1)
else:
    tpl = tpl.replace('<title>', block + '\n<title>', 1)
open(TPL, "w", encoding="utf-8").write(tpl)
print("icons embedded; template size", os.path.getsize(TPL))
