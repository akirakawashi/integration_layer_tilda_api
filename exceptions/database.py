class SessionMakerNotInitializedError(Exception):
    def __init__(self) -> None:
        super().__init__("Фабрика сессий базы данных не инициализирована.")


class DatabaseEngineNotInitializedError(Exception):
    def __init__(self) -> None:
        super().__init__("Движок базы данных не инициализирован.")
