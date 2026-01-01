#!/usr/bin/env bash
set -euo pipefail

DMG_PATH="${1:-}"

# Auto-find, wenn kein Pfad übergeben wurde
if [[ -z "${DMG_PATH}" ]]; then
  for p in \
    "$HOME/Downloads/Cursor-darwin-universal.dmg" \
    "$PWD/Cursor-darwin-universal.dmg" \
    "$HOME/Desktop/Cursor-darwin-universal.dmg"
  do
    if [[ -f "$p" ]]; then
      DMG_PATH="$p"
      break
    fi
  done
fi

if [[ -z "${DMG_PATH}" || ! -f "${DMG_PATH}" ]]; then
  echo "ERROR: Cursor-darwin-universal.dmg nicht gefunden."
  echo "Nutze: ./verify_cursor_dmg.sh /voller/pfad/zur/Cursor-darwin-universal.dmg"
  exit 1
fi

echo "DMG: ${DMG_PATH}"
echo

echo "== (1) SHA-256 Hash =="
shasum -a 256 "${DMG_PATH}"
echo

echo "== (2) DMG Strukturprüfung (hdiutil verify) =="
hdiutil verify "${DMG_PATH}"
echo

echo "== (3) Read-only mount =="
MOUNT_INFO="$(hdiutil attach -nobrowse -readonly "${DMG_PATH}")"
echo "${MOUNT_INFO}"
MOUNT_POINT="$(echo "${MOUNT_INFO}" | grep "/Volumes/" | tail -n 1 | awk -F'\t' '{print $NF}')"

if [[ -z "${MOUNT_POINT}" || ! -d "${MOUNT_POINT}" ]]; then
  echo "ERROR: Mount-Point nicht erkannt."
  exit 1
fi

APP_PATH="${MOUNT_POINT}/Cursor.app"
if [[ ! -d "${APP_PATH}" ]]; then
  # Fallback: App innerhalb des Volumes suchen
  APP_PATH="$(find "${MOUNT_POINT}" -maxdepth 3 -name "*.app" -print | head -n 1 || true)"
fi

if [[ -z "${APP_PATH}" || ! -d "${APP_PATH}" ]]; then
  echo "ERROR: Keine .app im gemounteten Volume gefunden."
  echo "Volume: ${MOUNT_POINT}"
  hdiutil detach "${MOUNT_POINT}" || true
  exit 1
fi

echo
echo "App: ${APP_PATH}"
echo

echo "== (4) Gatekeeper Assessment (spctl) =="
spctl -a -vv --type execute "${APP_PATH}" || true
echo

echo "== (5) Code Signatur Details (codesign -dv) =="
codesign -dv --verbose=4 "${APP_PATH}" 2>&1 || true
echo

echo "== (6) Code Signatur Verify (deep/strict) =="
codesign --verify --deep --strict --verbose=2 "${APP_PATH}" 2>&1 || true
echo

echo "== (7) Detach Volume =="
hdiutil detach "${MOUNT_POINT}" || true
echo "Done."
