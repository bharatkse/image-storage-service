#!/usr/bin/env bash
set -euo pipefail

#####################################
# image-stream dependency setup
# Uses pyenv for Python management
#####################################

PYTHON_VERSION="3.10.14"

SKIP_PYTHON=false
SKIP_DOCKER=false
CI_MODE=false

for arg in "$@"; do
  case "$arg" in
    --skip-python) SKIP_PYTHON=true ;;
    --skip-docker) SKIP_DOCKER=true ;;
  esac
done

if [ "${CI:-false}" = "true" ]; then
  CI_MODE=true
fi

log()  { echo "▶ $1"; }
warn() { echo "⚠ $1"; }

#####################################
# OS Detection (Ubuntu / Debian)
#####################################
check_os() {
  if ! command -v lsb_release >/dev/null 2>&1; then
    warn "Unsupported OS (lsb_release not found)"
    exit 1
  fi

  local os_id
  os_id="$(lsb_release -is)"

  if [[ "$os_id" != "Ubuntu" && "$os_id" != "Debian" ]]; then
    warn "Unsupported OS: $os_id"
    exit 1
  fi
}

#####################################
# Install system deps for pyenv (Python 3.10)
#####################################
install_pyenv_deps() {
  $CI_MODE && return

  local required_packages=(
    build-essential
    curl
    git
    make

    libssl-dev
    zlib1g-dev
    libbz2-dev
    libreadline-dev
    libsqlite3-dev
    libffi-dev
    liblzma-dev
    libncurses-dev
    libgdbm-dev
    libnss3-dev
    libdb-dev
    uuid-dev

    llvm
    xz-utils
    tk-dev
  )

  local missing_packages=()

  for pkg in "${required_packages[@]}"; do
    if ! dpkg -s "$pkg" >/dev/null 2>&1; then
      missing_packages+=("$pkg")
    fi
  done

  if [ "${#missing_packages[@]}" -eq 0 ]; then
    log "All pyenv system dependencies already installed"
    return
  fi

  log "Installing pyenv system dependencies"
  log "Missing packages: ${missing_packages[*]}"

  sudo apt update
  sudo apt install -y "${missing_packages[@]}"
}

#####################################
# Install pyenv
#####################################
install_pyenv() {
  if command -v pyenv >/dev/null 2>&1; then
    log "pyenv already installed"
    return
  fi

  $CI_MODE && { warn "pyenv install skipped in CI"; return; }

  log "Installing pyenv"
  curl -fsSL https://pyenv.run | bash

  export PYENV_ROOT="$HOME/.pyenv"
  export PATH="$PYENV_ROOT/bin:$PATH"

  if ! grep -q "pyenv init" "$HOME/.bashrc" 2>/dev/null; then
    cat <<'EOF' >> "$HOME/.bashrc"
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
EOF
  fi

  eval "$(pyenv init -)"
}

#####################################
# Install Python via pyenv
#####################################
install_python() {
  $SKIP_PYTHON && { log "Skipping Python setup"; return; }

  if ! command -v pyenv >/dev/null 2>&1; then
    warn "pyenv not available"
    exit 1
  fi

  if pyenv versions --bare | grep -qx "$PYTHON_VERSION"; then
    log "Python $PYTHON_VERSION already installed"
  else
    log "Installing Python $PYTHON_VERSION via pyenv"
    pyenv install "$PYTHON_VERSION"
  fi

  if [ -f .python-version ] && grep -qx "$PYTHON_VERSION" .python-version; then
    log "Python $PYTHON_VERSION already set locally"
  else
    log "Setting Python $PYTHON_VERSION as local version"
    pyenv local "$PYTHON_VERSION"
  fi
}

#####################################
# Install Docker + Compose
#####################################
install_docker() {
  $SKIP_DOCKER && { log "Skipping Docker install"; return; }

  if command -v docker >/dev/null 2>&1; then
    log "Docker already installed"
    return
  fi

  $CI_MODE && { warn "Docker install skipped in CI"; return; }

  log "Installing Docker"

  sudo apt update
  sudo apt install -y ca-certificates curl gnupg

  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

  local codename
  codename="$(lsb_release -cs)"

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $codename stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

  sudo apt update
  sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  sudo usermod -aG docker "$USER"

  warn "Log out or run 'newgrp docker' to apply Docker group changes"
}

#####################################
# Install AWS CLI v2
#####################################
install_aws_cli() {
  if command -v aws >/dev/null 2>&1; then
    log "AWS CLI already installed ($(aws --version 2>&1))"
    return
  fi

  $CI_MODE && { warn "AWS CLI install skipped in CI"; return; }

  log "Installing AWS CLI v2"

  local tmp_dir
  tmp_dir="$(mktemp -d)"

  curl -fsSL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip \
    -o "$tmp_dir/awscliv2.zip"

  unzip -q "$tmp_dir/awscliv2.zip" -d "$tmp_dir"
  sudo "$tmp_dir/aws/install"

  rm -rf "$tmp_dir"

  command -v aws >/dev/null 2>&1 || {
    warn "AWS CLI installation failed"
    exit 1
  }
}

#####################################
# Install Poetry (pyenv + Python 3.10 safe)
#####################################
install_poetry() {
  # Ensure pyenv is active and using correct Python
  if command -v pyenv >/dev/null 2>&1; then
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
  fi

  # Ensure we are using the pyenv-selected python
  local python_bin
  python_bin="$(pyenv which python)"

  if "$python_bin" -m poetry --version >/dev/null 2>&1; then
    log "Poetry already installed ($("$python_bin" -m poetry --version))"
    return
  fi

  log "Installing Poetry for Python $PYTHON_VERSION"

  "$python_bin" -m pip install --upgrade pip
  "$python_bin" -m pip install poetry

  python -m pip install --upgrade poetry poetry-plugin-export

  # Rebuild pyenv shims so `poetry` becomes available
  pyenv rehash

  poetry config virtualenvs.create true
  poetry config virtualenvs.in-project true

  # Final sanity check
  if ! command -v poetry >/dev/null 2>&1; then
    warn "Poetry installation failed for Python $PYTHON_VERSION"
    exit 1
  fi

  log "Poetry installed successfully ($(poetry --version))"
}


#####################################
# Python dependencies
#####################################
install_dependencies() {
  if [ ! -f pyproject.toml ]; then
    warn "pyproject.toml not found — skipping dependency install"
    return
  fi

  log "Installing / verifying Python dependencies"
  poetry install --no-interaction
}

#####################################
# pre-commit
#####################################
setup_precommit() {
  if [ ! -f .pre-commit-config.yaml ]; then
    warn "No pre-commit config — skipping"
    return
  fi

  if [ -f .git/hooks/pre-commit ]; then
    log "Pre-commit hooks already installed"
    return
  fi

  log "Installing pre-commit hooks"
  poetry run pre-commit install
}

#####################################
# Main
#####################################
main() {
  log "Setting up image-stream development environment"

  check_os
  install_pyenv_deps
  install_pyenv
  install_python
  install_docker
  install_aws_cli
  install_poetry
  install_dependencies
  setup_precommit

  log "Setup complete"
}

main "$@"
