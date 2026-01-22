from pydantic import BaseModel, Field


class ClientResponse(BaseModel):
    """클라이언트 응답 모델"""

    vital_id: str = Field(..., description="바이탈 식별자")
    patient_id: str = Field(..., description="환자 식별자")
    screened_type: str = Field(..., description="Screened Type")
    screened_date: str = Field(..., description="Screened Date(YYYYMMDD HH:MM:SS)")
    SEPS: int = Field(..., description="SEPS 점수")
    MAES: int = Field(..., description="MAES 점수")
    MORS: int = Field(..., description="MORS 점수")
    NEWS: int = Field(..., description="NEWS 점수")
    MEWS: int = Field(..., description="MEWS 점수")
    created_at: str = Field(..., description="생성 시각")
    updated_at: str = Field(..., description="수정 시각")
