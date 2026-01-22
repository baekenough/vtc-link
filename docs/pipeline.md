# 파이프라인

단계: fetch/receive -> normalize -> backend send -> response -> postprocess

단일 병원 기준 파이프라인

postprocess는 전체 파이프라인 성공 이후에만 실행하며 실패 시 3회 재시도

## 후처리 설정
- 설정 키: postprocess
- 모드: update_flag, insert_log

## 응답 전처리
- 백엔드 응답 필드를 클라이언트 응답 규격으로 정규화
- screened_date는 YYYYMMDD HH:MM:SS로 변환
- 점수 필드는 정수로 변환, 실패 시 0
