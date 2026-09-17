#!/usr/bin/env bash
# ==============================================================================
# Launch Audacity 4 with tracks in order for: Living for the City
# Artist: Stevie Wonder (1973)
# Album:  Innervisions
# Tempo:  98.0 BPM | Key: F# minor
#
# Usage:
#   ./launch.sh           # Load all tracks (00_full_song.wav, 01_..., ...) in order
#   ./launch.sh --project # Open saved .aup4 project file if present
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Locate Audacity binary
if [ -n "${AUDACITY_BIN:-}" ]; then
    AUDACITY="$AUDACITY_BIN"
elif [ -f "$HOME/AppImages/audacity-linux-4.0.0-x86_64.AppImage" ]; then
    AUDACITY="$HOME/AppImages/audacity-linux-4.0.0-x86_64.AppImage"
elif compgen -G "$HOME/AppImages/*audacity*.AppImage" > /dev/null 2>&1; then
    AUDACITY="$(ls -t "$HOME"/AppImages/*audacity*.AppImage | head -n 1)"
elif command -v audacity >/dev/null 2>&1; then
    AUDACITY="$(command -v audacity)"
else
    echo "Error: Audacity executable not found." >&2
    echo "Please set AUDACITY_BIN or install Audacity in ~/AppImages/ or system PATH." >&2
    exit 1
fi

# 2. Check for optional --project flag
if [ "${1:-}" = "--project" ] || [ "${1:-}" = "-p" ]; then
    PROJECT="$(ls -1 *.aup4 2>/dev/null | head -n 1 || true)"
    if [ -n "$PROJECT" ]; then
        echo "Opening Audacity project: $PROJECT"
        exec "$AUDACITY" "$PROJECT"
    else
        echo "No .aup4 project found in $SCRIPT_DIR, falling back to audio tracks..."
    fi
fi

# 3. Collect audio tracks in order (00_full_song.wav, 01_..., etc.)
TRACKS=()
while IFS= read -r file; do
    [ -n "$file" ] && TRACKS+=("$file")
done < <(find . -maxdepth 1 -name "0[0-9]_*.wav" | sort)

if [ ${#TRACKS[@]} -eq 0 ]; then
    while IFS= read -r file; do
        [ -n "$file" ] && TRACKS+=("$file")
    done < <(find . -maxdepth 1 -name "*.wav" | sort)
fi

if [ ${#TRACKS[@]} -eq 0 ]; then
    echo "Error: No audio tracks found in $SCRIPT_DIR" >&2
    exit 1
fi

echo "========================================================"
echo "Launching Audacity with ${#TRACKS[@]} track(s) in order:"
for idx in "${!TRACKS[@]}"; do
    printf "  [%d] %s\n" "$((idx + 1))" "${TRACKS[$idx]#./}"
done
echo "========================================================"

exec "$AUDACITY" "${TRACKS[@]}"
