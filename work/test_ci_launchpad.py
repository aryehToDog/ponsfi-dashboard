"""Daily-build regression: preserve the independent launchpad cache for refresh."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import ci_build
import launchpad


class DailyLaunchpadTests(unittest.TestCase):
    def test_daily_rebuild_preserves_cache_and_refreshes_before_render(self):
        cached = {"generated": 100, "metrics": {"revenue": {"stonk": 10}}}
        refreshed = {"generated": 200, "metrics": {"revenue": {"stonk": 20}}}
        rendered = []
        commands = []
        with tempfile.TemporaryDirectory() as root:
            work = Path(root) / "work"
            work.mkdir()
            dashboard = work / "dashboard-data.json"
            dashboard.write_text(json.dumps({"launchpads": cached}), encoding="utf-8")
            output = Path(root) / "outputs" / "monitor.html"
            deployed = Path(root) / "deploy" / "index.html"

            def command(args):
                script = os.path.basename(args[-1])
                commands.append(script)
                if script == "build_monitor.py":
                    # The real daily collector replaces this file without launchpads.
                    dashboard.write_text(json.dumps({"generated": "daily"}), encoding="utf-8")
                elif script == "stonk_page.py":
                    data = json.loads(dashboard.read_text(encoding="utf-8"))
                    data["stonkPage"] = {"updated": 200}
                    dashboard.write_text(json.dumps(data), encoding="utf-8")
                elif script == "render_only.py":
                    data = json.loads(dashboard.read_text(encoding="utf-8"))
                    rendered.append(data)
                    output.write_text(json.dumps(data), encoding="utf-8")

            with patch.multiple(ci_build, HERE=str(work), ROOT=root,
                                OUT_HTML=str(output), DEPLOY_HTML=str(deployed)), \
                    patch.object(sys, "argv", ["ci_build.py", "--mode", "daily"]), \
                    patch.object(ci_build, "run", side_effect=command), \
                    patch.object(ci_build, "merge_hourly"), \
                    patch.object(ci_build, "refresh_leaderboard", return_value=True), \
                    patch.object(launchpad, "fetch_launchpads", return_value=refreshed) as fetch:
                self.assertEqual(ci_build.main(), 0)

            fetch.assert_called_once_with(cached)
            self.assertEqual(commands, ["build_monitor.py", "stonk_page.py", "render_only.py"])
            self.assertEqual(len(rendered), 1)
            self.assertEqual(rendered[0]["launchpads"], refreshed)
            self.assertEqual(rendered[0]["stonkPage"], {"updated": 200})
            self.assertEqual(json.loads(deployed.read_text(encoding="utf-8"))["launchpads"], refreshed)


if __name__ == "__main__":
    unittest.main()
