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

## 📖 Extensive Daily Workflow & Usage Guide

To get the absolute most out of the Self-Helper ecosystem, follow this comprehensive daily operation guide. This walkthrough demonstrates how the CLI, background daemon, and AI coaching interact throughout your day.

### 0. Verify & Manage the Background Service
After running `install.sh`, the background telemetry daemon (`self-helper.service`) runs automatically via systemd. You can manage and check its status anytime:
```bash
# Check if the service is actively logging your windows and tabs
shtool status

# Restart the service (e.g., after modifying global configuration)
shtool restart
```

---

### Step 1: Morning Check-In & Setting Intentions
Start your day by establishing your persona, logging your baseline energy/focus, and checking today's limits.

```bash
# 1. Apply a lifestyle preset (auto-loads tailored habits and limits)
shtool preset engineer    # Options: student, nurse, engineer, hobbyist

# 2. Log your morning mood and focus on a 1-10 scale (automatically captures local weather!)
shtool mood

# 3. View your active goals and boundaries for the day
shtool goals
```

---

### Step 2: Entering Deep Work (Pomodoro + Active Mitigation)
When it is time to study or code without distraction, trigger the native focus timer.

```bash
# Start a 25-minute Pomodoro Deep Work session
shtool focus 25
```
**What happens:**
- A live countdown timer renders in your terminal.
- **Active Mitigation**: Every 5 seconds, the system scans for running applications matching your configured `LIMIT` goals (`firefox`, `x.com`, etc.) and automatically terminates them (`pkill`).
- When the timer completes, an audio chime plays (`paplay`) and you are prompted to log the session directly into your `study_journal`.

---

### Step 3: Active Recall & Spaced Repetition (SRS)
Review your flashcards when your cognitive energy is fresh.

```bash
# Add new questions as you read documentation or textbooks
shtool question add

# Run your Spaced Repetition self-test
shtool quiz
```
**What happens:**
- The SuperMemo-2 algorithm calculates which flashcards are **due today** based on your past confidence scores (`1-5`).
- Overdue questions appear first; answering with high confidence (`4-5`) pushes the next review interval days or weeks into the future.

---

### Step 4: Mid-Day Diagnostic & Local AI Coaching
At mid-day or whenever you feel your focus slipping, consult your local offline AI coach (`smollm2:360m`).

```bash
# Get your daily goal progress + 3 actionable AI coaching interventions
shtool report --ai
```
**What happens:**
- Self-Helper queries your local SQLite database and generates a structured JSON telemetry dump (`~/.local/share/self_helper/self_helper_dump.json`).
- Your local Ollama instance (`smollm2:360m`) reads the payload locally—no data ever leaves your machine—and outputs 3 direct, hyper-specific bullet points addressing your exact screen time and habits.

---

### Step 5: Evening Reflection & Habit Ticking
Wrap up your evening by logging your habits and reflecting on what you learned.

```bash
# 1. Interactive daily habit check-in (toggle done/undone)
shtool habit track

# 2. Run a guided evening reflection journal session
shtool journal

# 3. Need a quick boost or random quote before logging off?
shtool quotes --theme focus
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

## 🤖 AI Coaching Skill & Telemetry Ingestion

Self-Helper features a native **AI Coaching Skill Architecture** designed for ultra-low resource offline inference (`smollm2:360m`). When running `shtool report --ai` or piping `shtool dump` into external agentic workflows (`llm`, `aichat`, or custom scripts), the AI ingests a comprehensive 10-dimension JSON payload covering:

1. **Boundary & Limit Adherence**: Screen-time usage across apps and domains vs. configured `LIMIT` / `TARGET` goals (`is_limit`).
2. **Spaced Repetition Pulse**: Overdue flashcard review checks (`next_review_date`) and confidence level trajectories.
3. **Behavioral & Mood Correlations**: Cross-referencing `study_journal`, `habit_logs`, and `mood_journal` check-ins to identify burnout or distraction fatigue.

For the exact system prompt rules, schema breakdowns, and guidance on extending this skill with custom models, see our official specification:
👉 **[doc/AI_COACHING_SKILL.md](doc/AI_COACHING_SKILL.md)**

---

## Future Roadmap

We are constantly evolving to make Self-Helper the ultimate productivity OS. Our progress:

- ✅ **True Spaced Repetition System (SRS)**: Algorithmic flashcard scheduling (SuperMemo-2) via `shtool quiz`.
- ✅ **Native Pomodoro & Deep Work Mode**: Terminal countdown (`shtool focus`) with active process mitigation (`pkill`) and auto-logging to your study journal.
- ✅ **Local AI Coaching Integration**: Sub-250MB offline coaching (`smollm2:360m`) via `shtool report --ai` providing 3 actionable micro-interventions.
- 🚧 **Automated Background Mitigation**: Implicit daemon-based application enforcement.
- 🚧 **Gamification & Streaks**: Persistent tracking of goal streaks (e.g., "7-day coding streak") to boost consistency.
- 🚧 **Terminal User Interface (TUI)**: Building a rich, persistent terminal dashboard for real-time visualization of habits, progress bars, and journal entries.

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
