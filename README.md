# ⚡ Self-Helper Telemetry System

A production-grade, low-overhead activity tracking and behavioral coaching framework for Linux desktop environments (fully compatible with both **Wayland** and **X11** sessions). 

Self-Helper integrates directly with **ActivityWatch** for window and browser telemetry, matches your time against customized daily targets or limits in a local database, provides active real-time notification alerts, and compiles structured JSON reports ready for AI self-help advisers.

---

## ✨ Features

- **🚀 Dual-Engine Tracking**: Passive telemetry matching desktop window events combined with browser tab/URL aggregation via the ActivityWatch Firefox Extension.
- **📂 Structured SQLite goal storage**: Handles sub-second daily calculations for strict boundaries and productive target goals.
- **📈 CLI Coaching Reports**: Detailed daily progress visualizations and 7-day cumulative reports highlighting distraction trends and peak focus blocks.
- **🛡️ Configurable Privacy Levels**: Complete local control over database logging depth (low, medium, or high privacy filtering).
- **🖥️ Desktop Widget Overlay**: Lightweight rendering using Conky (`~2s` updates) to display your current focus status right on your wallpaper.
- **🔔 Resilient Notifications**: Deduplicated active alert system that warns you as you approach daily boundary limits without spamming your desktop.

---

## 🛠️ Privacy Settings

Giving you full control over how much window, domain, or link detail is logged and dumped for analysis. Configure your tracking depth using:

```bash
shtool config --privacy [low | medium | high]
```

- **Low Privacy (High Context - Default)**: Logs active goals, system application usage, base website domains, and the **exact page URLs + titles** visited. Ideal for feeding to AI coaches for deep semantic suggestions.
- **Medium Privacy (Standard Detail)**: Logs goals, system application usage, and website domains. **Excludes exact URLs and webpage titles**.
- **High Privacy (Goal-Only Detail)**: Logs configured goals and matched totals only. **Disables ActivityWatch telemetry fetching**. Excludes all non-goal system applications and web activities.

---

## 🚀 Installation & Setup

### 1. Prerequisites
Ensure the following packages are running on your system:
- **ActivityWatch**: Install and execute `aw-qt`.
- **Firefox Extension**: Install the [ActivityWatch Firefox Add-on](https://addons.mozilla.org/en-US/firefox/addon/activitywatch/) and enable URL tracking.
- **Conky (Optional)**: Install `conky-all` for the wallpaper widget.

### 2. Git Clone and Run Installer
```bash
git clone https://github.com/muranja/self_helper.git
cd self_helper
chmod +x install.sh
./install.sh
```

### 3. Load Aliases
```bash
source ~/.bashrc
```

---

## 📖 Command Reference (`shtool`)

| Command | Arguments | Description |
|---|---|---|
| `shtool` | `None` / `--help` | Prints the colorized subcommand dashboard map |
| `shtool config` | `None` | Displays active system and privacy settings |
| `shtool config` | `--privacy [low/medium/high]` | Sets data filter level |
| `shtool status` | `None` | Evaluates system load, active task, and target bars |
| `shtool goals` | `None` | Lists configured limits and minimum target thresholds |
| `shtool add` | `--pattern <regex> --hours <N> [--limit]` | Adds a new daily tracking pattern (limit = max, default = min) |
| `shtool report` | `None` | Compiles daily focus summaries and top 5 applications |
| `shtool weekly` | `None` | Outputs 7-day coaching trends and trend analysis |
| `shtool dump` | `None` | Exports historical activity to `~/self_helper_dump.json` |
| `shtool daemon` | `None` | Displays user-level systemd service status |
| `shtool restart`| `None` | Restarts the background synchronization daemon |

---

## ☕ Support the Project & Donate

If Self-Helper has helped you optimize your screen time, manage digital distractions, and focus on deep work, consider supporting development!

Your donations help maintain open-source system tool integration layers, new dashboard features, and notification extensions.

- **☕ Buy Me A Coffee**: [buymeacoffee.com/muranja](https://www.buymeacoffee.com/muranja)
- **💖 GitHub Sponsors**: Sponsor `@muranja` directly on GitHub.
- **💵 PayPal**: Send support to [paypal.me/muranja](https://paypal.me/muranja)
- **⚡ Lightning Network (BTC)**: `muranja@getalby.com`

---

## 📝 License
This project is licensed under the MIT License. Feel free to fork, adapt, and share!
