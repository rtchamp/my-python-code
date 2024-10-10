.PHONY: venv clean install

venv:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	echo '#!/bin/bash\nsource .venv/bin/activate' > activate.sh
	chmod +x activate.sh
	$(MAKE) install

install: requirements.txt
	.venv/bin/pip install -r requirements.txt

clean:
	rm -rf .venv activate.sh
	rm -f test.db  # 테스트 데이터베이스 파일 삭제

requirements.txt:
	@echo "requirements.txt 파일이 없습니다. 파일을 생성하고 필요한 패키지를 추가해주세요."
	@exit 1
