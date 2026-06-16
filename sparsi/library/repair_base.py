from typing import Optional

class ErrRepairable(Exception):
    """Exception raised by operators to request an AI-driven repair of their input."""
    def __init__(self, prompt: str, cause: Optional[Exception] = None):
        self.prompt = prompt
        self.cause = cause
        super().__init__(prompt)
