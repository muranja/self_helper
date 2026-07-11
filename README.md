# Self-Helper Telemetry System

A production-grade, low-overhead activity tracking, journaling, and behavioral coaching framework for Linux desktop environments. 

---

## The Soul of the Tool (Philosophy)

Self-Helper is built on the premise that **mindless restriction doesn't work; mindful tracking and reflection do.** 

It is not just a website blocker. It is a comprehensive digital ecosystem designed to help you build a healthier relationship with your screen time. By combining passive telemetry (tracking what you do) with active journaling (asking how you feel and what you've learned), Self-Helper bridges the gap between *raw data* and *behavioral change*. It empowers you to build habits, master new subjects through active recall, and understand the environmental factors (like mood and weather) that affect your deep work.

---

## Technology Stack

- **Core Engine:** Pure Python 3 (No heavy external dependencies).
- **Data Persistence:** Local, fast, and secure **SQLite** database using WAL mode for concurrent read/writes.
- **Telemetry Integration:** Interfaces directly with the **ActivityWatch REST API** for window and browser domain tracking.
- **Background Service:** Native Linux **Systemd** user services for resilient, invisible background operation.
- **CLI / Interface:** Native terminal interface (`shtool`) and optional lightweight desktop rendering using **Conky**.
- **External APIs:** Integrates seamlessly with offline-first design, falling back to free APIs (like `wttr.in`) for environmental context (weather) when available.

---

## Features (Currently Implemented)

- **Dual-Engine Tracking**: Passive telemetry matching desktop window events combined with browser tab/URL aggregation via the ActivityWatch Firefox Extension.
- **Persona Presets**: Instantly configure the tool for your lifestyle (`student`, `nurse`, `engineer`, `hobbyist`) with pre-loaded goals, habits, and learning subjects.
- **Structured Goal Storage**: Set strict daily limits (e.g., max 1 hour of YouTube) or productive targets (e.g., min 2 hours of terminal/coding).
- **Guided Mood & Reflection Journals**: Log your mood on a 1-10 scale (including energy and focus), track gratitude, and answer structured prompts for morning/evening reflection. Includes automatic local weather context.
- **Daily Habit Tracker**: Add recurring daily habits and check them off interactively right in your terminal.
- **Flashcard Catalog & Quizzes**: Add active recall questions to your learning subjects and test yourself using the built-in `shtool quiz` command. Tracks your confidence levels (1-5) over time.
- **Study Journal**: Log dedicated study sessions, tracking duration, topic, and understanding ratings.
- **CLI Coaching Reports**: Detailed daily progress visualizations and 7-day cumulative reports highlighting distraction trends and peak focus blocks.
- **AI-Ready JSON Exports**: Run `shtool dump` to export your entire database (goals, usage, moods, habits, study logs) into a structured JSON payload (Schema v2.0), perfect for ingestion by AI coaches for deep semantic suggestions.
- **Configurable Privacy Levels**: Complete local control over database logging depth (low, medium, or high privacy filtering).

---

## How It Really Works

1. **The Daemon (`self-helper.service`)**: A lightweight Python script runs in the background. Every few seconds, it queries the local ActivityWatch server to see what window or browser tab is currently active.
2. **The Database**: If the active window matches one of your configured "goals" (e.g., `youtube.com` or `terminal`), the daemon updates the `daily_accumulated_time` table in your local SQLite database.
3. **The Interface (`shtool`)**: When you run `shtool` commands, you are interacting with this database. You can view your progress, log manual entries (like habits or moods), or configure your goals. 
4. **The Alerts**: The daemon continuously checks your accumulated time against your targets. If you are approaching a `limit` goal, it triggers a non-spammy system notification (and optional audio chimes) to remind you to step away.

---

## Installation & Setup

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

## Command Reference (`shtool`)

| Category | Command | Description |
|---|---|---|
| **Coaching** | `shtool report` | Daily goal performance & coaching advice |
| | `shtool weekly` | 7-day trends & coaching |
| | `shtool dump` | Export full database to JSON for AI analysis |
| **Settings** | `shtool preset <name>` | Apply a persona preset (student, nurse, engineer, hobbyist) |
| | `shtool goals` | List all limits and focus targets |
| | `shtool add/edit/remove` | Manage your tracking goals |
| **Learning** | `shtool study` | Log a guided study session |
| | `shtool learning-goal` | Manage learning subjects (add/remove/list) |
| | `shtool quiz` | Self-test with flashcards and update confidence |
| **Mindset** | `shtool habit track` | Manage and tick off daily habits |
| | `shtool mood` | Log a guided mood check-in (scored 1-10) |
| | `shtool journal` | Run a guided journal session (study/reflection/evening) |
| | `shtool quotes` | Motivational quotes & facts by theme |

---

## Future Roadmap

We are constantly evolving to make Self-Helper the ultimate productivity OS. Upcoming features include:

- **True Spaced Repetition System (SRS)**: Upgrading `shtool quiz` with an algorithmic scheduler (like SuperMemo-2) to optimize flashcard review times based on past confidence scores.
- **Native Pomodoro & Deep Work Mode**: A `shtool focus` command that starts a timer and actively manipulates system configurations (like `/etc/hosts`) to aggressively block distracting domains during study sessions.
- **Local AI Coaching Integration**: Integrating local LLMs (via Ollama) directly into `shtool report` to provide dynamic, conversational coaching advice based on your telemetry without exporting data externally.
- **Terminal User Interface (TUI)**: Building a rich, persistent terminal dashboard for real-time visualization of habits, progress bars, and journal entries.
- **Gamification & Streaks**: Persistent tracking of goal streaks (e.g., "7-day coding streak") to boost dopamine and consistency.

---

## Support the Project & Donate

If Self-Helper has helped you optimize your screen time, manage digital distractions, and focus on deep work, consider supporting development!

Your donations help maintain open-source system tool integration layers, new dashboard features, and notification extensions.

- **Buy Me A Coffee**: [buymeacoffee.com/muranja](https://www.buymeacoffee.com/muranja)
- **GitHub Sponsors**: Sponsor `@muranja` directly on GitHub.
- **PayPal**: Send support to [paypal.me/muranja](https://paypal.me/muranja)
- **Lightning Network (BTC)**: `muranja@getalby.com`

---

## License
This project is licensed under the MIT License. Feel free to fork, adapt, and share!
