class StorageHostNotConfiguredError(Exception):
    def __init__(self) -> None:
        super().__init__("Не задан хост файлового хранилища.")


class StorageUsernameNotConfiguredError(Exception):
    def __init__(self) -> None:
        super().__init__("Не задан пользователь файлового хранилища.")


class StorageCredentialsNotConfiguredError(Exception):
    def __init__(self) -> None:
        super().__init__("Не задан пароль или путь к приватному ключу файлового хранилища.")


class StorageLibraryNotInstalledError(Exception):
    def __init__(self) -> None:
        super().__init__("Библиотека paramiko не установлена. Выполните poetry install.")


class StoragePrivateKeyNotFoundError(Exception):
    def __init__(self, private_key_path: str) -> None:
        super().__init__(f"Не найден приватный ключ файлового хранилища: {private_key_path}")


class StorageAuthenticationFailedError(Exception):
    def __init__(self) -> None:
        super().__init__("Не удалось пройти аутентификацию в файловом хранилище.")


class StorageUploadFailedError(Exception):
    def __init__(self) -> None:
        super().__init__("Не удалось загрузить файл в файловое хранилище.")
