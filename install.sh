#!/usr/bin/env bash
# ==============================================================================
# Self-Helper Telemetry System - One-Click Installer Script
# ==============================================================================
set -e

# Visual colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "======================================================================"
echo "          INSTALLING SELF-HELPER TELEMETRY & COACHING SYSTEM          "
echo "======================================================================"
echo -e "${NC}"

# 1. Establish necessary folders
echo -e "${BLUE}[1/5] Establishing folder structure...${NC}"
mkdir -p "$HOME/.local/bin"
mkdir -p "$HOME/.config/conky"
mkdir -p "$HOME/.config/systemd/user"
mkdir -p "$HOME/.config/autostart"
echo -e "  ${GREEN}✓ Target folders configured.${NC}"

# 2. Copy source and asset files
echo -e "${BLUE}[2/5] Deploying scripts and configurations...${NC}"
cp src/self_helper.py "$HOME/.local/bin/self_helper.py"
cp src/self_help_report.py "$HOME/.local/bin/self_help_report.py"
cp src/shtool "$HOME/.local/bin/shtool"
cp config/self_helper.conf "$HOME/.config/conky/self_helper.conf"
cp config/self-helper.service "$HOME/.config/systemd/user/self-helper.service"
cp config/activitywatch-xhost.desktop "$HOME/.config/autostart/activitywatch-xhost.desktop"

# Make binaries executable
chmod +x "$HOME/.local/bin/self_helper.py"
chmod +x "$HOME/.local/bin/self_help_report.py"
chmod +x "$HOME/.local/bin/shtool"
echo -e "  ${GREEN}✓ File deployment successful.${NC}"

# 3. Handle systemd registration
echo -e "${BLUE}[3/5] Registering tracking background daemon...${NC}"
systemctl --user daemon-reload
systemctl --user enable self-helper.service
systemctl --user restart self-helper.service
echo -e "  ${GREEN}✓ Systemd user daemon registered and started.${NC}"

# 4. Handle shell alias installation
echo -e "${BLUE}[4/5] Updating shell configuration...${NC}"
BASHRC="$HOME/.bashrc"
ALIAS_LINE="alias shtool=\"\$HOME/.local/bin/shtool\""

if [ -f "$BASHRC" ]; then
    if grep -q "shtool" "$BASHRC"; then
        echo -e "  ${YELLOW}! Alias already exists in ~/.bashrc, updating hook...${NC}"
        # Remove old sh- or shtool lines to keep it clean
        sed -i '/self_helper.py/d' "$BASHRC"
        sed -i '/self_help_report.py/d' "$BASHRC"
        sed -i '/shtool/d' "$BASHRC"
    fi
    # Append fresh alias at the end of .bashrc
    echo -e "\n# Self-Helper Telemetry system alias\n$ALIAS_LINE" >> "$BASHRC"
    echo -e "  ${GREEN}✓ Registered shtool base alias in ~/.bashrc${NC}"
else
    echo -e "  ${YELLOW}! ~/.bashrc not found. Please add the following alias manually:${NC}"
    echo -e "    ${CYAN}alias shtool=\"\$HOME/.local/bin/shtool\"${NC}"
fi

# 5. Dependencies and validations check
echo -e "${BLUE}[5/5] Running system checks...${NC}"
if ! command -v aw-qt &> /dev/null; then
    echo -e "  ${YELLOW}! Warning: 'aw-qt' (ActivityWatch) command not found in PATH.${NC}"
    echo -e "    Make sure ActivityWatch is running for tracking to populate."
else
    echo -e "  ${GREEN}✓ ActivityWatch verified.${NC}"
fi

if ! command -v conky &> /dev/null; then
    echo -e "  ${YELLOW}! Warning: 'conky' is not installed. Desktop widget requires it.${NC}"
    echo -e "    Install it via: ${CYAN}sudo apt install conky-all${NC}"
else
    echo -e "  ${GREEN}✓ Conky desktop widget engine verified.${NC}"
fi

# SUCCESS BANNER
echo -e "${GREEN}"
echo "======================================================================"
echo "          INSTALLATION COMPLETE - SELF-HELPER IS NOW READY!          "
echo "======================================================================"
echo -e "${NC}"
echo -e "To reload environment and start using shtool:"
echo -e "  ${CYAN}source ~/.bashrc${NC}"
echo -e ""
echo -e "Set your daily targets and boundaries:"
echo -e "  ${CYAN}shtool add --pattern \"terminal\" --hours 2${NC} (Productivity Target)"
echo -e "  ${CYAN}shtool add --pattern \"youtube.com\" --hours 1 --limit${NC} (Usage boundary)"
echo -e ""
echo -e "Check your live dashboard overlay or dump files:"
echo -e "  ${CYAN}shtool status${NC}"
echo -e "  ${CYAN}shtool dump${NC}"
echo -e ""
echo -e "To support the developer, check the donation section in the README.md!"
echo -e "======================================================================"
