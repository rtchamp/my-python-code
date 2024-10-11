CURRENT_DIR := $(shell pwd)
TARGET_DIR := /path/to/target/directory

# 임시 디렉토리 정의
TMP_DIR := tmp_build

# 기본 타겟
.PHONY: all
all: prepare run-target clean

# 임시 디렉토리 준비 및 파일 이동
.PHONY: prepare
prepare:
	@mkdir -p $(TMP_DIR)
	@find . -maxdepth 1 -type f -not -name "makefile" -exec mv {} $(TMP_DIR)/ \;
	@find . -maxdepth 1 -type d -not -name "." -not -name "$(TMP_DIR)" -exec mv {} $(TMP_DIR)/ \;

# 타겟 실행
.PHONY: run-target
run-target:
	@if [ -n "$(MAKECMDGOALS)" ] && [ "$(MAKECMDGOALS)" != "all" ]; then \
		cd $(TMP_DIR) && $(MAKE) $(MAKECMDGO
