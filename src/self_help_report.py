#!/usr/bin/env python3
"""
Self-Help Report Generator
Queries the local tracking database to evaluate goals and print actionable daily and weekly behavioral feedback.
"""

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timedelta

STATE_DIR = Path.home() / ".local/share/self_helper"
DB_PATH = STATE_DIR / "goals_manager.db"

class ReportGenerator:
    """Reads usage records and translates metrics into daily and weekly coaching feedback."""
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _get_ascii_bar(self, percentage: float, width: int = 15) -> str:
        """Returns a terminal-friendly visual progress indicator."""
        filled_length = int(round(width * percentage / 100))
        # Ensure we clamp boundaries
        filled_length = max(0, min(width, filled_length))
        bar = "█" * filled_length + "░" * (width - filled_length)
        return f"[{bar}]"

    def get_daily_data(self, target_date: str) -> List[Dict[str, Any]]:
        goals_data = []
        with self._connect() as conn:
            # Query goals configuration
            cursor = conn.execute("SELECT app_pattern, target_seconds, is_limit FROM goals;")
            goals = cursor.fetchall()

            for pattern, target_sec, is_limit in goals:
                # Query daily accumulated time
                t_cursor = conn.execute(
                    "SELECT duration_seconds FROM daily_accumulated_time WHERE date = ? AND app_pattern = ?;",
                    (target_date, pattern)
                )
                row = t_cursor.fetchone()
                accumulated_sec = row[0] if row else 0

                goals_data.append({
                    "pattern": pattern,
                    "target_seconds": target_sec,
                    "accumulated_seconds": accumulated_sec,
                    "is_limit": bool(is_limit)
                })
        return goals_data

    def get_weekly_data(self) -> Dict[str, Any]:
        """Aggregates metrics for the last 7 days."""
        today = datetime.now()
        dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
        
        weekly_stats: Dict[str, List[int]] = {}
        goals_config: Dict[str, Dict[str, Any]] = {}

        with self._connect() as conn:
            # Fetch current goals metadata
            cursor = conn.execute("SELECT app_pattern, target_seconds, is_limit FROM goals;")
            for pattern, target_sec, is_limit in cursor.fetchall():
                weekly_stats[pattern] = [0] * 7
                goals_config[pattern] = {
                    "target_seconds": target_sec,
                    "is_limit": bool(is_limit)
                }

            # Gather records for each day of the week
            for idx, date_str in enumerate(dates):
                for pattern in weekly_stats.keys():
                    t_cursor = conn.execute(
                        "SELECT duration_seconds FROM daily_accumulated_time WHERE date = ? AND app_pattern = ?;",
                        (date_str, pattern)
                    )
                    row = t_cursor.fetchone()
                    if row:
                        weekly_stats[pattern][idx] = row[0]

        return {
            "dates": dates,
            "weekly_stats": weekly_stats,
            "config": goals_config
        }

    def get_top_apps(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Queries ActivityWatch REST API to fetch the top N most active applications today."""
        import socket
        import json
        import urllib.request
        
        hostname = socket.gethostname()
        
        # 1. Fetch buckets to find window bucket
        try:
            req = urllib.request.Request("http://127.0.0.1:5600/api/0/buckets", headers={"User-Agent": "SelfHelper/1.0"})
            with urllib.request.urlopen(req, timeout=2.0) as response:
                buckets = json.loads(response.read().decode("utf-8"))
        except Exception:
            return []
            
        window_bucket = next((b for b in buckets if "aw-watcher-window" in b and hostname in b), None)
        if not window_bucket:
            return []

        # 2. Fetch last 1000 events to cover active tracking scope
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:5600/api/0/buckets/{window_bucket}/events?limit=1000",
                headers={"User-Agent": "SelfHelper/1.0"}
            )
            with urllib.request.urlopen(req, timeout=2.0) as response:
                events = json.loads(response.read().decode("utf-8"))
        except Exception:
            return []

        # 3. Aggregate durations per application name for today
        app_durations = {}
        today_str = datetime.now().strftime("%Y-%m-%d")
        for event in events:
            timestamp_str = event.get("timestamp", "")
            if timestamp_str:
                event_date = timestamp_str.split("T")[0]
                if event_date != today_str:
                    continue

            data = event.get("data", {})
            app = data.get("app", "Unknown")
            if app == "Unknown":
                continue
            duration = event.get("duration", 0.0)
            app_durations[app] = app_durations.get(app, 0.0) + duration

        # Sort and take top N
        sorted_apps = sorted(app_durations.items(), key=lambda x: x[1], reverse=True)
        return [{"app": app_name, "seconds": dur} for app_name, dur in sorted_apps[:limit]]

    def print_daily_report(self) -> None:
        today_str = datetime.now().strftime("%Y-%m-%d")
        goals = self.get_daily_data(today_str)

        if not goals:
            print("No goals set yet! Add goals using 'self_helper.py add-goal' to generate coaching feedback.")
            return

        print(f"==================================================")
        print(f"       DAILY SELF-HELP REPORT ({today_str})     ")
        print(f"==================================================")
        
        focus_score = 0.0
        total_tracked = 0
        limit_violations = []
        target_successes = []
        ongoing_targets = []

        for g in goals:
            total_tracked += 1
            curr_hrs = g["accumulated_seconds"] / 3600.0
            tgt_hrs = g["target_seconds"] / 3600.0
            pct = (g["accumulated_seconds"] / g["target_seconds"]) * 100.0 if g["target_seconds"] > 0 else 0

            type_str = "LIMIT" if g["is_limit"] else "TARGET"
            bar = self._get_ascii_bar(pct)
            print(f"\n• [{type_str}] '{g['pattern']}' {bar} {pct:.1f}%")
            print(f"  Logged: {curr_hrs:.2f}h / {tgt_hrs:.2f}h")

            if g["is_limit"]:
                if pct >= 100.0:
                    print("  [CRITICAL] Limit Exceeded! Step away, close the app, and reset.")
                    limit_violations.append(g["pattern"])
                elif pct >= 80.0:
                    print("  [WARNING] You are close to your limit. Wrap up current tasks.")
                else:
                    print("  [GOOD] Keeping usage well within bounds.")
                    focus_score += 1.0
            else:
                if pct >= 100.0:
                    print("  [SUCCESS] Target Completed! Excellent consistency.")
                    target_successes.append(g["pattern"])
                    focus_score += 1.0
                elif pct > 0.0:
                    print("  [IN PROGRESS] Nice start! Keep pushing to reach your minimum.")
                    ongoing_targets.append(g["pattern"])
                    focus_score += (pct / 100.0)
                else:
                    print("  [NOT STARTED] Zero activity logged. Schedule time for this practice.")

        # Performance summary
        print(f"\n==================================================")
        print(f"             BEHAVIORAL ACTION PLAN               ")
        print(f"==================================================")
        
        overall_idx = (focus_score / total_tracked) * 100.0 if total_tracked > 0 else 0.0
        print(f"Daily Focus Index: {overall_idx:.1f}%")

        if limit_violations:
            print(f"\n[ALERT] Distraction Overrun: You breached limits on: {', '.join(limit_violations)}.")
            print("Recommendation: Shift physical environments to break the habit loop.")

        if target_successes:
            print(f"\n[VICTORY] You achieved your skill targets for: {', '.join(target_successes)}!")
            print("Recommendation: Maintain this momentum. Try to start with this app tomorrow.")

        if ongoing_targets:
            print(f"\n[NEXT STEPS] Complete your pending goals: {', '.join(ongoing_targets)}.")
            print("Recommendation: Plan a dedicated 45-minute focus window.")

        # Fetch and print top apps for transparency
        top_apps = self.get_top_apps(limit=5)
        if top_apps:
            print(f"\n==================================================")
            print(f"         TOP 5 MOST USED APPS TODAY               ")
            print(f"==================================================")
            for idx, item in enumerate(top_apps, start=1):
                app_name = item["app"]
                hrs = item["seconds"] / 3600.0
                print(f"  {idx}. '{app_name}': {hrs:.2f}h ({int(item['seconds'] // 60)}m)")

    def print_weekly_report(self) -> None:
        data = self.get_weekly_data()
        weekly_stats = data["weekly_stats"]
        config = data["config"]
        dates = data["dates"]

        if not weekly_stats:
            print("No goals set yet! Add goals to generate weekly coaching history.")
            return

        print(f"==================================================")
        print(f"         WEEKLY PERSISTENCE & TRENDS             ")
        print(f"==================================================")

        for pattern, daily_seconds in weekly_stats.items():
            cfg = config[pattern]
            target_sec = cfg["target_seconds"]
            is_limit = cfg["is_limit"]
            type_str = "LIMIT" if is_limit else "TARGET"
            
            total_sec = sum(daily_seconds)
            avg_sec = total_sec / 7.0
            
            print(f"\n★ App Pattern: '{pattern}' ({type_str})")
            print(f"  Weekly Cumulative: {total_sec / 3600.0:.2f}h | Daily Avg: {avg_sec / 3600.0:.2f}h")
            
            # Daily breakdowns inside sparkline
            print("  Daily History (last 7 days):")
            for day_idx, date_str in enumerate(dates):
                sec = daily_seconds[day_idx]
                pct = (sec / target_sec) * 100.0 if target_sec > 0 else 0
                weekday_name = datetime.strptime(date_str, "%Y-%m-%d").strftime("%a")
                bar = self._get_ascii_bar(pct, width=10)
                print(f"    {weekday_name}: {bar} {pct:.1f}% ({sec / 3600.0:.2f}h)")

            # Trend Calculation
            first_half_avg = sum(daily_seconds[:3]) / 3.0
            second_half_avg = sum(daily_seconds[4:]) / 3.0
            
            if first_half_avg > 0:
                trend_change = ((second_half_avg - first_half_avg) / first_half_avg) * 100.0
            else:
                trend_change = 100.0 if second_half_avg > 0 else 0.0

            trend_indicator = "UPWARD" if trend_change > 5.0 else ("DOWNWARD" if trend_change < -5.0 else "STABLE")
            
            # Actionable coaching feedback based on trends
            print(f"  Trend Analysis: {trend_indicator} ({trend_change:+.1f}% intensity change from early-week)")
            if not is_limit:
                if trend_indicator == "UPWARD":
                    print("  Coaching: Excellent trend! Your practice blocks are expanding.")
                elif trend_indicator == "DOWNWARD":
                    print("  Coaching: Warning! Focus is dropping. Re-examine your schedule structure.")
                else:
                    print("  Coaching: Steady output. Try raising your daily target by 15 mins to grow.")
            else:
                if trend_indicator == "UPWARD":
                    print("  Coaching: Warning! Distraction exposure is rising. Audit your browser habits.")
                elif trend_indicator == "DOWNWARD":
                    print("  Coaching: Success! Your exposure is decreasing. Keep this boundary strong.")
                else:
                    print("  Coaching: Boundary holds stable. Consider lowering the daily limit to tighten focus.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Self-Help Diagnostic and Telemetry Evaluator.")
    parser.add_argument("--weekly", action="store_true", help="Print weekly cumulative trend analysis.")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"Error: Goals database not found at {DB_PATH}. Initialize the daemon first.")
        sys.exit(1)

    generator = ReportGenerator(DB_PATH)
    if args.weekly:
        generator.print_weekly_report()
    else:
        generator.print_daily_report()


if __name__ == "__main__":
    main()
