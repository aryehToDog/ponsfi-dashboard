# -*- coding: utf-8 -*-
"""把 work/brand/ 里的「像素画」Logo 内嵌进 work/template.html（v3.23 起；一条命令搞定，可反复跑）。

内嵌位置（与站点一一对应）：
  ① <head> favicon：32px PNG（标签页）+ 180px 苹果触屏图标（data URI，零外部请求）
  ② 页头 <h1> 的 <i class="brand">：52px PNG（26px 显示 × 2 倍图，视网膜屏也清晰）
  ③ og:image / twitter:image 指向 https://stonk1000x.top/logo-pixel.png（800px 原画）

源文件：logo-pix-32.png、logo-pix-52.png、logo-pix-180.png
改完 logo 的流程：node work/brand/render_pixel.mjs → python3 work/brand/embed_icon.py
（旧「卡通狗」整套在 work/brand/prev-dog/，回退见 work/看板维护说明.md）
"""
import base64, os, re, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TPL = os.path.join(ROOT, "work", "template.html")
OG_URL = "https://stonk1000x.top/logo-pixel.png"


def b64(name):
    with open(os.path.join(HERE, name), "rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")


def main():
    tpl = open(TPL, encoding="utf-8").read()
    shutil.copyfile(TPL, TPL + ".bak-logo-pixel")

    # ① favicon 四行块（SVG+PNG+苹果+主题色）→ 两行图标 + 主题色
    block = (
        '<link rel="icon" type="image/png" sizes="32x32" href="data:image/png;base64,%s">\n'
        '<link rel="apple-touch-icon" sizes="180x180" href="data:image/png;base64,%s">\n'
        '<meta name="theme-color" content="#0a0c11">'
    ) % (b64("logo-pix-32.png"), b64("logo-pix-180.png"))
    full = re.compile(
        r'<link rel="icon"[^>]*>\n'
        r'<link rel="icon"[^>]*>\n'
        r'<link rel="apple-touch-icon"[^>]*>\n'
        r'<meta name="theme-color"[^>]*>'
    )
    assert len(full.findall(tpl)) == 1, "favicon 块匹配数不是 1，先看看模板结构"
    tpl = full.sub(lambda m: block, tpl, count=1)

    # ② 页头品牌标：<i class="brand">…</i> 里的内联 SVG 换成 PNG 图标
    img = '<img alt="" width="26" height="26" src="data:image/png;base64,%s">' % b64("logo-pix-52.png")
    pat = re.compile(r'(<i class="brand" aria-hidden="true">)<svg .*?</svg>', re.S)
    assert len(pat.findall(tpl)) == 1, "页头品牌标匹配数不是 1"
    tpl = pat.sub(lambda m: m.group(1) + img, tpl, count=1)

    # ③ 页头图标样式：沿用原 .brand 的圆角观感 + 像素锐化
    css_old = 'h1 .brand svg{display:block}'
    assert tpl.count(css_old) == 1, ".brand svg 样式匹配数不是 1"
    tpl = tpl.replace(
        css_old,
        css_old + 'h1 .brand img{display:block;border-radius:6px;image-rendering:pixelated}',
        1,
    )

    # ④ 分享图地址：og:image / twitter:image（换新文件名，绕开平台的旧图缓存）
    old = "https://stonk1000x.top/logo-512.png"
    assert tpl.count(old) == 2, "og/twitter 图片地址数量不是 2"
    tpl = tpl.replace(old, OG_URL)

    open(TPL, "w", encoding="utf-8").write(tpl)

    # 写后自检
    tpl2 = open(TPL, encoding="utf-8").read()
    assert '<i class="brand" aria-hidden="true"><svg' not in tpl2, "页头还有旧 SVG 残留"
    assert 'id="dogG"' not in tpl2, "小狗渐变还有残留"
    assert tpl2.count("logo-pixel.png") == 2, "og/twitter 新地址数量不对"
    assert tpl2.count("logo-512") == 0, "旧分享图地址还有残留"
    print("像素 logo 已内嵌（favicon×2 + 页头 + og/twitter）；模板 %.1f KB" % (os.path.getsize(TPL) / 1024))


if __name__ == "__main__":
    main()
