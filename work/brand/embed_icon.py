# -*- coding: utf-8 -*-
"""把 work/brand/ 里的 logo 内嵌进 work/template.html（幂等，可反复跑）。

内嵌位置（与站点一一对应）：
  ① <head> 里的 favicon 三件套：SVG（主） + 32px PNG（兜底） + 180px 苹果触屏图标
  ② 页头 <h1> 里的 <i class="brand"> 内联 SVG（跟随主题、零外部请求）

源文件：logo.svg（站点图标母版）、logo-32.png、logo-180.png、header-dog.svg（页头用）
改完 logo 的流程：node work/brand/render_dog.mjs → python3 work/brand/embed_icon.py
"""
import base64, os, re, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TPL = os.path.join(ROOT, "work", "template.html")


def b64(name):
    with open(os.path.join(HERE, name), "rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")


def build_icon_block():
    return (
        '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,%s">\n'
        '<link rel="icon" type="image/png" sizes="32x32" href="data:image/png;base64,%s">\n'
        '<link rel="apple-touch-icon" sizes="180x180" href="data:image/png;base64,%s">\n'
        '<meta name="theme-color" content="#0a0c11">'
    ) % (b64("logo.svg"), b64("logo-32.png"), b64("logo-180.png"))


def main():
    tpl = open(TPL, encoding="utf-8").read()
    shutil.copyfile(TPL, TPL + ".bak-logo-dog")

    # ① favicon 三件套 + theme-color：整块替换（先匹配完整四行块，匹配不到再退回单行）
    block = build_icon_block()
    full = re.compile(
        r'<link rel="icon"[^>]*>\n'
        r'<link rel="icon"[^>]*>\n'
        r'<link rel="apple-touch-icon"[^>]*>\n'
        r'<meta name="theme-color"[^>]*>'
    )
    n_full = len(full.findall(tpl))
    if n_full == 1:
        tpl = full.sub(lambda m: block, tpl, count=1)
    else:
        raise SystemExit("favicon 块匹配数 %d（应为 1）——先看看模板结构是不是变了" % n_full)

    # ② 页头品牌标：<i class="brand">…</i> 里的内联 SVG 换成新 logo
    header = open(os.path.join(HERE, "header-dog.svg"), encoding="utf-8").read().strip()
    pat = re.compile(r'(<i class="brand" aria-hidden="true">)<svg .*?</svg>')
    hits = pat.findall(tpl)
    if len(hits) != 1:
        raise SystemExit("页头品牌标匹配数 %d（应为 1）" % len(hits))
    tpl = pat.sub(lambda m: m.group(1) + header, tpl, count=1)

    open(TPL, "w", encoding="utf-8").write(tpl)
    print("logo 已内嵌；模板大小 %.1f KB" % (os.path.getsize(TPL) / 1024))


if __name__ == "__main__":
    main()
