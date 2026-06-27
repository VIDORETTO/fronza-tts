from app.schemas.tts import TTSRequest
from app.schemas.usage import UsageEstimate


class UsageEstimator:
    def estimate(self, request: TTSRequest) -> UsageEstimate:
        chars = len(request.text)
        return UsageEstimate(
            provider_id=request.provider_id or "unknown",
            unit="characters",
            estimated_amount=float(chars),
            confidence="high",
            notes=f"Direct character count: {chars}",
        )
