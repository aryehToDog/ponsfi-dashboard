#!/usr/bin/env python3
"""ponsfi.xyz 误报申诉复查（纯脚本，不经过模型）。

每天 09:55 由 launchd（com.ponspulse.appeal-check）运行一次，检查：
1. MetaMask 官方黑名单里是否还有 ponsfi.xyz（只剩 ponsfi.top 即成功）
2. PR MetaMask/eth-phishing-detect#299334 状态（merged / closed / open）
3. ScamSniffer issue scam-database#827 的 state 与评论数（有新评论即提醒）
4. GoPlus 判定（2026-10-04 起被误标 phishing_site=1，已提交申诉，期望恢复）
5. GoPlus 超 3 个工作日无变化 -> 提醒一次催办（service@gopluslabs.io）

规则：一切照旧则静默；「成功（含 GoPlus 清除） / 需要处理 / GoPlus 催办 / 连续 10 天无进展」才弹系统通知。
用法: python3 appeal_check.py [--test]
"""
import datetime
import json
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "appeal-check.log")
STATE = os.path.join(HERE, "appeal-check-state.json")

MM_URL = "https://raw.githubusercontent.com/MetaMask/eth-phishing-detect/main/src/config.json"
PR_URL = "https://api.github.com/repos/MetaMask/eth-phishing-detect/pulls/299334"
SS_ISSUE_URL = "https://api.github.com/repos/scamsniffer/scam-database/issues/827"
GP_URL = "https://api.gopluslabs.io/api/v1/phishing_site?url=ponsfi.xyz"
GP_ESCALATE_DATE = datetime.date(2026, 10, 9)  # 申诉提交（10-04）后超 3 个工作日仍无变化则提醒催办

UA = {"User-Agent": "ponspulse-appeal-check/1.0"}


def log(line):
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(f"[{stamp}] {line}\n")
    except Exception:
        pass


def notify(title, message):
    script = 'display notification {} with title {}'.format(
        json.dumps(message, ensure_ascii=False), json.dumps(title, ensure_ascii=False)
    )
    try:
        proc = subprocess.run(["osascript", "-e", script], timeout=20,
                              capture_output=True, text=True)
        log("已发送系统通知" if proc.returncode == 0 else "通知失败: " + (proc.stderr or "").strip()[:200])
    except Exception as exc:
        log(f"通知异常: {exc}")


def get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def fetch():
    state = {"checked_at": datetime.datetime.now().isoformat(timespec="seconds")}
    try:
        text = get(MM_URL)
        entries = sorted({tok.strip('[]," ') for tok in text.replace('"', " ").replace(",", " ").split() if "ponsfi" in tok})
        state["metamask_entries"] = entries
        state["metamask_has_xyz"] = any("ponsfi.xyz" in e for e in entries)
        state["metamask_ok"] = True
    except Exception as exc:
        state["metamask_ok"] = False
        state["metamask_error"] = str(exc)[:160]
    try:
        pr = json.loads(get(PR_URL))
        state["pr_state"] = pr.get("state")
        state["pr_merged"] = bool(pr.get("merged"))
        state["pr_ok"] = True
    except Exception as exc:
        state["pr_ok"] = False
        state["pr_error"] = str(exc)[:160]
    try:
        issue = json.loads(get(SS_ISSUE_URL))
        state["ss_state"] = issue.get("state")
        state["ss_comments"] = int(issue.get("comments") or 0)
        state["ss_ok"] = True
    except Exception as exc:
        state["ss_ok"] = False
        state["ss_error"] = str(exc)[:160]
    try:
        gp = json.loads(get(GP_URL))
        res = gp.get("result")
        if isinstance(res, dict):
            flag = str(res.get("phishing_site", "0")) == "1"
        else:
            flag = str(res) == "1"
        state["goplus_flag"] = flag
        state["goplus_ok"] = True
    except Exception as exc:
        state["goplus_ok"] = False
        state["goplus_error"] = str(exc)[:160]
    return state


def main():
    if "--test" in sys.argv:
        notify("PonsPulse 测试", "这是一条申诉复查脚本测试通知，收到即表示通知功能正常。")
        return 0
    old = {}
    if os.path.exists(STATE):
        try:
            with open(STATE, encoding="utf-8") as fh:
                old = json.load(fh)
        except Exception:
            old = {}
    new = fetch()
    alerts = []
    success = False

    if new.get("metamask_ok") and old.get("metamask_ok") and old.get("metamask_has_xyz") and not new.get("metamask_has_xyz"):
        alerts.append("MetaMask 黑名单里 ponsfi.xyz 已消失，钱包警告预计 1~3 天内消失，可以放心分享（只认 ponsfi.xyz）")
        success = True
    if new.get("pr_ok") and old.get("pr_ok") and new.get("pr_merged") and not old.get("pr_merged"):
        alerts.append("PR #299334 已被合并")
        success = True
    if new.get("pr_ok") and old.get("pr_ok") and new.get("pr_state") == "closed" and not new.get("pr_merged") and old.get("pr_state") != "closed":
        alerts.append("PR #299334 被关闭且未合并，建议去 PR 里看维护者留言并回复")
    if new.get("ss_ok") and old.get("ss_ok") and new.get("ss_comments", 0) > old.get("ss_comments", 0):
        alerts.append(f"ScamSniffer issue #827 有新回复（评论 {old.get('ss_comments')}→{new.get('ss_comments')}），建议查看")
    if new.get("goplus_ok") and new.get("goplus_flag") and not old.get("goplus_flag"):
        alerts.append("GoPlus 开始把 ponsfi.xyz 标记为钓鱼（意外情况，需尽快处理）")
    if new.get("goplus_ok") and old.get("goplus_ok") and old.get("goplus_flag") and not new.get("goplus_flag"):
        alerts.append("GoPlus 误报已清除！币安/OKX 钱包的拦截预计 1~3 天内陆续解除，可以放心分享（只认 ponsfi.xyz）")
        success = True
    notified_gp_escalate = bool(old.get("notified_gp_escalate"))
    if (new.get("goplus_ok") and new.get("goplus_flag")
            and datetime.date.today() >= GP_ESCALATE_DATE and not notified_gp_escalate):
        alerts.append("GoPlus 误报仍未清除（已超过 3 个工作日）：建议发催办邮件到 service@gopluslabs.io（或 X 私信 @GoPlusSecurity），说明这是已提交的误报申诉，附上 goPlus 反馈表单提交成功记录")
        notified_gp_escalate = True
    new["notified_gp_escalate"] = notified_gp_escalate

    watch_keys = ("metamask_has_xyz", "pr_state", "pr_merged", "ss_state", "ss_comments", "goplus_flag")
    changed = [k for k in watch_keys if k in new and old.get(k) != new.get(k)]
    all_ok = all(new.get(k) for k in ("metamask_ok", "pr_ok", "ss_ok", "goplus_ok"))
    if old and all_ok and not changed:
        days = int(old.get("days_no_progress") or 0) + 1
    else:
        days = 0
    notified_10d = bool(old.get("notified_10d"))
    if changed:
        notified_10d = False
    if days >= 10 and not notified_10d:
        alerts.append(f"申诉已连续 {days} 天毫无进展，建议去 PR / issue 里礼貌催一下")
        notified_10d = True
    new["days_no_progress"] = days
    new["notified_10d"] = notified_10d

    if alerts:
        notify("ponsfi.xyz 申诉成功 🎉" if success else "ponsfi.xyz 申诉提醒", "；".join(alerts[:3]))
        log("告警: " + "；".join(alerts))
    else:
        brief = json.dumps({k: new.get(k) for k in watch_keys if k in new}, ensure_ascii=False)
        log(f"无变化 {brief}，无进展天数 {days}")
    try:
        with open(STATE, "w", encoding="utf-8") as fh:
            json.dump(new, fh, ensure_ascii=False, indent=2)
    except Exception as exc:
        log(f"状态写入失败: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
