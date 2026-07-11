#!/usr/bin/env python3
"""
Self-Helper Integration Daemon
Integrates ActivityWatch, system metrics, and local goal management into a unified database and widget source.
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import socket
import sqlite3
import sys
import urllib.request
import urllib.error
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Graceful optional import of psutil
try:
    import psutil
except ImportError:
    psutil = None

# System Paths setup
CACHE_DIR = Path.home() / ".cache/self_helper"
STATE_DIR = Path.home() / ".local/share/self_helper"
for directory in (CACHE_DIR, STATE_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# Logger Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(STATE_DIR / "helper_daemon.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SelfHelper")


@dataclass(frozen=True)
class Goal:
    id: Optional[int]
    app_pattern: str  # String match pattern (e.g. 'chrome', 'slack', 'code')
    target_seconds: int  # Daily limit or target (seconds)
    is_limit: bool  # True if it's a maximum limit, False if target (minimum)
    created_at: str


@dataclass
class DailySummary:
    timestamp: str
    cpu_utilization: float
    ram_utilization: float
    active_app: str
    active_window: str
    is_afk: bool
    goals_progress: List[Dict[str, Any]]


class ActivityWatchClient:
    """Interacts with the local ActivityWatch REST API wrapper."""
    def __init__(self, host: str = "127.0.0.1", port: int = 5600) -> None:
        self.base_url = f"http://{host}:{port}/api/0"
        self.hostname = socket.gethostname()

    def _get(self, endpoint: str) -> Optional[Any]:
        url = f"{self.base_url}/{endpoint}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SelfHelperDaemon/1.0"})
            with urllib.request.urlopen(req, timeout=2.0) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as e:
            logger.debug(f"Could not connect to ActivityWatch API at {url}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Malformed JSON response from {url}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Unexpected connection error querying {url}: {e}")
            return None

    def get_current_state(self) -> Dict[str, Any]:
        """Fetches the latest active window and AFK status from ActivityWatch buckets."""
        state = {
            "app": "Unknown",
            "title": "Unknown",
            "is_afk": True
        }

        # Resolve bucket IDs dynamically based on current hostname
        buckets = self._get("buckets")
        if not buckets:
            return state

        window_bucket = next((b for b in buckets if "aw-watcher-window" in b and self.hostname in b), None)
        afk_bucket = next((b for b in buckets if "aw-watcher-afk" in b and self.hostname in b), None)
        web_bucket = next((b for b in buckets if "aw-watcher-web" in b and self.hostname in b), None)

        if window_bucket:
            # Query last window event
            events = self._get(f"buckets/{window_bucket}/events?limit=1")
            if events and isinstance(events, list) and len(events) > 0:
                data = events[0].get("data", {})
                state["app"] = data.get("app", "Unknown")
                state["title"] = data.get("title", "Unknown")

        if afk_bucket:
            # Query last AFK status event
            events = self._get(f"buckets/{afk_bucket}/events?limit=1")
            if events and isinstance(events, list) and len(events) > 0:
                data = events[0].get("data", {})
                state["is_afk"] = data.get("status", "unknown") == "afk"

        # If it is a browser application, overlay domain-level telemetry
        browser_apps = ("firefox", "chrome", "chromium", "brave", "opera", "google-chrome")
        if state["app"].lower() in browser_apps and web_bucket:
            web_events = self._get(f"buckets/{web_bucket}/events?limit=1")
            if web_events and isinstance(web_events, list) and len(web_events) > 0:
                web_data = web_events[0].get("data", {})
                url = web_data.get("url", "")
                title = web_data.get("title", "")
                if url:
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(url).netloc
                        if domain.startswith("www."):
                            domain = domain[4:]
                    except Exception:
                        domain = ""
                    
                    if domain:
                        state["app"] = f"{state['app']} ({domain})"
                    if title:
                        state["title"] = title

        return state


class GoalStore:
    """Manages SQLite persistence layer for user goals."""
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_pattern TEXT NOT NULL UNIQUE,
                    target_seconds INTEGER NOT NULL,
                    is_limit INTEGER NOT NULL, -- 1 = limit (max), 0 = target (min)
                    created_at TEXT NOT NULL
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_accumulated_time (
                    date TEXT NOT NULL,
                    app_pattern TEXT NOT NULL,
                    duration_seconds INTEGER DEFAULT 0,
                    PRIMARY KEY (date, app_pattern)
                );
            """)
            conn.commit()

    def add_goal(self, goal: Goal) -> bool:
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO goals (app_pattern, target_seconds, is_limit, created_at) VALUES (?, ?, ?, ?);",
                    (goal.app_pattern, goal.target_seconds, 1 if goal.is_limit else 0, goal.created_at)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Goal pattern '{goal.app_pattern}' already exists.")
            return False

    def list_goals(self) -> List[Goal]:
        with self._connect() as conn:
            cursor = conn.execute("SELECT id, app_pattern, target_seconds, is_limit, created_at FROM goals;")
            return [Goal(r[0], r[1], r[2], r[3] == 1, r[4]) for r in cursor.fetchall()]

    def log_time(self, date_str: str, app_pattern: str, seconds: int) -> None:
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO daily_accumulated_time (date, app_pattern, duration_seconds)
                VALUES (?, ?, ?)
                ON CONFLICT(date, app_pattern) DO UPDATE SET
                duration_seconds = duration_seconds + excluded.duration_seconds;
            """, (date_str, app_pattern, seconds))
            conn.commit()

    def get_progress(self, date_str: str) -> List[Dict[str, Any]]:
        progress_reports = []
        goals = self.list_goals()
        
        with self._connect() as conn:
            for goal in goals:
                cursor = conn.execute(
                    "SELECT duration_seconds FROM daily_accumulated_time WHERE date = ? AND app_pattern = ?;",
                    (date_str, goal.app_pattern)
                )
                row = cursor.fetchone()
                current_duration = row[0] if row else 0
                
                progress_reports.append({
                    "app_pattern": goal.app_pattern,
                    "target_seconds": goal.target_seconds,
                    "current_seconds": current_duration,
                    "is_limit": goal.is_limit,
                    "status_percentage": min(100.0, (current_duration / goal.target_seconds) * 100.0)
                })
        return progress_reports


class SystemMonitor:
    """Fetches real-time host resource statistics."""
    def get_utilization(self) -> Dict[str, float]:
        if psutil is None:
            return {"cpu": 0.0, "ram": 0.0}
        try:
            return {
                "cpu": psutil.cpu_percent(interval=None),
                "ram": psutil.virtual_memory().percent
            }
        except Exception as e:
            logger.debug(f"Failed to fetch system metrics via psutil: {e}")
            return {"cpu": 0.0, "ram": 0.0}


class IntegrationDaemon:
    """Drives the polling cycle, coordinates components, and writes state caching."""
    def __init__(self, api_client: ActivityWatchClient, store: GoalStore, monitor: SystemMonitor) -> None:
        self.api = api_client
        self.store = store
        self.monitor = monitor
        self.should_run = True
        self.poll_interval = 2.0  # Poll status every 2 seconds
        self.notified_goals = set()
        self.current_date_str = datetime.now().strftime("%Y-%m-%d")

    def _send_notification(self, title: str, message: str, urgency: str = "normal") -> None:
        """Fires a standard libnotify desktop alert."""
        try:
            import subprocess
            subprocess.run(["notify-send", "-u", urgency, title, message], check=False)
        except Exception as e:
            logger.debug(f"Failed to issue notify-send: {e}")

    async def run(self) -> None:
        logger.info("Initializing background integration loops...")
        
        while self.should_run:
            try:
                # 1. Fetch data from systems
                sys_metrics = self.monitor.get_utilization()
                aw_state = self.api.get_current_state()
                today_str = datetime.now().strftime("%Y-%m-%d")

                # 2. Update local tracked database for goals matching current app
                if not aw_state["is_afk"] and aw_state["app"] != "Unknown":
                    # Match goals and attribute duration increment
                    goals = self.store.list_goals()
                    for goal in goals:
                        if goal.app_pattern.lower() in aw_state["app"].lower() or \
                           goal.app_pattern.lower() in aw_state["title"].lower():
                            self.store.log_time(today_str, goal.app_pattern, int(self.poll_interval))

                # 3. Compile Progress Report
                progress = self.store.get_progress(today_str)
                
                # Check for day boundary to flush notification logs
                if today_str != self.current_date_str:
                    self.notified_goals.clear()
                    self.current_date_str = today_str

                # Evaluate notification alerts based on goal targets/limits
                for gp in progress:
                    pct = gp['status_percentage']
                    pattern = gp['app_pattern']
                    is_limit = gp['is_limit']

                    if is_limit:
                        if pct >= 100.0 and (pattern, "limit_exceeded") not in self.notified_goals:
                            self._send_notification(
                                "Goal Limit Exceeded",
                                f"Daily boundary breached for '{pattern}'!",
                                "critical"
                            )
                            self.notified_goals.add((pattern, "limit_exceeded"))
                        elif pct >= 80.0 and (pattern, "limit_warning") not in self.notified_goals:
                            self._send_notification(
                                "Goal Limit Warning",
                                f"You have reached {pct:.0f}% of your daily limit for '{pattern}'!",
                                "normal"
                            )
                            self.notified_goals.add((pattern, "limit_warning"))
                    else:
                        if pct >= 100.0 and (pattern, "target_completed") not in self.notified_goals:
                            self._send_notification(
                                "Goal Target Achieved!",
                                f"Congratulations! You completed your daily target for '{pattern}'!",
                                "normal"
                            )
                            self.notified_goals.add((pattern, "target_completed"))

                summary = DailySummary(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    cpu_utilization=sys_metrics["cpu"],
                    ram_utilization=sys_metrics["ram"],
                    active_app=aw_state["app"],
                    active_window=aw_state["title"],
                    is_afk=aw_state["is_afk"],
                    goals_progress=progress
                )

                # 4. Atomically write cache to avoid race conditions with widget UI reads
                temp_cache = CACHE_DIR / "status.json.tmp"
                with open(temp_cache, "w") as f:
                    json.dump(asdict(summary), f, indent=2)
                temp_cache.replace(CACHE_DIR / "status.json")

                # 5. Format flat-text dashboard for lightweight widget consumption
                widget_lines = [
                    f"CPU: {sys_metrics['cpu']:.1f}% | RAM: {sys_metrics['ram']:.1f}%",
                    f"App: {aw_state['app']} ({'AFK' if aw_state['is_afk'] else 'Active'})",
                    f"Title: {aw_state['title'][:40]}..." if len(aw_state['title']) > 40 else f"Title: {aw_state['title']}",
                    "",
                    "GOALS:"
                ]
                if not progress:
                    widget_lines.append("  No goals configured.")
                else:
                    for gp in progress:
                        g_type = "LMT" if gp['is_limit'] else "TGT"
                        cur_hrs = gp['current_seconds'] / 3600.0
                        tgt_hrs = gp['target_seconds'] / 3600.0
                        pct = gp['status_percentage']
                        
                        # Generate ascii bar for conky
                        filled = int(round(10 * pct / 100))
                        filled = max(0, min(10, filled))
                        bar = "█" * filled + "░" * (10 - filled)
                        
                        widget_lines.append(f"  • {g_type} '{gp['app_pattern']}': [{bar}] {pct:.1f}% ({cur_hrs:.2f}h/{tgt_hrs:.2f}h)")

                temp_widget = CACHE_DIR / "widget.txt.tmp"
                with open(temp_widget, "w") as f:
                    f.write("\n".join(widget_lines) + "\n")
                temp_widget.replace(CACHE_DIR / "widget.txt")

            except Exception as e:
                logger.error(f"Error encountered in execution iteration: {e}", exc_info=True)
            
            await asyncio.sleep(self.poll_interval)

    def stop(self, *args: Any) -> None:
        logger.info("Termination signal received. Exiting daemon process gracefully...")
        self.should_run = False


def cli_main() -> None:
    parser = argparse.ArgumentParser(description="Self-Helper Goal and Tracker daemon integration.")
    subparsers = parser.add_subparsers(dest="command", help="Operational commands")

    # Daemon Execution Parser
    subparsers.add_parser("start-daemon", help="Launch the background monitoring engine.")

    # Goal Management Parsers
    add_parser = subparsers.add_parser("add-goal", help="Configure a new time goal.")
    add_parser.add_argument("--pattern", required=True, type=str, help="Application name or window title pattern.")
    add_parser.add_argument("--hours", required=True, type=float, help="Target time threshold (in hours).")
    add_parser.add_argument("--limit", action="store_true", help="Mark goal as a limit (max allowance) instead of a target.")

    subparsers.add_parser("list-goals", help="Print all configured productivity goals.")
    subparsers.add_parser("status", help="Read current status and goals progress.")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    db_path = STATE_DIR / "goals_manager.db"
    store = GoalStore(db_path)
    client = ActivityWatchClient()
    monitor = SystemMonitor()

    if args.command == "start-daemon":
        daemon = IntegrationDaemon(client, store, monitor)
        
        # Standard POSIX signal bindings
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, daemon.stop)

        try:
            loop.run_until_complete(daemon.run())
        finally:
            loop.close()

    elif args.command == "add-goal":
        seconds = int(args.hours * 3600)
        success = store.add_goal(Goal(
            id=None,
            app_pattern=args.pattern,
            target_seconds=seconds,
            is_limit=args.limit,
            created_at=datetime.now(timezone.utc).isoformat()
        ))
        if success:
            print(f"Goal set successfully for pattern '{args.pattern}' -> {args.hours} hours.")
        else:
            print("Failed to save goal configuration.")

    elif args.command == "list-goals":
        goals = store.list_goals()
        if not goals:
            print("No goals set yet. Use 'add-goal' to configure goals.")
            return
        for g in goals:
            goal_type = "Max Limit" if g.is_limit else "Min Target"
            print(f"[{g.id}] Pattern: '{g.app_pattern}' | Target: {g.target_seconds/3600:.2f}h | Type: {goal_type}")

    elif args.command == "status":
        cache_file = CACHE_DIR / "status.json"
        if not cache_file.exists():
            print("No status logs are cached. Ensure the background daemon is running.")
            return
        
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading status cache file: {e}")
            return
            
        print("=== SYSTEM & ACTIVITY STATUS ===")
        print(f"Updated At: {data['timestamp']}")
        print(f"CPU usage:  {data['cpu_utilization']}% | RAM: {data['ram_utilization']}%")
        print(f"Focus App:  {data['active_app']} (AFK: {data['is_afk']})")
        print(f"Title:      {data['active_window']}")
        print("\n=== GOAL PROGRESS FOR TODAY ===")
        if not data.get('goals_progress'):
            print("No goal progress data recorded yet.")
        else:
            for gp in data['goals_progress']:
                g_type = "LIMIT" if gp['is_limit'] else "TARGET"
                cur_hrs = gp['current_seconds'] / 3600.0
                tgt_hrs = gp['target_seconds'] / 3600.0
                print(f"• [{g_type}] '{gp['app_pattern']}': {cur_hrs:.2f}h / {tgt_hrs:.2f}h ({gp['status_percentage']:.1f}%)")


if __name__ == "__main__":
    cli_main()
