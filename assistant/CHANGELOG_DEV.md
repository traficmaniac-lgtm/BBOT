# Dev Changelog

## 2025-02-05
- Добавлен клиент Binance (python-binance) и PairLoader с детекцией fee-free (API/эвристика/ручной whitelist) и fallback в мок.
- UI вкладки Pairs: новая таблица (Symbol/Base/Quote/FeeFree/FeeMethod), фильтры search/quote/fee-free, выбор пары открывает Trading.
- Статусбар показывает активную пару/стейт/подключение; обновлена UI-спека и briefing.

## 2025-02-01
- Обновлен гид для Виктории с описанием параллельного процесса через `assistant/` файлы.
- Зафиксированы новые вопросы/решения, добавлены шаги по будущему UI-рефакторингу.
- README дополнен ссылкой на brief и описанием принципа parallel dev.

## 2025-01-01
- Добавлены подробные спецификации (TZ, ROADMAP, UI_SPEC, AI_CONTRACT, CONFIG_SPEC, SECURITY).
- Созданы файлы связи с Викторией (BRIEF, STATUS, QUESTIONS, DECISIONS, CHANGELOG_DEV).
- Реализован каркас приложения: конфиг-сервис, state machine, AI мок, GUI на Tkinter с вкладками.
- Добавлены шаблоны конфигов и .bat файлы для обновления и запуска.
