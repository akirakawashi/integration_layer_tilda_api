class NextcloudBaseUrlNotConfiguredError(Exception):
    def __init__(self) -> None:
        super().__init__("Не задан адрес Nextcloud.")


class NextcloudUsernameNotConfiguredError(Exception):
    def __init__(self) -> None:
        super().__init__("Не задан пользователь Nextcloud.")


class NextcloudAppPasswordNotConfiguredError(Exception):
    def __init__(self) -> None:
        super().__init__("Не задан app password для Nextcloud.")


class NextcloudAuthenticationFailedError(Exception):
    def __init__(self) -> None:
        super().__init__("Не удалось пройти аутентификацию в Nextcloud.")


class NextcloudDirectoryCreateFailedError(Exception):
    def __init__(self, status_code: int | None = None) -> None:
        message = "Не удалось создать директорию в Nextcloud."
        if status_code is not None:
            message = f"{message} HTTP {status_code}."
        super().__init__(message)


class NextcloudUploadFailedError(Exception):
    def __init__(self, status_code: int | None = None) -> None:
        message = "Не удалось загрузить файл в Nextcloud."
        if status_code is not None:
            message = f"{message} HTTP {status_code}."
        super().__init__(message)
