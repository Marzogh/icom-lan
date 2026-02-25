# AGENTS.md — AI Agent Instructions

## Проект

**icom-lan** — Python-библиотека для управления трансиверами Icom по LAN.
Чистая реализация проприетарного UDP-протокола Icom, без зависимости от wfview или RS-BA1.

## Философия

Это **библиотека**, не приложение. Каждое решение оценивай через призму:
- "Удобно ли это **пользователю библиотеки**?"
- "Понятно ли это без чтения исходников?"
- "Можно ли это использовать в одну строку?"

## Принципы разработки

### API Design
- **Pythonic API** — `radio.frequency`, не `radio.get_frequency()` (используй properties)
- **Sync + Async** — основной код async, sync-обёртка через `asyncio.run`
- **Context managers** — `async with IcomRadio(...) as radio:` для автоматического disconnect
- **Sensible defaults** — подключение к радио должно работать с минимумом параметров
- **Type hints everywhere** — строгая типизация, `py.typed` маркер
- **Enum для режимов/настроек** — `Mode.USB`, не магические строки

### Код
- **Чистая архитектура** — transport, protocol, commands, audio — отдельные слои
- **Без глобального состояния** — всё через экземпляры классов
- **Без side effects при импорте** — `import icom_lan` ничего не делает
- **Логирование через `logging`** — не print, не loguru. Стандартный модуль.
- **Минимум зависимостей** — для core: только stdlib. Opus — optional dependency.

### Качество
- **TDD** — сначала тест, потом код. Без исключений.
- **pytest** — единственный фреймворк для тестов
- **Моки для UDP** — тесты не требуют реального радио
- **Integration tests** — отдельно, помечены `@pytest.mark.integration`, требуют радио
- **100% type coverage** — mypy strict
- **Docstrings** — Google style, на английском

### Git
- **Conventional commits** — `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
- **Маленькие коммиты** — одна логическая единица на коммит
- **Ветки не нужны** — пока solo-разработка, коммитим в main

## Структура проекта

```
icom-lan/
├── src/icom_lan/           # Исходный код
│   ├── __init__.py         # Публичный API, реэкспорт
│   ├── radio.py            # IcomRadio — главный класс
│   ├── transport.py        # UDP transport, keep-alive
│   ├── protocol.py         # Packet parsing, serialization
│   ├── commands.py         # CI-V команды
│   ├── audio.py            # Аудио стриминг (Opus)
│   ├── types.py            # Enums, dataclasses, типы
│   └── exceptions.py       # Кастомные исключения
├── tests/
│   ├── conftest.py         # Фикстуры, моки UDP
│   ├── test_protocol.py    # Парсинг/сериализация пакетов
│   ├── test_transport.py   # Подключение, keep-alive
│   ├── test_commands.py    # CI-V команды
│   ├── test_radio.py       # Интеграция через IcomRadio
│   └── integration/        # Тесты с реальным радио
├── docs/
│   └── PROJECT.md          # Цели, план, протокол
├── references/
│   └── wfview/             # Склонированный wfview (gitignored)
├── README.md
├── pyproject.toml
├── AGENTS.md               # Этот файл
└── CLAUDE.md               # Инструкции для Claude Code
```

## Workflow

1. Перед началом работы — прочитай `docs/PROJECT.md` (план и текущая фаза)
2. Перед написанием кода — напиши тест
3. Перед коммитом — убедись что `pytest` проходит
4. После значимых изменений — обнови `docs/PROJECT.md` (чеклист фазы)

## Reference Code

`references/wfview/` — склонированный wfview для изучения протокола.
**Ключевые файлы:**
- `include/packettypes.h` — структуры пакетов (начни с него)
- `src/radio/icomudpbase.cpp` — UDP transport
- `src/radio/icomudphandler.cpp` — auth/login
- `src/radio/icomudpcivdata.cpp` — CI-V через UDP
- `src/radio/icomcommander.cpp` — все CI-V команды

**ВАЖНО:** Не копируй код wfview. Изучай протокол, пиши свою реализацию.

## Тестовое оборудование

- Icom IC-7610 на `192.168.1.100`
- Порты: 50001 (control), 50002 (ci-v), 50003 (audio)
- Username/password: настраиваются в IC-7610 network settings
