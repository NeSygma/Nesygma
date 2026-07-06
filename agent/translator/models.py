from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

class PhaseUsage(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)

class TranslatorOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    success: bool
    iterations_used: int = Field(ge=0)
    messages: list[Any]
    usage: PhaseUsage
    definitive_result_text: Optional[str] = None
    solver_payload: Optional[dict[str, Any]] = None
    last_tool_name: Optional[str] = None
    last_tool_args: Optional[dict[str, Any]] = None
    failure_reason: Optional[str] = None

    @model_validator(mode="after")
    def _validate_success_payload(self) -> "TranslatorOutcome":
        if self.success and not self.definitive_result_text:
            raise ValueError("Successful translator outcome requires definitive_result_text.")
        if not self.success and not self.failure_reason:
            raise ValueError("Failed translator outcome requires failure_reason.")
        return self
