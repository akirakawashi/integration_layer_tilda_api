class TildaJobNotFoundError(Exception):
    def __init__(self, job_id: int) -> None:
        super().__init__(f"Задача Tilda с id={job_id} не найдена.")


class TildaJobConflictStateError(Exception):
    def __init__(self, tran_id: str) -> None:
        super().__init__(
            f"Задача Tilda с tran_id={tran_id} не найдена после конфликта вставки."
        )
