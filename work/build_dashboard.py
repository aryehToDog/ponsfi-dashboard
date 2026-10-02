#!/usr/bin/env python3
"""旧入口，保留只为兼容老习惯：现在一律转交 build_monitor.py。

（老版本只会抓 series/meta/price，会把 dashboard-data.json 里的 market、
 leaderboard 字段整段覆盖掉，并绕过版本标签注入，所以不要再单独用它。）
"""
import os
import runpy

HERE = os.path.dirname(os.path.abspath(__file__))
runpy.run_path(os.path.join(HERE, "build_monitor.py"), run_name="__main__")
