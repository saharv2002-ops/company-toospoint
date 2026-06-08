#!/bin/bash
set -e

echo ""
echo "  ToosPoint RFQ Search — Setup & Launch"
echo "  ======================================"
echo ""

# ── 1. Xcode Command Line Tools (needed for git, python, etc.) ────────────────
if ! xcode-select -p &>/dev/null; then
  echo "  [1/5] Installing Xcode Command Line Tools..."
  xcode-select --install
  echo "        Follow the popup prompt, then re-run this script."
  exit 0
else
  echo "  [1/5] Xcode CLI tools ✓"
fi

# ── 2. Homebrew ───────────────────────────────────────────────────────────────
if ! command -v brew &>/dev/null; then
  echo "  [2/5] Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  # Add brew to PATH for Apple Silicon Macs
  if [[ -f /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  fi
else
  echo "  [2/5] Homebrew ✓"
fi

# ── 3. Python 3 ───────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "  [3/5] Installing Python 3..."
  brew install python3
else
  echo "  [3/5] Python $(python3 --version) ✓"
fi

# ── 4. Virtual environment + dependencies ────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"

echo "  [4/5] Setting up Python environment..."
if [[ ! -d "$VENV" ]]; then
  python3 -m venv "$VENV"
fi
source "$VENV/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet flask requests

echo "        Dependencies installed ✓"

# ── 5. API key config ─────────────────────────────────────────────────────────
CONFIG="$SCRIPT_DIR/rfp_config.json"
echo "  [5/5] Checking config..."

if [[ ! -f "$CONFIG" ]]; then
  echo ""
  echo "  ┌─────────────────────────────────────────────────────┐"
  echo "  │  SAM.gov API Key Setup                              │"
  echo "  │                                                     │"
  echo "  │  Get a free key at:                                 │"
  echo "  │  sam.gov → Account Details → System Accounts       │"
  echo "  └─────────────────────────────────────────────────────┘"
  echo ""
  read -rp "  Paste your SAM.gov API key (or press Enter to skip): " SAM_KEY
  cat > "$CONFIG" <<EOF
{
  "sam_api_key": "$SAM_KEY",
  "max_results": 25
}
EOF
  echo "        Config saved ✓"
else
  echo "        Config found ✓"
fi

# ── Launch ────────────────────────────────────────────────────────────────────
echo ""
echo "  Starting ToosPoint RFQ Search at http://127.0.0.1:5051"
echo "  Press Ctrl+C to stop."
echo ""

cd "$SCRIPT_DIR"
python3 rfq_search.py
