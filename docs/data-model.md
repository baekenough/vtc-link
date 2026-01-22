# 데이터 모델

## 캐노니컬 필드
- patient_id (string)
- patient_name (string, optional)
- birthdate (YYYYMMDD)
- age (int, optional)
- sex (M/F)
- ward (string, max 30)
- department (string, max 30)
- SBP, DBP, PR, RR (int)
- BT, SpO2 (float)
- created_at, updated_at (UTC ISO8601)

## 클라이언트 응답 필드
- vital_id (string)
- patient_id (string)
- screened_type (string)
- screened_date (YYYYMMDD HH:MM:SS)
- SEPS, MAES, MORS, NEWS, MEWS (int)
- created_at, updated_at (string)
