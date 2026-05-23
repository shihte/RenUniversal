# ============================================================
# RenUniversal Project Makefile — Dynamic Self-Healing Build System
# ============================================================
.PHONY: help check-env setup run start stop restart status test clean doctor

PROJECT_ROOT := $(shell pwd)
PID_FILE     := $(PROJECT_ROOT)/.agent.pid
LOG_FILE     := $(PROJECT_ROOT)/agent.log
VENV_DIR     := $(PROJECT_ROOT)/.venv
VENV_PYTHON  := $(VENV_DIR)/bin/python
VENV_PIP     := $(VENV_DIR)/bin/pip
SERVER_SCRIPT:= $(PROJECT_ROOT)/backend/stream_server.py
REQUIREMENTS := $(PROJECT_ROOT)/backend/requirements.txt
PORT         := 8080
PORT_HTTPS   := 8443

# --- Python 版本掃描（支援 Apple Silicon / Intel / Linux）---
PYTHON_CANDIDATES := \
	/opt/homebrew/opt/python@3.10/bin/python3 \
	/opt/homebrew/opt/python@3.11/bin/python3 \
	/opt/homebrew/opt/python@3.9/bin/python3  \
	/opt/homebrew/opt/python@3.12/bin/python3 \
	/usr/local/opt/python@3.10/bin/python3    \
	/usr/local/opt/python@3.11/bin/python3    \
	/usr/local/opt/python@3.9/bin/python3     \
	python3.12 python3.11 python3.10 python3.9 python3 python

COMPATIBLE_PYTHON := $(shell \
	for py in $(PYTHON_CANDIDATES); do \
		if command -v $$py >/dev/null 2>&1; then \
			VER=$$($$py -c 'import sys; v=sys.version_info; print(f"{v.major}.{v.minor}")' 2>/dev/null); \
			MAJOR=$$(echo $$VER | cut -d. -f1); \
			MINOR=$$(echo $$VER | cut -d. -f2); \
			if [ "$$MAJOR" = "3" ] && [ "$$MINOR" -ge 9 ] && [ "$$MINOR" -le 12 ] 2>/dev/null; then \
				echo $$py; break; \
			fi; \
		fi; \
	done)

# ============================================================
# HELP
# ============================================================
help:
	@echo ""
	@echo "  ╔══════════════════════════════════════╗"
	@echo "  ║      RenUniversal Agent — 指令說明           ║"
	@echo "  ╚══════════════════════════════════════╝"
	@echo ""
	@echo "  make doctor   — 診斷系統環境並嘗試自動修復"
	@echo "  make setup    — 初始化 Python 虛擬環境與依賴"
	@echo "  make start    — 在背景啟動 Agent 伺服器"
	@echo "  make stop     — 停止所有 Agent 相關進程"
	@echo "  make restart  — 重啟 Agent 伺服器"
	@echo "  make status   — 顯示目前運行狀態"
	@echo "  make run      — 前景執行（可見日誌，Ctrl+C 停止）"
	@echo "  make test     — 執行架構驗證測試"
	@echo "  make clean    — 清除快取、日誌與 PID 檔案"
	@echo "  make install PATH=<dir> — 安裝 .renuniversal 外掛套件"
	@echo "  make build --name <N> --skills <S> --events <E> --apps <A> — 打包自訂外掛"
	@echo ""

# ============================================================
# DOCTOR — 環境診斷與自動修補
# ============================================================
doctor:
	@echo "=== RenUniversal 環境診斷 (Doctor) ==="
	@echo ""
	@echo "▶ 1. 偵測作業系統..."
	@OS=$$(uname -s); \
	ARCH=$$(uname -m); \
	echo "   OS: $$OS / Arch: $$ARCH"
	@echo ""

	@echo "▶ 2. 偵測 Python..."
	@if [ -z "$(COMPATIBLE_PYTHON)" ]; then \
		echo "   ✗ 找不到相容 Python (3.9–3.12)"; \
		$(MAKE) _install_python; \
	else \
		echo "   ✓ 找到: $(COMPATIBLE_PYTHON) ($$($(COMPATIBLE_PYTHON) --version))"; \
	fi
	@echo ""

	@echo "▶ 3. 檢查虛擬環境..."
	@if [ ! -f "$(VENV_PYTHON)" ]; then \
		echo "   ✗ 虛擬環境不存在，嘗試重建..."; \
		$(MAKE) _create_venv; \
	else \
		PYVER=$$($(VENV_PYTHON) --version 2>&1); \
		echo "   ✓ 虛擬環境 Python: $$PYVER"; \
	fi
	@echo ""

	@echo "▶ 4. 檢查關鍵套件..."
	@if [ -f "$(VENV_PYTHON)" ]; then \
		for pkg in flask flask_cors cv2 mediapipe numpy loguru pydantic; do \
			if $(VENV_PYTHON) -c "import $$pkg" 2>/dev/null; then \
				echo "   ✓ $$pkg"; \
			else \
				echo "   ✗ $$pkg 缺失，嘗試安裝..."; \
				$(VENV_PIP) install -r $(REQUIREMENTS) --quiet || true; \
				break; \
			fi; \
		done; \
	fi
	@echo ""

	@echo "▶ 5. 檢查伺服器腳本..."
	@if [ -f "$(SERVER_SCRIPT)" ]; then \
		echo "   ✓ $(SERVER_SCRIPT)"; \
	else \
		echo "   ✗ 找不到 $(SERVER_SCRIPT)！請確認專案結構"; \
	fi
	@echo ""

	@echo "▶ 6. 檢查 Port 佔用..."
	@for port in $(PORT) $(PORT_HTTPS); do \
		PIDS=$$(lsof -t -i :$$port 2>/dev/null || true); \
		if [ -n "$$PIDS" ]; then \
			echo "   ⚠ Port $$port 已被佔用 (PID: $$PIDS)"; \
		else \
			echo "   ✓ Port $$port 空閒"; \
		fi; \
	done
	@echo ""
	@echo "=== 診斷完成 ==="

# ============================================================
# 內部修補指令（由其他指令呼叫，不直接使用）
# ============================================================
_install_python:
	@OS=$$(uname -s); \
	if [ "$$OS" = "Darwin" ]; then \
		if command -v brew >/dev/null 2>&1; then \
			echo "   → Homebrew 已安裝，正在安裝 Python 3.10..."; \
			brew install python@3.10 && echo "   ✓ Python 3.10 安裝完成！請重新執行 make setup" && exit 1; \
		else \
			echo "   → Homebrew 未安裝，嘗試安裝 Homebrew..."; \
			RESP=n; \
			if [ -t 0 ]; then read -p "   是否安裝 Homebrew？(y/N) " RESP; fi; \
			if [ "$$RESP" = "y" ] || [ "$$RESP" = "Y" ]; then \
				/bin/bash -c "$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" && \
				brew install python@3.10 && echo "   ✓ 完成！請重新執行 make setup" && exit 1; \
			else \
				echo "   請手動安裝 Python 3.10: https://www.python.org/downloads/"; \
				exit 1; \
			fi; \
		fi; \
	elif [ "$$OS" = "Linux" ]; then \
		if command -v apt-get >/dev/null 2>&1; then \
			echo "   → 偵測到 Debian/Ubuntu，安裝 Python 3.10..."; \
			sudo apt-get update -qq && sudo apt-get install -y python3.10 python3.10-venv python3-pip || exit 1; \
		elif command -v dnf >/dev/null 2>&1; then \
			echo "   → 偵測到 Fedora/RHEL，安裝 Python 3.10..."; \
			sudo dnf install -y python3.10 || exit 1; \
		elif command -v yum >/dev/null 2>&1; then \
			echo "   → 偵測到 CentOS，安裝 Python 3.10..."; \
			sudo yum install -y python310 python310-pip || exit 1; \
		elif command -v pacman >/dev/null 2>&1; then \
			echo "   → 偵測到 Arch Linux，安裝 Python..."; \
			sudo pacman -S --noconfirm python || exit 1; \
		else \
			echo "   ✗ 無法自動安裝，請手動安裝 Python 3.9-3.12"; \
			exit 1; \
		fi; \
	else \
		echo "   ✗ 不支援的作業系統: $$OS。請手動安裝 Python 3.9-3.12"; \
		exit 1; \
	fi

_create_venv:
	@if [ -z "$(COMPATIBLE_PYTHON)" ]; then \
		echo "   ✗ 沒有可用的 Python，請先執行 make doctor"; \
		exit 1; \
	fi
	@# 若舊 venv 損壞則刪除重建
	@if [ -d "$(VENV_DIR)" ] && [ ! -f "$(VENV_PYTHON)" ]; then \
		echo "   ⚠ 發現損壞的虛擬環境，刪除重建..."; \
		rm -rf "$(VENV_DIR)"; \
	fi
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "   → 建立虛擬環境..."; \
		$(COMPATIBLE_PYTHON) -m venv "$(VENV_DIR)" || { \
			echo "   ✗ venv 建立失敗，嘗試安裝 python3-venv..."; \
			OS=$$(uname -s); \
			if [ "$$OS" = "Linux" ] && command -v apt-get >/dev/null 2>&1; then \
				sudo apt-get install -y python3-venv python3-pip && \
				$(COMPATIBLE_PYTHON) -m venv "$(VENV_DIR)"; \
			else \
				exit 1; \
			fi; \
		}; \
		echo "   ✓ 虛擬環境建立完成"; \
	fi

_install_deps:
	@echo "→ 升級 pip..."
	@$(VENV_PYTHON) -m pip install --upgrade pip --quiet || true
	@echo "→ 開始安裝核心套件依賴..."
	@while IFS= read -r pkg || [ -n "$$pkg" ]; do \
		[ -z "$$pkg" ] && continue; \
		[[ "$$pkg" =~ ^# ]] && continue; \
		echo "   ⏳ 正在安裝: $$pkg ..."; \
		$(VENV_PIP) install "$$pkg" --quiet || echo "   ⚠ 安裝失敗: $$pkg"; \
	done < "$(REQUIREMENTS)"
	@echo "   ✓ 所有套件檢查與安裝完畢！"

# ============================================================
# SETUP
# ============================================================
setup:
	@echo "=== 初始化 RenUniversal Agent 環境 ==="
	@if [ -z "$(COMPATIBLE_PYTHON)" ]; then \
		echo "✗ 找不到相容的 Python (3.9–3.12)，嘗試自動修復..."; \
		$(MAKE) _install_python; \
	fi
	@echo "✓ 使用 Python: $(COMPATIBLE_PYTHON) ($$($(COMPATIBLE_PYTHON) --version))"
	@$(MAKE) _create_venv
	@$(MAKE) _install_deps
	@mkdir -p skills events
	@mkdir -p backend/services
	@echo ""
	@echo "=== 設定完成！執行 'make start' 啟動伺服器 ==="

# ============================================================
# RUN (前景)
# ============================================================
run:
	@if [ ! -f "$(VENV_PYTHON)" ]; then \
		echo "✗ 找不到虛擬環境。執行 'make setup' 初始化。"; exit 1; \
	fi
	@echo "=== 前景啟動 RenUniversal（Ctrl+C 停止）==="
	@PYTHONPATH="$(PROJECT_ROOT):$$PYTHONPATH" $(VENV_PYTHON) "$(SERVER_SCRIPT)"

# ============================================================
# START (背景)
# ============================================================
start:
	@if [ ! -f "$(VENV_PYTHON)" ]; then \
		echo "✗ 找不到虛擬環境。執行 'make setup' 初始化。"; exit 1; \
	fi
	@if [ ! -f "$(SERVER_SCRIPT)" ]; then \
		echo "✗ 找不到伺服器腳本: $(SERVER_SCRIPT)"; exit 1; \
	fi
	@# 若已有進程在跑則阻止重複啟動
	@if [ -f "$(PID_FILE)" ]; then \
		PID=$$(cat "$(PID_FILE)" 2>/dev/null || true); \
		if [ -n "$$PID" ] && kill -0 "$$PID" 2>/dev/null; then \
			echo "Agent 已在運行中 (PID: $$PID)，執行 'make restart' 重啟。"; \
			exit 1; \
		else \
			rm -f "$(PID_FILE)"; \
		fi; \
	fi
	@# 雙重確認端口（避免殭屍進程）
	@STALE=$$(lsof -t -i :$(PORT) 2>/dev/null || true); \
	if [ -n "$$STALE" ]; then \
		echo "⚠ Port $(PORT) 被佔用 (PID: $$STALE)，先清除..."; \
		for p in $$STALE; do kill -9 $$p 2>/dev/null || true; done; \
		sleep 3; \
	fi
	@echo "=== 啟動 RenUniversal Agent 伺服器 ==="
	@PYTHONPATH="$(PROJECT_ROOT):$$PYTHONPATH" \
		nohup $(VENV_PYTHON) "$(SERVER_SCRIPT)" >"$(LOG_FILE)" 2>&1 & \
		echo $$! >"$(PID_FILE)"
	@sleep 3
	@# 驗證啟動成功
	@PID=$$(cat "$(PID_FILE)" 2>/dev/null || true); \
	if [ -n "$$PID" ] && kill -0 "$$PID" 2>/dev/null; then \
		echo "✓ Agent 啟動成功 (PID: $$PID)"; \
		echo "  日誌: $(LOG_FILE)"; \
		echo "  監控: http://localhost:$(PORT)"; \
	else \
		echo "✗ 進程已終止，檢查日誌："; \
		tail -20 "$(LOG_FILE)" 2>/dev/null || true; \
		rm -f "$(PID_FILE)"; \
		exit 1; \
	fi

# ============================================================
# STOP — 三層式確保徹底停止
# ============================================================
stop:
	@echo "=== 停止 RenUniversal Agent 伺服器 ==="
	@KILLED=0; \
	\
	# 層 1: PID 檔案
	if [ -f "$(PID_FILE)" ]; then \
		PID=$$(cat "$(PID_FILE)" 2>/dev/null || true); \
		if [ -n "$$PID" ]; then \
			if kill -0 "$$PID" 2>/dev/null; then \
				echo "  → 終止 PID 檔案進程 $$PID..."; \
				kill "$$PID" 2>/dev/null || true; \
				pkill -f "nokey@localhost.run" 2>/dev/null || true; \
				sleep 3; \
				kill -9 "$$PID" 2>/dev/null || true; \
				KILLED=1; \
			fi; \
		fi; \
		rm -f "$(PID_FILE)"; \
	fi; \
	\
	# 層 2: pgrep 搜尋所有 stream_server.py 進程
	PYPIDS=$$(pgrep -f "stream_server.py" 2>/dev/null || true); \
	if [ -n "$$PYPIDS" ]; then \
		for pid in $$PYPIDS; do \
			echo "  → 終止進程 $$pid (stream_server.py)..."; \
			kill "$$pid" 2>/dev/null || true; \
		done; \
		sleep 3; \
		for pid in $$PYPIDS; do \
			kill -9 "$$pid" 2>/dev/null || true; \
		done; \
		KILLED=1; \
	fi; \
	\
	# 層 3: lsof 端口強制清除
	for port in $(PORT) $(PORT_HTTPS); do \
		PORT_PIDS=$$(lsof -t -i :$$port 2>/dev/null || true); \
		if [ -n "$$PORT_PIDS" ]; then \
			for p in $$PORT_PIDS; do \
				echo "  → 強制終止 Port $$port 進程 $$p..."; \
				kill -9 $$p 2>/dev/null || true; \
			done; \
			KILLED=1; \
		fi; \
	done; \
	\
	rm -f "$(PID_FILE)"; \
	if [ "$$KILLED" = "1" ]; then \
		echo "✓ Agent 已停止"; \
	else \
		echo "ℹ 找不到正在運行的 Agent 進程"; \
	fi

# ============================================================
# RESTART
# ============================================================
restart:
	@$(MAKE) stop
	@sleep 1
	@$(MAKE) start

# ============================================================
# STATUS
# ============================================================
status:
	@echo "=== RenUniversal Agent 狀態 ==="
	@if [ -f "$(PID_FILE)" ]; then \
		PID=$$(cat "$(PID_FILE)" 2>/dev/null || true); \
		if [ -n "$$PID" ] && kill -0 "$$PID" 2>/dev/null; then \
			echo "  ✓ 運行中 (PID: $$PID)"; \
		else \
			echo "  ✗ PID 檔案存在但進程已終止"; \
			rm -f "$(PID_FILE)"; \
		fi; \
	else \
		PYPIDS=$$(pgrep -f "stream_server.py" 2>/dev/null || true); \
		if [ -n "$$PYPIDS" ]; then \
			echo "  ⚠ 進程存在但無 PID 檔案 (PID: $$PYPIDS)"; \
		else \
			echo "  ✗ 未運行"; \
		fi; \
	fi
	@echo "  端口 $(PORT): $$(lsof -t -i :$(PORT) 2>/dev/null && echo 佔用 || echo 空閒)"
	@echo "  端口 $(PORT_HTTPS): $$(lsof -t -i :$(PORT_HTTPS) 2>/dev/null && echo 佔用 || echo 空閒)"

# ============================================================
# TEST
# ============================================================
test:
	@if [ ! -f "$(VENV_PYTHON)" ]; then \
		echo "✗ 找不到虛擬環境。執行 'make setup'。"; exit 1; \
	fi
	@echo "=== 執行架構驗證測試 ==="
	@PYTHONPATH="$(PROJECT_ROOT):$$PYTHONPATH" $(VENV_PYTHON) backend/test_architecture.py

# ============================================================
# CLEAN
# ============================================================
clean:
	@echo "=== 清除暫存檔案 ==="
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -f "$(PID_FILE)"
	@rm -f "$(LOG_FILE)"
	@rm -f preferences.json
	@rm -f backend/core/.status.tmp
	@echo "✓ 清除完成"

# ============================================================
# INSTALL PLUGIN
# ============================================================
install:
	@if [ -z "$(PATH)" ]; then \
		echo "✗ 請提供外掛路徑，例如：make install PATH=./my_plugin"; exit 1; \
	fi
	@if [ ! -f "$(VENV_PYTHON)" ]; then \
		echo "✗ 找不到虛擬環境。執行 'make setup'。"; exit 1; \
	fi
	@$(VENV_PYTHON) tools/installer.py "$(PATH)"

# ============================================================
# BUILD PLUGIN
# ============================================================
build:
	@if [ -z "$(NAME)" ]; then \
		echo "✗ 請提供外掛名稱，例如：make build NAME=MyPlugin SKILLS=skills/lean"; exit 1; \
	fi
	@if [ ! -f "$(VENV_PYTHON)" ]; then \
		echo "✗ 找不到虛擬環境。執行 'make setup'。"; exit 1; \
	fi
	@$(VENV_PYTHON) tools/builder.py --name "$(NAME)" --skills $(SKILLS) --events $(EVENTS) --apps $(APPS)
