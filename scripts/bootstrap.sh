#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# image-storage dependency setup
# - pyenv: Python runtime
# - pipx: global tools (Poetry)
# ============================================================================

PYTHON_VERSION="3.10.14"

SKIP_PYTHON=false
SKIP_DOCKER=false
WRITE_PYTHON_VERSION=false
CI_MODE=false

for arg in "$@"; do
  case "$arg" in
    --skip-python) SKIP_PYTHON=true ;;
    --skip-docker) SKIP_DOCKER=true ;;
    --write-python-version) WRITE_PYTHON_VERSION=true ;;
  esac
done

if [ "${CI:-false}" = "true" ]; then
  CI_MODE=true
fi

# Ensure pipx tools always win over pyenv shims
export PATH="$HOME/.local/bin:$PATH"

log()  { echo "▶ $1"; }
warn() { echo "⚠ $1"; }

# ============================================================================
# OS Detection (Ubuntu / Debian)
# ============================================================================
check_os() {
  command -v lsb_release >/dev/null 2>&1 || {
    warn "Unsupported OS (lsb_release not found)"
    exit 1
  }

  local os_id
  os_id="$(lsb_release -is)"

  [[ "$os_id" == "Ubuntu" || "$os_id" == "Debian" ]] || {
    warn "Unsupported OS: $os_id"
    exit 1
  }
}

# ============================================================================
# System dependencies
# ============================================================================
install_system_deps() {
  $CI_MODE && return

  local packages=(
    build-essential curl git make unzip
    libssl-dev zlib1g-dev libbz2-dev libreadline-dev
    libsqlite3-dev libffi-dev liblzma-dev
    libncurses-dev libgdbm-dev libnss3-dev
    libdb-dev uuid-dev llvm xz-utils tk-dev
    pipx
  )

  local missing=()
  for pkg in "${packages[@]}"; do
    dpkg -s "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
  done

  if [ "${#missing[@]}" -eq 0 ]; then
    log "All system dependencies already installed"
    return
  fi

  log "Installing system dependencies: ${missing[*]}"
  sudo apt update
  sudo apt install -y "${missing[@]}"
}

# ============================================================================
# pyenv
# ============================================================================
install_pyenv() {
  command -v pyenv >/dev/null 2>&1 && {
    log "pyenv already installed"
    return
  }

  $CI_MODE && { warn "Skipping pyenv install in CI"; return; }

  log "Installing pyenv"
  curl -fsSL https://pyenv.run | bash

  cat <<'EOF' >> "$HOME/.bashrc"
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
EOF

  export PYENV_ROOT="$HOME/.pyenv"
  export PATH="$PYENV_ROOT/bin:$PATH"
  eval "$(pyenv init -)"
}

# ============================================================================
# Python via pyenv
# ============================================================================
install_python() {
  $SKIP_PYTHON && { log "Skipping Python setup"; return; }

  command -v pyenv >/dev/null 2>&1 || {
    warn "pyenv not available"
    exit 1
  }

  if pyenv versions --bare | grep -qx "$PYTHON_VERSION"; then
    log "Python $PYTHON_VERSION already installed"
  else
    log "Installing Python $PYTHON_VERSION"
    pyenv install "$PYTHON_VERSION"
  fi

  pyenv local "$PYTHON_VERSION"
}

# ============================================================================
# .python-version
# ============================================================================
write_python_version_file() {
  $WRITE_PYTHON_VERSION || return

  if [ -f .python-version ]; then
    if grep -qx "$PYTHON_VERSION" .python-version; then
      log ".python-version already set to $PYTHON_VERSION"
      return
    fi
  fi

  log "Writing .python-version ($PYTHON_VERSION)"
  echo "$PYTHON_VERSION" > .python-version
}

# ============================================================================
# Docker
# ============================================================================
install_docker() {
  $SKIP_DOCKER && { log "Skipping Docker"; return; }

  command -v docker >/dev/null 2>&1 && {
    log "Docker already installed"
    return
  }

  $CI_MODE && { warn "Skipping Docker install in CI"; return; }

  log "Installing Docker"
  sudo apt update
  sudo apt install -y ca-certificates curl gnupg

  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

  sudo apt update
  sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  sudo usermod -aG docker "$USER"

  warn "Log out or run 'newgrp docker' to apply Docker group changes"
}

# ============================================================================
# AWS CLI v2
# ============================================================================
install_aws_cli() {
  command -v aws >/dev/null 2>&1 && {
    log "AWS CLI already installed ($(aws --version 2>&1))"
    return
  }

  $CI_MODE && { warn "Skipping AWS CLI install in CI"; return; }

  log "Installing AWS CLI v2"
  tmp_dir="$(mktemp -d)"

  curl -fsSL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip \
    -o "$tmp_dir/awscliv2.zip"

  unzip -q "$tmp_dir/awscliv2.zip" -d "$tmp_dir"
  sudo "$tmp_dir/aws/install"
  rm -rf "$tmp_dir"
}

# ============================================================================
# Poetry (pipx ONLY)
# ============================================================================
install_poetry() {
  command -v pipx >/dev/null 2>&1 || {
    warn "pipx not available"
    exit 1
  }

  if command -v poetry >/dev/null 2>&1; then
    log "Poetry already installed ($(poetry --version))"
  else
    log "Installing Poetry via pipx"
    pipx install poetry==2.3.1
  fi

  log "Ensuring poetry-plugin-export is available"
  pipx inject poetry poetry-plugin-export

  # Hard guarantee
  poetry export --help >/dev/null 2>&1 || {
    warn "Poetry export command not available"
    exit 1
  }

  poetry config virtualenvs.create true
  poetry config virtualenvs.in-project true
}

# ============================================================================
# Python dependencies
# ============================================================================
install_dependencies() {
  [ -f pyproject.toml ] || {
    warn "pyproject.toml not found — skipping deps"
    return
  }

  log "Installing Python dependencies"
  poetry install --no-interaction
}

# ============================================================================
# pre-commit
# ============================================================================
setup_precommit() {
  [ -f .pre-commit-config.yaml ] || {
    warn "No pre-commit config — skipping"
    return
  }

  [ -f .git/hooks/pre-commit ] && {
    log "Pre-commit already installed"
    return
  }

  log "Installing pre-commit hooks"
  poetry run pre-commit install
}

# ============================================================================
# Main
# ============================================================================
main() {
  log "Setting up image-storage development environment"

  check_os
  install_system_deps
  install_pyenv
  install_python
  write_python_version_file
  install_docker
  install_aws_cli
  install_poetry
  install_dependencies
  setup_precommit

  log "Setup complete"
}

main "$@"
