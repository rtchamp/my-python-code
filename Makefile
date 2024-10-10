.PHONY: commit-and-push

# 커밋 메시지를 입력받기 위한 변수
MESSAGE ?= "자동 커밋: 모든 변경사항"

commit-and-push:
	@echo "현재 Git 상태 확인 중..."
	@git status

	@echo "\n변경된 파일 추가 중..."
	@git add .

	@echo "\n변경사항 커밋 중..."
	@git commit -m "모든 변경사항 커밋"

	@echo "\n원격 저장소로 푸시 중..."
	@git push origin main

	@echo "\n완료: 모든 변경사항이 커밋되고 푸시되었습니다."

help:
	@echo "사용법:"
	@echo "  make commit-and-push [MESSAGE=\"커밋 메시지\"]"
	@echo "\n기본 커밋 메시지: \"자동 커밋: 모든 변경사항\""
	@echo "커스텀 메시지를 사용하려면: make commit-and-push MESSAGE=\"여기에 메시지 입력\""
