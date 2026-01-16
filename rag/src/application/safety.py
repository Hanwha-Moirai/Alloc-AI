class SafetyError(ValueError):
    pass


class DefaultSafetyPolicy:
    def ensure_safe(self, prompt: str) -> None:
        if not prompt.strip():
            raise SafetyError("Empty prompt is not allowed.")
