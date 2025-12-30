# BBOT Desktop Copilot

Desktop GUI-приложение для подготовки и запуска торгового бота (без реальных ордеров в v0.1). Содержит конфигуратор, загрузку fee-free пар, AI-анализ параметров и state machine.

## Быстрый старт
1. Создай виртуальное окружение `.venv` и установи зависимости:
   ```bash
   python -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```
2. Скопируй `config/config.example.yaml` в `config/config.yaml` и заполни ключи (файл не коммитится).
3. Запусти GUI: на Windows через `run_app.bat`, на других ОС `python main.py`.

## Где что лежит
- `ui/` — Tkinter GUI, вкладки Dashboard/Pairs/AI/Trading/Risk/Logs/Settings.
- `core/` — конфиги, стейт, логирование.
- `ai/` — prompt builder, клиент (OpenAI или мок).
- `exchanges/` — интерфейсы и мок загрузки пар.
- `assistant/` — связь Codex ↔ Victoria (см. быстрый гид `assistant/VICTORIA_BRIEF.md`).
- `docs/` — спецификации. Roadmap: `docs/ROADMAP.md`.
- `config/` — шаблон и локальный конфиг.
- `logs/` — вывод логов приложения.

## Полезные документы
- Полное ТЗ: `docs/TZ.md`
- Roadmap: `docs/ROADMAP.md`
- UI Specification: `docs/UI_SPEC.md`
- AI контракт: `docs/AI_CONTRACT.md`
- Config spec: `docs/CONFIG_SPEC.md`
- Быстрый гид для Виктории: `assistant/VICTORIA_BRIEF.md`

## Параллельная работа Codex ↔ Victoria
- Общаемся через файлы в `assistant/`: STATUS (срез), CHANGELOG_DEV (что изменилось), QUESTIONS (открытые вопросы), DECISIONS (принятые решения), VICTORIA_BRIEF (шпаргалка по проекту).
- После каждого изменения обновляем STATUS и CHANGELOG_DEV, чтобы синхронизация шла без личной переписки.

