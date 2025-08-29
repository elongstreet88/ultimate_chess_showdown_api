.PHONY: all \
        brew \
        python-venv-setup \
        redis \
        vscode-shell-check \
        generate-env \
		scan-git-for-secrets

all: \
        brew \
        python-venv-setup \
        vscode-shell-check \
        generate-env

# Homebrew
brew:
	@if ! command -v brew >/dev/null 2>&1; then \
		echo "🚀 Installing Homebrew..."; \
		/bin/bash -c "$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; \
	else \
		echo "✅ Homebrew is already installed."; \
	fi

# Python + pyenv + venv (pip install output hidden)
python-venv-setup:
	@command -v pyenv >/dev/null 2>&1 || { \
		echo "⚠️ pyenv is not installed. Installing with Homebrew..."; \
		command -v brew >/dev/null 2>&1 || { \
			echo "❌ Homebrew is not installed. Please install Homebrew first."; \
			exit 1; \
		}; \
		brew update && brew install pyenv; \
		echo "✅ pyenv installed."; \
	}

	@if [ -f ".python-version" ]; then \
		PYTHON_VERSION=$$(cat .python-version); \
	elif [ -f ".tool-versions" ]; then \
		PYTHON_VERSION=$$(grep python .tool-versions | awk '{ print $$2 }'); \
	else \
		echo "❌ No .python-version or .tool-versions file found."; \
		exit 1; \
	fi; \
	echo "✅ Using Python version $$PYTHON_VERSION"; \
	if ! pyenv versions --bare | grep -qx "$$PYTHON_VERSION"; then \
		echo "⬇️  Installing missing Python version $$PYTHON_VERSION with pyenv..."; \
		if ! pyenv install -s "$$PYTHON_VERSION"; then \
			echo "❌ pyenv could not install Python $$PYTHON_VERSION. It may not be available."; \
			echo "🔧 Try updating pyenv with: brew update && brew upgrade pyenv"; \
			echo "🔍 See available versions with: pyenv install --list"; \
			exit 1; \
		fi; \
	fi; \
	pyenv local "$$PYTHON_VERSION"; \
	export PYENV_VERSION=$$PYTHON_VERSION; \
	if [ ! -d ".venv" ]; then \
		echo "📦 Creating virtual environment with Python $$PYTHON_VERSION..."; \
		pyenv exec python -m venv .venv; \
	else \
		echo "✅ Virtual environment (.venv) already exists."; \
	fi; \
	. .venv/bin/activate && \
		echo "⬆️  Upgrading pip and installing dependencies..." && \
		pip install --upgrade pip --trusted-host pypi.org --trusted-host files.pythonhosted.org > /dev/null 2>&1 && \
		pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org > /dev/null 2>&1


vscode-shell-check:
	@SETTINGS_PATH="$$HOME/Library/Application Support/Code/User/settings.json"; \
	if [ ! -f "$$SETTINGS_PATH" ]; then \
		echo "⚠️  VS Code settings.json not found. Is VS Code installed and run at least once?"; \
		exit 1; \
	fi; \
	CURRENT=$$(jq -r '.["terminal.integrated.defaultProfile.osx"] // empty' "$$SETTINGS_PATH"); \
	if [ "$$CURRENT" = "zsh" ]; then \
		echo "✅ VS Code default terminal is already set to zsh."; \
	else \
		if [ -z "$$CURRENT" ]; then \
			echo "❌ VS Code default terminal is not set."; \
		else \
			echo "❌ VS Code default terminal is set to: $$CURRENT"; \
		fi; \
		echo "🔧 Updating default terminal to zsh..."; \
		tmpfile=$$(mktemp); \
		jq '. + {"terminal.integrated.defaultProfile.osx": "zsh"}' "$$SETTINGS_PATH" > $$tmpfile && mv $$tmpfile "$$SETTINGS_PATH"; \
		echo "✅ Updated VS Code default terminal to zsh.\n⚠️ YOU MUST RESTART VS Code (ensure it's completely closed, including background processes).⚠️"; \
	fi

generate-env:
	@echo "⚙️  Create .env encrypted file from dev keyvault secrets"; \
	if ! python ./tools/scripts/encrypt.py encrypt_secrets_to_env; then \
		echo "❌  Failed to create .env file from Key Vault secrets."; \
		echo " This sometimes happens if VSCode's Python interpreter is not set to the virtualenv."; \
		echo " To fix, run this:"; \
		echo "   cmd+shift+p -> Python: Clear Workspace Interpreter Setting"; \
		echo " Then, restart VSCode and run this command again."; \
		exit 1; \
	fi

scan-git-for-secrets:
	@echo "🔍 Scanning for credentials in .env file"; \
	python3 ./tools/scripts/scan_git_for_secrets.py
