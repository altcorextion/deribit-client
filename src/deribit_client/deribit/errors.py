class DeribitError(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"Deribit error {code}: {message}")
        self.code = code
        self.message = message