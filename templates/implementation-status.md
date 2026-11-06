# Журнал исполнения разработки

Начальная запись: 05.11.2026. Документация подготовлена; реализация и обучение не выполнены.
Обновляет исполнитель после реальной работы. Допустимые статусы: todo, in_progress, blocked, done.
Критерии — [основной план](../docs/11-product-development-plan.md); подробности — профильные документы.

| Этап | Статус | Evidence: пути/команды/результаты | Commit | Блокер / следующий шаг |
|---|---|---|---|---|
| S01 Каркас | done | Python 3.11.17 Linux: clean uv sync --locked; CLI help/version; ruff; 6 tests passed; подробности ниже | — | remote CI и Windows ещё не запускались; далее S02 |
| S02 Аудит данных | blocked | reports/data/dataset-card.md; signverod-metadata-audit.json; kaggle-metadata-audit.json; два воспроизводимых скрипта | f10d848; продолжение см. запись ниже | Два ZIP v1 получены, CRC/SHA-256 проверены; нет принятого корпуса ≥5 000, прав всех компонентов и пилота |
| S03 Импорт | todo | — | — | вход: принятый источник |
| S04 QC и split | todo | — | — | вход: корпус и человеческий QC |
| S05 Обучение | todo | — | — | вход: принятый split и GPU |
| S06 Core/CLI | todo | — | — | вход: bundle для полной приёмки |
| S07 API | todo | — | — | вход: core |
| S08 UI | todo | — | — | вход: API |
| S09 Упаковка | todo | — | — | вход: рабочий локальный продукт |
| S10 Сдача | todo | — | — | вход: финальные результаты и отчёт |
| S11 Эксплуатация | todo | — | — | после отдельного запроса на размещение |
| S12 Интеграции | todo | — | — | после выбора consumer |

## Запись выполненного шага — шаблон

- Дата и исполнитель:
- Этап / конкретная задача:
- Входы и версии:
- Изменённые файлы:
- Команды проверки и фактические результаты:
- Evidence: logs/reports/hashes (без секретов и приватных данных):
- Критерии: выполнены / не выполнены, причина:
- Ограничения и блокеры:
- Commit (при наличии):
- Точный следующий шаг:

Не записывать вымышленные метрики, не ссылаться на отсутствующие логи и не объявлять
исследование карточки датасета полной проверкой данных. Если изменился split или bundle,
указать, какие прежние метрики и проверки перестали относиться к текущей версии.

## S01 — 06.11.2026

- Исполнитель: Codex; поручение пользователя — сохранить уточнения и выполнить первый этап.
- Входы: проектные документы, схема v1, уточнения пользователя 06.11.2026, образец МИСПИС2.docx (только оформление).
- Созданы `pyproject.toml`, `uv.lock`, `.python-version`, `src/sealsign`, `.env.example`, `tests/test_startup.py`, `.github/workflows/ci.yml`.
- Пакет 0.1.0: `sealsign --help`, `sealsign --version`, `python -m sealsign`; логирование приложения и разрешение внешних путей без создания каталогов. ML-зависимостей и предсказаний пока нет.
- Зависимости: uv 0.13.4, Python 3.11.17, hatchling 1.27.0, pytest 8.3.5, ruff 0.11.13; транзитивные dev-зависимости и hashes — в uv.lock.
- Среда проверки: облачный Linux CPU. Установлен отдельный Python 3.11 в /tmp/sealsign-python; системный Python не менялся.
- Проверенные команды из корня репозитория:
  - `uv python install 3.11`: интерпретатор скачан и установлен; создание необязательной ссылки в read-only ~/.local/bin не удалось, uv использует установленный интерпретатор напрямую.
  - `uv lock`, `uv sync --locked`: успешно.
  - Чистый venv: `UV_PROJECT_ENVIRONMENT=/tmp/sealsign-clean uv sync --locked`: успешно, 6 пакетов; затем те же CLI/checks из этого окружения.
  - `uv run --no-sync sealsign --help`: exit 0, справка без весов/GPU.
  - `uv run --no-sync sealsign --version`: exit 0, sealsign 0.1.0.
  - `ruff check .`: All checks passed.
  - `ruff format --check .`: 6 files already formatted.
  - `pytest`: 6 passed (0.13 s в чистом окружении).
  - `git diff --check`: успешно.
  - `git check-ignore artifacts/references/report-example.docx`: образец исключён из Git.
- Служебные настройки облачной среды для uv: `UV_CACHE_DIR=/tmp/sealsign-uv`, `UV_PYTHON_INSTALL_DIR=/tmp/sealsign-python`; нужны из-за read-only домашнего каталога, не являются настройками продукта.
- Проверенные риски: CLI и импорт без модели/ML-библиотек; отсутствие создаваемых файлов при старте; пути с пробелами и внешние каталоги; ошибочный параметр CLI возвращает exit 2.
- CI повторяет установку из lock, lint, format, tests и CLI на ubuntu-latest/windows-latest, Python 3.11/3.12. Локальные проверки проходят; фактический GitHub Actions run ещё не запускался, совместимость Windows и Python 3.12 ещё не подтверждена исполнением.
- Решения сохранены в docs/08; паспорт образца — docs/13. Минимум данных теперь 5 000 уникальных страниц. Обучение, API/UI, модель и метрики не реализованы и не проверены.
- Git: после дополнительного поручения пользователя изменения S01 подготовлены к коммиту и push в origin/work. Коммит этапа определяется по сообщению `feat: implement S01 project scaffold and record requirements`; фактический результат push сообщается в чате.
- Следующий шаг S02: аудит лицензии, версии и реальных файлов Sig & Stamps, подсчёт уникальных страниц с проверкой обязательного N ≥ 5 000. Если единый набор меньше — подобрать дополнительные допустимые источники, раскрыть provenance и объём доразметки; минимум не снижать.

## S02 — 06.11.2026, доступная часть аудита

- Пользователь поручил следующий этап; автор Git настроен локально: chrtxachok <egormalanin425@gmail.com>.
- Повторно прочитаны инструкции, планы и реестр; S01 опубликован ранее как 63f17d4.
- Добавлены reports/data/dataset-card.md, reports/data/signverod-metadata-audit.json, scripts/audit_signver_metadata.py; обновлены ссылки и реестр.
- Получены полный Git tree и пять CSV/text файлов SignverOD-зеркала зафиксированной ревизии; сырые метаданные хранятся в gitignored artifacts/data-audit/signverod/. Изображения и веса не скачивались.
- Измерено: 2 765 файлов, 2 761 различных Git blob, 4 группы побайтовых дублей; 632 коллизии image ID; 7 549/1 666 строк bbox train/test. Это проверка метаданных, не QC изображений. Полные counts и SHA-256 входов — JSON-отчёт.
- Прочитаны источники резервных кандидатов, первичные README/LICENSE DocLayNet; составлен сравнительный паспорт с точными blob ID и ограничениями.
- Команда: `python scripts/audit_signver_metadata.py artifacts/data-audit/signverod --output reports/data/signverod-metadata-audit.json` — exit 0, accepted_for_training=false. Скрипт не разрешает обучение и не заменяет S03 importer.
- Сеть: curl к universe.roboflow.com — proxy CONNECT 403; environment_status подтверждает restricted/enforced и отсутствие Roboflow/Kaggle в allowlist. Это блокировка окружения, не 403 самого сайта. Запрос открытия доступа отправлен пользователю.
- Критерии S02 не выполнены: нет принятого экспорта, проверенной первичной лицензии Sig & Stamps, checksum архива, ≥5 000 пригодных оригиналов и визуального пилота. Статус blocked, не done.
- Следующий шаг: первичные Roboflow/Kaggle-карточки и экспорт, затем counts/dedup, пилот до 200 страниц и выбор дополнительных источников при недостаточном N.
- Изменения аудита коммитятся и отправляются в origin/work отдельным коммитом `research: audit S02 dataset candidates and record blockers`; данные и персональные образцы не включаются.

- Проверки изменений S02: `ruff check .` — passed; `ruff format --check .` — 7 files formatted; `pytest` — 6 passed (0.15 s); `git diff --check` — passed. Изменён ignore `data/` на `/data/`, чтобы разрешить только агрегированные отчёты в reports/data/; исходный корпус по-прежнему исключён.


## S02 — 06.11.2026, продолжение от f10d848

- Поручение: продолжить только S02 в work, сначала проверить Roboflow/Kaggle,
  по результату commit/push с автором chrtxachok <egormalanin425@gmail.com>.
- Локальная ветка была на ab4a900; `git fetch origin work` и fast-forward на
  FETCH_HEAD подтвердили f10d848. Прочитаны актуальные AGENTS.md, журнал и профильные документы.
- Использована инструкция cloud-environment-runtime: проверены текущая readiness,
  `/etc/codex/network-policy.json`, штатный proxy/TLS. Политика restricted/enforced,
  Roboflow/Kaggle разрешены, secrets/outbound identities отсутствуют.
- Сеть с разрешённым сетевым доступом исполнительной песочницы: Roboflow root API
  200 JSON, project API без ключа 401, Universe root 403; Kaggle search/view/list 200.
  Запросы внутри исходной песочницы сеть не имели; это ограничение запуска, не сервиса.
- Проверены version-pinned download endpoints mirror v1 и SignverOD v15: 302 на
  storage.googleapis.com. Переход mirror download дал proxy CONNECT 403; домена нет
  в allowlist. Пользователю отправлен конкретный запрос открытия домена; ключи в чат не запрашивались.
- Созданы scripts/audit_kaggle_metadata.py, tests/test_kaggle_audit.py,
  reports/data/kaggle-metadata-audit.json; обновлены паспорт, README, docs/08 и docs/09.
- Полные списки пяти кандидатов: 2 452 / 2 765 / 17 110 / 842 / 1 000 изображений.
  Основной mirror v1 имеет Unknown и меньше 5 000; SignverOD v15 — CC0 по API.
  В новом кандидате 16 000 RVL-CDIP не имеют целевых labels, 810 signatures и
  300 stamps требуют проверки полноты обоих классов. Это не подтверждённые оригиналы.
- Evidence: отчёт содержит номера версий, размеры view/list, SHA-256 всех ответов;
  сырые API-ответы только в gitignored artifacts/data-audit/kaggle/inventory/.
  List не поддерживает version pinning: view проверен до/после, ограничение раскрыто.
- Реально исполнена команда полного сбора из раздела 5 паспорта; exit 0,
  до конца пройдены все списки, totalBytes view совпали с суммой list.
- Проверки: `UV_CACHE_DIR=/tmp/sealsign-uv uv sync --locked --python python3.12`
  — успешно; Python 3.12.14 Linux CPU, uv 0.13.4. `.venv/bin/ruff check .` — passed;
  `.venv/bin/ruff format --check .` — 9 files formatted;
  `.venv/bin/pytest` — 10 passed (0.18 s); `git diff --check` — passed.
  Новые tests проверяют повторные пути, пагинацию, смену версии и отличие счётчика
  изображений от проверенных оригиналов; сеть в tests не используется.
- Критерии S02 выполнены частично: установлены текущие API-версии/декларации лицензий
  и состав файлов. Не выполнены: архив/checksum ZIP, проверенные права всех выбранных
  источников, ≥5 000 пригодных уникальных страниц, визуальный пилот и оценка доразметки.
  accepted_for_training=false. S03 и обучение не запускались, метрик модели нет.
- Следующий шаг: разрешить storage.googleapis.com, загрузить version-pinned экспорты,
  сохранить SHA-256, проверить README/YAML/условия компонентов нового составного
  кандидата и первичные условия Sig & Stamps; выполнить совместный пилот до 200 страниц.
- Git: коммит продолжения определяется сообщением
  `research: continue S02 with public Kaggle inventories`; результат push сообщается в чате.


## S02 — 06.11.2026, проверка реальных ZIP

- Поручение пользователя: продолжить S02, проверить доступ, commit/push в work.
- После fetch актуальная origin/work оказалась на e8895aa поверх f10d848;
  выполнен fast-forward, существующие результаты сохранены. AGENTS.md, журнал,
  README, docs/00, docs/08, docs/09, docs/11 и профильный docs/03 прочитаны.
- Сеть: текущая политика restricted/enforced разрешает Roboflow/Kaggle и
  storage.googleapis.com. API Roboflow root 200, Universe project 403,
  Kaggle search 200. После разрешения сети исполнительной песочницы загрузки работают;
  штатные proxy/TLS сохранены, секреты не настроены.
- Получены version-pinned ZIP Sig & Stamps v1 (169 435 546 байт) и составного
  zeadekrame v1 (1 989 701 019 байт). SHA-256, команды, YAML evidence и результаты
  — раздел 6 reports/data/dataset-card.md, sig-stamps-zip-audit.json,
  composite-zip-audit.json. ZIP/изображения только в gitignored artifacts/.
- scripts/audit_dataset_zip.py проверяет CRC всех членов без распаковки,
  считает SHA-256 изображений, дубли, пересечения исходных split и строки labels;
  отклоняет небезопасные/повторные пути, symlink и превышение бюджета.
  Это аудит байтов и структуры, не importer, декодер или геометрический validator.
- Sig & Stamps: 2 452 различных байтовых изображения, 5 265 строк, 16 пустых labels.
  YAML 0=signature/1=stamp требует обратного mapping; polygon rows нельзя
  интерпретировать как готовые bbox. Лицензия Unknown; минимум 5 000 не выполнен.
- Составной набор: 17 110 изображений, 17 075 разных SHA-256. 16 000 RVL-CDIP
  не имеют целевых labels; 810 signatures дают 4 148 строк и 56 пустых labels;
  300 stamps дают 486 строк и 285 разных SHA-256. В stamps 3 группы exact-дублей
  пересекают train/val. Такой split не принимать без перегруппировки.
- В YAML signatures есть декларация CC BY 4.0 и Roboflow v1; у stamps отсутствуют
  источник/лицензия. Декларация лицензии сборки не устанавливает права компонентов.
  Mapping signatures 0→1, stamps 0→0: source class ID без provenance неоднозначен.
- Критерии S02: реальные экспорты/checksum/CRC и структурные counts получены.
  Не выполнены: подтверждённые права всех компонентов, ≥5 000 пригодных оригиналов,
  визуальный совместный пилот и оценка доразметки. accepted_for_training=false;
  S02 blocked. Декодирование, S03 и обучение не запускались, метрик модели нет.
- Следующий шаг: первичные условия signatures, provenance/условия stamps и RVL-CDIP;
  затем декодирование/near duplicates и совместный воспроизводимый пилот до 200 страниц.
- Git: коммит шага определяется сообщением `research: audit downloaded S02 dataset archives`;
  push в origin/work выполняется по поручению пользователя, автор chrtxachok
  <egormalanin425@gmail.com>. Данные, secrets и приватные примеры не включаются.
- Проверки: Python 3.12.14 Linux CPU; `UV_CACHE_DIR=/tmp/sealsign-uv uv sync --locked --python python3.12`
  успешно; обе команды ZIP-аудита из паспорта завершились exit 0.
  `.venv/bin/ruff check .` — passed; `.venv/bin/ruff format --check .` — 11 files formatted;
  `.venv/bin/pytest -q` — 16 passed (0.26 s); `git diff --check` — passed.
  Новые тесты: CRC повреждённого ZIP, опасные пути/symlink, обнаружение exact leakage,
  различие пустых labels/непроверенных страниц и подтверждённых negatives.
  `git check-ignore` подтвердил исключение ZIP из Git; GPU/модель не проверялись.
