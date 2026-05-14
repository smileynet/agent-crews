#!/usr/bin/env bash
# OS-native toast notification
# Usage: notify-toast.sh TITLE MESSAGE
set -euo pipefail

TITLE="${1:?Usage: notify-toast.sh TITLE MESSAGE}"
MSG="${2:-}"

case "${OSTYPE:-}" in
  darwin*)
    osascript -e "display notification \"$MSG\" with title \"$TITLE\"" ;;
  linux*)
    if command -v notify-send &>/dev/null; then
      notify-send "$TITLE" "$MSG"
    else
      echo "[$TITLE] $MSG" >&2
    fi ;;
  msys*|cygwin*|win*)
    powershell -c "New-BurntToastNotification -Text '$TITLE','$MSG'" 2>/dev/null \
      || powershell -c "[void][System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); [System.Windows.Forms.MessageBox]::Show('$MSG','$TITLE')" 2>/dev/null \
      || echo "[$TITLE] $MSG" >&2 ;;
  *)
    echo "[$TITLE] $MSG" >&2 ;;
esac
