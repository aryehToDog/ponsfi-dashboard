import os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
p = os.path.join(ROOT, "work", "render_only.py")
src = open(p, encoding="utf-8").read()
shutil.copyfile(p, p + ".bak-icon")

old_head = 'BANNER = """<!-- ==========================================================================\n     ponsfi.xyz 看板 · 版本 v2.5「只读声明」 · 2026-10-03'
new_head = ('BANNER = """<!-- ==========================================================================\n'
            '     ponsfi.xyz 看板 · 版本 v2.8「品牌图标」 · 2026-10-04\n'
            '     【这一版改了什么】换掉了浏览器标签页上的「地球」占位图标 —— 之前 <link rel="icon" href="data:,">\n'
            '       是空图标，所以浏览器只能显示地球。现在换成正式 logo：深色圆角方块 + 紫(#8b7cff)→绿(#2ee6a8)\n'
            '       渐变的「P」字标（紫=Pons，绿=StonkFun，正好对上站内两个协议的主色）。\n'
            '       · 全部内嵌为 data URI（SVG 主图标 + 32px PNG 兜底 + 180px 苹果触屏图标），不新增任何文件\n'
            '       · 同时补了 <meta name="theme-color" content="#0a0c11">，手机浏览器地址栏跟着变深色\n'
            '       · 源文件：work/brand/logo.svg、logo-16/32/180/512.png（改完跑 work/brand/embed_icon.py 重新内嵌）\n'
            '     ---------------------------------------------------------------------------\n'
            '     ponsfi.xyz 看板 · 版本 v2.5「只读声明」 · 2026-10-03')
assert old_head in src, "banner head not found"
src = src.replace(old_head, new_head, 1)

src = src.replace('<meta name="dashboard-version" content="v2.5-2026-10-03">',
                  '<meta name="dashboard-version" content="v2.8-2026-10-04">', 1)
src = src.replace('VER = "v2.5 · 2026-10-03"', 'VER = "v2.8 · 2026-10-04"', 1)
assert 'v2.8-2026-10-04' in src and 'v2.8 · 2026-10-04' in src
open(p, "w", encoding="utf-8").write(src)
print("render_only.py bumped to v2.8")
