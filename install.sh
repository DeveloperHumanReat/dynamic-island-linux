#!/usr/bin/env bash
set -euo pipefail

# Bootstrap: the only system dependency needed by this first prototype is
# Python 3 with Tk. The rest is installed into ~/.local.
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "python3 bulunamadı. Lütfen dağıtımınızın Python 3 paketini kurun."
  exit 1
fi

if ! "$PYTHON" -c 'import tkinter' >/dev/null 2>&1; then
  DISTRO_ID="linux"
  if [[ -r /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    DISTRO_ID="${ID:-linux}"
  fi

  echo "Tkinter eksik; dağıtım bağımlılığı otomatik kuruluyor ($DISTRO_ID)."
  case "$DISTRO_ID" in
    ubuntu|debian|linuxmint|pop|elementary|zorin)
      sudo apt-get update
      sudo apt-get install -y python3-tk
      ;;
    fedora|rhel|centos|rocky|almalinux)
      if command -v dnf >/dev/null 2>&1; then sudo dnf install -y python3-tkinter; else sudo yum install -y tkinter; fi
      ;;
    arch|manjaro|endeavouros|cachyos|garuda|artix)
      sudo pacman -Sy --needed --noconfirm tk
      ;;
    opensuse*|suse)
      sudo zypper --non-interactive install python3-tk
      ;;
    alpine)
      sudo apk add python3-tkinter
      ;;
    void)
      sudo xbps-install -Sy python3-tkinter
      ;;
    *)
      echo "Bu dağıtım otomatik eşleştirilemedi: $DISTRO_ID"
      echo "Paket yöneticinizden Python 3 Tk paketini kurun ve betiği tekrar çalıştırın."
      exit 1
      ;;
  esac
fi

# Wayland backend dependencies. Install them proactively so the user does not
# need to choose individual packages. If a distro has no gtk-layer-shell
# package, the X11 backend remains available and the installer explains why.
DISTRO_ID="linux"
if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  DISTRO_ID="${ID:-linux}"
fi
case "$DISTRO_ID" in
  ubuntu|debian|linuxmint|pop|elementary|zorin)
    sudo apt-get update
    sudo apt-get install -y python3-gi gir1.2-gtk-3.0 gir1.2-gtklayershell-0.1 libgtk-layer-shell0
    ;;
  fedora|rhel|centos|rocky|almalinux)
    if command -v dnf >/dev/null 2>&1; then
      sudo dnf install -y python3-gobject gtk3 gtk-layer-shell
    else
      sudo yum install -y python3-gobject gtk3 gtk-layer-shell
    fi
    ;;
  arch|manjaro|endeavouros|cachyos|garuda|artix)
    sudo pacman -Sy --needed --noconfirm python-gobject gtk3 gtk-layer-shell
    ;;
  opensuse*|suse)
    sudo zypper --non-interactive install python3-gobject gtk3 gtk-layer-shell
    ;;
  alpine)
    sudo apk add py3-gobject3 gtk+3.0 gtk-layer-shell
    ;;
  void)
    sudo xbps-install -Sy python3-gobject gtk+3 gtk-layer-shell
    ;;
  *)
    echo "Wayland paketleri bu dağıtımda otomatik eşleştirilemedi; X11 backend kurulacak."
    ;;
esac

exec "$PYTHON" "$ROOT_DIR/installer.py"
