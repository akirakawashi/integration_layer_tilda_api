# integration_layer_tilda_api

Сервис для приёма webhook'ов из Tilda, постановки фоновых задач в PostgreSQL, скачивания архивов и сохранения их в Nextcloud.

## Что Делает Сервис

Проект состоит из двух runtime-процессов:

- `api`: принимает webhook-запросы от Tilda и записывает задачи в PostgreSQL
- `worker`: забирает задачи из очереди, скачивает файл, валидирует его и загружает в Nextcloud

Для хранения состояния задач используется PostgreSQL, для миграций базы данных — Alembic.

## Основной Сценарий Работы

1. Tilda отправляет webhook на `POST /api/v1/webhooks/tilda`
2. API валидирует payload, при необходимости проверяет webhook API key и сохраняет задачу в PostgreSQL со статусом `queued`
3. Worker забирает следующую доступную задачу
4. Worker получает прямую ссылку на архив из Selectel, скачивает файл, валидирует архив и загружает его в Nextcloud
5. Статус задачи обновляется на `done`, `retry_wait` или `failed`

## Статусы Задач

- `queued`: новая задача, ожидающая обработки
- `processing`: задача взята worker'ом в работу
- `retry_wait`: временная ошибка, задача будет обработана повторно после `next_retry_at`
- `done`: файл успешно скачан и загружен в Nextcloud
- `failed`: задача завершилась необратимой ошибкой или исчерпала лимит попыток

## Требования

- Python `3.12`
- Poetry
- Docker and Docker Compose

## Конфигурация

Конфигурация загружается из `.env`.

Основные группы переменных:

- `POSTGRES_*`: подключение к базе данных
- `WEBHOOK_*`: настройки проверки webhook API key
- `NEXTCLOUD_*`: конфигурация Nextcloud WebDAV
- `FILE_DOWNLOADER_*`: локальное временное хранилище, размер файла, разрешённые расширения
- `WORKER_*`: polling, retry, время блокировки задачи

## Локальный Запуск

### 1. Установить зависимости

```bash
poetry install
```

Если окружение уже создавалось раньше и состав зависимостей менялся, проще всего повторно выполнить `poetry install`.

### 2. Запустить PostgreSQL

Если локально нужна только база:

```bash
docker compose up -d db
```

### 3. Применить миграции

```bash
poetry run alembic upgrade head
```

### 4. Запустить API

```bash
poetry run python -m api.app
```

API будет доступен по адресам:

- `http://localhost:8003/health`
- `http://localhost:8003/docs`

### 5. Запустить worker во втором терминале

```bash
poetry run python -m worker.main
```

## Запуск Через Docker Compose

В репозитории уже есть:

- [Dockerfile](/home/shiawase/ic8/integration_layer_tilda_api/Dockerfile:1): один image для `api` и `worker`
- [docker-compose.yml](/home/shiawase/ic8/integration_layer_tilda_api/docker-compose.yml:1): основной compose-стек для `db`, `migrate`, `api` и `worker`

### Первый запуск, когда базы данных ещё нет

```bash
docker compose build --no-cache
docker compose up -d db
docker compose --profile ops run --rm migrate
docker compose up -d api worker
```

### Проверить состояние

```bash
docker compose ps
docker compose logs --tail=100 api
docker compose logs --tail=100 worker
```

### Остановить стек

```bash
docker compose down
```

## API Endpoint'ы

- `GET /health`: liveness-проверка API-процесса
- `POST /api/v1/webhooks/tilda`: приём webhook'а от Tilda, ответ — plain text `ok`

## Проверки Качества

Линтер:

```bash
poetry run ruff check .
```

Проверка типов:

```bash
poetry run python -m mypy .
```

Автотестов в репозитории пока нет.

## Ограничения И Допущения

- API ожидает webhook в формате `application/x-www-form-urlencoded`
- тестовый запрос Tilda с полем `test=test` принимается без создания записи в базе данных
- worker поддерживает только архивы `zip` и `rar`
- если Tilda присылает ссылку на `tupwidget.com`, worker извлекает из HTML прямую ссылку на `*.selstorage.ru`
- `GET /health` сейчас не проверяет доступность PostgreSQL и Nextcloud, а показывает только то, что API-процесс запущен

## Примечания

- `api` и `worker` — это отдельные процессы, но работают они на одной кодовой базе
- при локальной разработке после изменения кода worker нужно перезапускать вручную
- скачанные файлы временно сохраняются в `storage/tilda_downloads`
- перед загрузкой worker валидирует тип архива
- для масштабирования можно запускать несколько экземпляров worker'а на одной базе данных
