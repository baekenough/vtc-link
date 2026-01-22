# postprocess

후처리는 파이프라인 성공 후 병원 시스템에 상태를 반영하는 단계

## update_flag
- 특정 테이블의 플래그 컬럼을 업데이트
- 설정: table, key_column, key_value, flag_column, flag_value

## insert_log
- 지정 테이블에 로그 레코드를 삽입
- 설정: table, columns, values
