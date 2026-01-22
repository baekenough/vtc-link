from pydantic import BaseModel, Field


class Patient(BaseModel):
    """환자 식별 정보"""

    patient_id: str = Field(..., description="환자 식별자")
    patient_name: str | None = Field(default=None, description="환자 이름")
    birthdate: str = Field(..., description="생년월일(YYYYMMDD)")
    age: int | None = Field(default=None, description="나이")
    sex: str = Field(..., description="성별 코드(M/F)")
    ward: str | None = Field(default=None, max_length=30, description="병동")
    department: str | None = Field(default=None, max_length=30, description="진료과")


class Vitals(BaseModel):
    """생체신호 측정값"""

    SBP: int = Field(..., description="수축기 혈압")
    DBP: int = Field(..., description="이완기 혈압")
    PR: int = Field(..., description="맥박수")
    RR: int = Field(..., description="호흡수")
    BT: float = Field(..., description="체온(섭씨)")
    SpO2: float = Field(..., description="산소포화도")


class Timestamps(BaseModel):
    """레코드 타임스탬프 메타데이터"""

    created_at: str = Field(..., description="생성 시각(UTC ISO8601)")
    updated_at: str = Field(..., description="수정 시각(UTC ISO8601)")


class CanonicalPayload(BaseModel):
    """백엔드로 전달되는 캐노니컬 페이로드"""

    patient: Patient
    vitals: Vitals
    timestamps: Timestamps
