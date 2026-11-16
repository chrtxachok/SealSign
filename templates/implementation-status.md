# Журнал исполнения разработки

Начальная запись: 05.11.2026. Документация подготовлена; реализация и обучение не выполнены.
Обновляет исполнитель после реальной работы. Допустимые статусы: todo, in_progress, blocked, done.
Критерии — [основной план](../docs/11-product-development-plan.md); подробности — профильные документы.

| Этап | Статус | Evidence: пути/команды/результаты | Commit | Блокер / следующий шаг |
|---|---|---|---|---|
| S01 Каркас | done | Python 3.11.17 Linux: clean uv sync --locked; CLI help/version; ruff; 6 tests passed; подробности ниже | — | remote CI и Windows ещё не запускались; далее S02 |
| S02 Аудит данных | blocked | reports/data/dataset-card.md; signverod-metadata-audit.json; kaggle-metadata-audit.json; два воспроизводимых скрипта | f10d848; продолжение см. запись ниже | Два ZIP v1 получены, CRC/SHA-256 проверены; нет принятого корпуса ≥5 000, прав всех компонентов и пилота |
| S03 Импорт | blocked | docs/14; src/sealsign/data; import-verification.json; 46 tests passed | см. запись S03 | код и исследовательские прогоны готовы; вход S02 не принят, исключения требуют QC |
| S04 QC и split | blocked | docs/15-qc-pilot.md; два пилота по 50 страниц; исследовательский аудит пересечений docs/16 | см. запись S04 | нужны принятый корпус, независимый просмотр, устранение спорных случаев и групповой split |
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


## S03 — 06.11.2026, импорт и канонические аннотации

- Поручение пользователя: «следующий этап»; выполнена независимая реализация S03,
  блокер принятия источника из S02 сохранён. Ветка work, исходный commit 57d05de.
- Добавлены src/sealsign/data/{geometry,importer,validator}.py, CLI data import/validate,
  configs/import-{sig-stamps-v1,composite-labels-v1}.json, docs/14-data-import.md,
  tests/test_data_import.py и reports/data/import-verification.json; обновлены README,
  журнал и решения. Pillow==13.0.0 закреплён в pyproject.toml и uv.lock.
- Импортёр: ZIP SHA-256 и бюджет, запрет traversal/symlink/повторов, orphan labels,
  неоднозначных image→label; стабильные page_id, source checksum/геометрия/provenance,
  pixel COCO bbox, производные unreviewed YOLO, PNG и технические previews.
  EXIF 1–8 преобразуется согласованно с рамками; исходный split сохраняется отдельно.
- Все страницы unreviewed, новые split/group IDs null. Missing и empty_unreviewed
  различаются. Ошибочная страница остаётся в manifest с причиной, без частичных рамок.
  accepted_for_training=false. Безопасный новый output, существующий не перезаписывается.
- Проверенная среда: Linux CPU, Python 3.12.14, Pillow 13.0.0. Сеть/готовность
  cloud environment проверены; штатные proxy/TLS сохранены. Команды:
  - `UV_CACHE_DIR=/tmp/sealsign-uv uv lock --python python3.12` и
    `UV_CACHE_DIR=/tmp/sealsign-uv uv sync --locked --python python3.12`: успешно.
    Первая попытка uv lock без выбора Python упёрлась в read-only home для Python 3.11;
    исправлено явным выбором имеющегося Python 3.12, системная конфигурация не менялась.
  - `.venv/bin/sealsign data import --help`: exit 0.
  - Оба import из docs/14 исполнены через `.venv/bin/sealsign`, preview-limit=12:
    Sig & Stamps — 2 452 входных/канонических страниц, 5 265 рамок, 0 исключений;
    составной — только 1 110 выбранных signatures/stamps, 1 102 канонических страниц,
    4 613 рамок, 8 исключений Box extends outside image. Весь RVL-CDIP не импортирован.
  - Первое исполнение на JPEG выявило отсутствие атрибута n_frames у JpegImageFile;
    исправлено через getattr с default=1, добавлен регрессионный тест.
  - `uv run --no-sync sealsign data validate artifacts/data-import/composite-labels-v1`
    (UV_CACHE_DIR=/tmp/sealsign-uv): exit 0, 1 102 images/4 613 annotations.
    uv предупредил о .python-version=3.11 при активной 3.12; следующий запуск явно
    использовал `--python python3.12` (обе версии разрешены pyproject).
  - `uv run --no-sync --python python3.12 sealsign data validate artifacts/data-import/sig-stamps-v1`
    (тот же cache): exit 0, 2 452 images/5 265 annotations.
  - `.venv/bin/ruff check .`, `.venv/bin/ruff format --check .`, `git diff --check`: passed.
    `.venv/bin/pytest -q`: 46 passed (0.66 s). Tests без внешних данных/сети.
- Проверены реальная конвертация bbox/polygon и mapping, все EXIF, NaN/out-of-bounds,
  неверный class, повреждённый файл, небезопасные ZIP/повтор/symlink, orphan/ambiguity,
  exact duplicate groups, повторяемость, подмена checksum/геометрии/YOLO и CLI end-to-end.
- Counts до/после: Sig & Stamps сохраняет все 5 265 строк (1 834 stamp/3 431 signature),
  16 пустых labels не считаются negatives. В composite остаётся 4 148 signature/465 stamp;
  8 исключённых stamp-страниц содержат 21 исходную строку; 56 пустых labels unreviewed.
  Все выбранные реальные изображения имеют EXIF=1; EXIF 2–8 проверены на fixtures.
- Ограничения: нет принятого источника ≥5 000 из S02, совместного визуального QC и
  решения по исключениям. CSV/COCO/raster masks не поддерживаются как вход;
  полная топология polygon не проверяется. Preview первых 12 — не случайный пилот S02.
  Ни уникальные оригиналы, ни полнота двух классов, ни обучение этим не подтверждены.
- Статус S03 blocked, не done: реализация и исследовательский прогон подтверждены,
  приёмка на разрешённом корпусе зависит от S02. S04 и обучение не запускались.
- Следующий шаг: закрыть права/provenance и пилот S02, согласовать 8 исключений,
  повторить импорт принятого корпуса; затем переходить к QC/группировке S04.
- Git: отдельный коммит `feat: implement research data import and validation`, затем
  push origin/work, автор chrtxachok <egormalanin425@gmail.com>. Данные/превью не публикуются.


## S04 — 15.11.2026, подготовка совместного пилота

- По просьбе пользователя продолжается работа в облачном checkout work с c224810.
  Папка Windows D: из облачной среды не была видна; архивы восстановлены через
  публичный version-pinned Kaggle API, штатный proxy/TLS. Локальные ZIP и данные
  находятся только под gitignored artifacts/ и в Git не включаются.
- SHA-256 совпали с паспортом S02: Sig & Stamps v1 —
  f5719c8acb7dcf903b84c3ca0f68fe5523031e809b514d1c8f32493e4bbc6617;
  zeadekrame v1 — ed41b57f00a2d91ce218fcc7f333fd70300c67f9b0d926ffc7c206d62d156594.
  Первый ZIP повторно импортирован: 2 452 images, 5 265 annotations, 0 исключений;
  `sealsign data validate` exit 0. Пригодность/права этим не подтверждаются.
- Созданы scripts/prepare_qc_pilot.py и docs/15-qc-pilot.md, тесты отбора и
  checksum; подготовлена приватная выборка 50 страниц исходного train, seed=42:
  `artifacts/data-qc/sig-stamps-pilot-v1/`. Test не использован. В выборке
  не повторяются точный SHA-256 и префикс имени до `.rf.`; это не доказательство
  независимости документов и не проверка near duplicates.
- Локальный manifest SHA-256 d41609f98e391dd607cdea95299735b13540bfce8aed1b98802339c626e9cd71;
  annotations SHA-256 6f70d9551492df1aff01aedf9bdd5d50aac27692b02a6821abe97f93e87f40a5.
  pilot.json фиксирует page IDs и seed, отдельные pages/ и annotated/ предназначены
  для независимого просмотра; review-template.csv не содержит решений.
- Проверки на Python 3.12.14: `.venv/bin/ruff check .` — passed;
  `.venv/bin/ruff format --check .` — passed; `.venv/bin/pytest -q` — 48 passed;
  отбор исключает upstream test, воспроизводим и отклоняет изменение изображения.
  Реальная команда подготовки и формат записаны в docs/15.
- S04 blocked: пилот подготовлен, но просмотр и согласование не проведены;
  source ещё не принят в S02/S03, права и ≥5 000 независимых страниц не доказаны.
  Не назначены group/split и не проводилось обучение. Следующий шаг: независимый
  просмотр пилота, фиксация спорных случаев и проверка прав; после этого полный QC,
  объединение групп и разбиение по документам/дублям.

- Дополнительно тот же отбор применён к импортированным signatures/stamps из
  составного ZIP: 50 страниц train (38 signatures, 12 stamps), без RVL-CDIP.
  При импорте получены 1 102 из 1 110 images, 4 613 annotations и 8 исключённых
  страниц с bbox за границами; `sealsign data validate` exit 0. Manifest SHA-256
  0011868b7f70e676c97a954f8f959822b742b3354ec1e6fb0e23392aa2175607,
  annotations SHA-256 1f40f98c3b8c455e572b56bf5af0d4727c2cd0f5bd0c1146a16b5cd84c8f15ac.
  Оба пилота упакованы в отдельные приватные ZIP под artifacts/data-qc/;
  в каждом есть README, исходные страницы, рамки и пустой review-template.csv.
  S04 остаётся blocked: просмотр этих страниц ещё не выполнен.


## S04 — 15.11.2026, диагностика пересечений

- По поручению пользователя продолжена доступная работа S04 при ожидающемся
  человеческом просмотре. Добавлены scripts/audit_leakage.py, docs/16-leakage-audit.md,
  tests/test_leakage_audit.py и агрегированный reports/data/leakage-audit.json.
- Из двух локальных импортированных bundle проверены checksums и 3 554 PNG;
  исключённые 8 страниц и неимпортированные 16 000 RVL-CDIP не исследовались.
  Входные хеши, параметры и полная команда записаны в отчёте и docs/16.
- На разных исходных split одного архива: 3 пары точных исходных SHA-256 в
  composite и 1 545 пар совпадающих префиксов `.rf.` в Sig & Stamps (176 page_id).
  Префикс — лишь эвристика: пары не являются подтверждёнными дубликатами.
- dHash grayscale 9×8, Hamming ≤2: 225 кандидатных пар; 115 между источниками.
  Категории пересекаются, похожие документы могут не быть дублями, часть реальных
  дублей может не обнаружиться. Детальный CSV с page_id — только gitignored
  artifacts/data-qc/leakage-audit-v1/. Ни один кандидат не помечен проверенным.
- Проверки: Python 3.12.14, Pillow 13.0.0; реальная команда docs/16 exit 0,
  `.venv/bin/ruff check .` и `.venv/bin/ruff format --check .` — passed,
  `.venv/bin/pytest -q` — 51 passed, `git diff --check` — passed.
  Тестируются точные пересечения, одинаковый смысл valid/val, изменение PNG
  и неразрешение обучения. Источники и приватные изображения не коммитятся.
- S04 остаётся blocked: проверки визуальной разметки и прав, разрешение candidate
  pairs, группировка всех страниц и новый split не завершены. Список candidate pairs
  не содержит внутрисплитных пар одного источника и не является готовым split.
- Git: `research: audit dataset leakage candidates`, push в work; автор
  chrtxachok <egormalanin425@gmail.com>.


## S04 — 15.11.2026, обратная связь по пилотам

- Пользователь сообщил в чате, что проверил оба пилота (по 50 страниц), и дал
  общую оценку: «в целом нормально». Это подтверждение просмотра и общего
  впечатления; отдельные решения по страницам, перечень ошибок и заполненные
  таблицы не предоставлены. Уточнение о пропусках, неверных рамках и спорных
  случаях запрошено пользователю.
- Не делать вывод об отсутствии ошибок или принятии каждой bbox из общей оценки.
  Независимый второй просмотр, полная проверка корпуса на оба класса, разрешение
  совпадений, группировка и новый split остаются незавершёнными. S04 blocked.


## S04 — 15.11.2026, замечания к составному пилоту

- Пользователь указал: composite sample 003 — левая копия печати не размечена;
  sample 037 — нижняя рамка не охватывает печать снизу. Эти случаи повторно
  просмотрены на annotated preview: оба замечания подтверждаются визуально.
- Sample 003: page_id df58bed8a9cce64fc0f5dee1412ca126aae51f5edb8c6f8cd0b39e8a7280d86a.
  Sample 037: page_id a0848883cd999a9604596dd09cf9607c96c063bf3c2b48d9cb2cd7121926ce1f.
  Номера относятся к composite-labels-pilot-v1, seed=42. Изображения не публикуются.
- На preview заметны цветные надписи и рамки помимо красной рамки нашего preview;
  происхождение этих элементов требуется проверить по исходным пикселям и источнику.
  Страницы остаются unreviewed: исправленные координаты и bbox в каноническую
  разметку не вносились; возможные подписи на этих страницах также требуют QC.
- Оба случая направлены на доразметку и второй просмотр. Нельзя считать весь
  набор полностью размеченным; решение о corpus/split и статус S04 не меняются.


## S04 — 15.11.2026, исправления и аудит источника

- Пользователь подтвердил фиолетовые предложенные рамки обоих образцов composite
  (003 — добавить bbox печати, 037 — исправить нижнюю bbox). Исходный bundle v1
  сохранён; локально создан composite-labels-qc-v2 с provenance в qc-corrections.json.
  Изменена одна bbox, добавлена одна, удалений нет; обновлены два derived YOLO
  файла и annotation_version двух manifest страниц. Обе страницы unreviewed.
- Базовый annotations SHA-256 1f40f98c3b8c455e572b56bf5af0d4727c2cd0f5bd0c1146a16b5cd84c8f15ac;
  новый b1cb6838e3a972df80944b846ca873eb9016517e369f4bb89b15c1d68b49711c.
  Private qc-corrections.json SHA-256 70b6d39622892886f9c6766b80c8c7e6de98f6c8c6ca319619784b9681846cd3;
  локальный одноразовый скрипт создания с проверкой base hash/PNG сохранён в
  artifacts/data-qc/composite-corrections-v1/apply-confirmed.py.
- Валидатор qc-v2: pages=1 110, images=1 102, annotations=4 614,
  accepted_for_training=false. Сравнение с v1: 1 изменённая bbox, 1 добавленная,
  0 удалённых, 2 изменённые записи manifest. Старый аудит пересечений относится
  к v1; для qc-v2 требуется отдельное доказательство перед split.
- На 003 и 037 зелёные рамки и `Stamp` видны уже в исходных нормализованных PNG;
  подтверждено совпадение PNG из pilot/pages и исходного импортированного bundle.
  Команда audit_green_pixels.py по узкому RGB-порогу нашла кандидатов во всех
  292 декодированных изображениях stamps; это не визуальное подтверждение 292
  нанесённых рамок, естественные зелёные объекты могут дать ложные срабатывания.
  8 исключённых страниц не проверены; другие компоненты команда не оценивает.
- Технические ограничения и доказательства — docs/17-source-overlay-audit.md,
  агрегированный reports/data/green-pixel-audit.json; приватные координаты и PNG
  только в artifacts/. Яркая разметка в пикселях — риск утечки меток и качества.
- Проверки: `.venv/bin/sealsign data validate artifacts/data-import/composite-labels-qc-v2`
  exit 0; сравнение различий с v1; `.venv/bin/ruff check .`,
  `.venv/bin/ruff format --check .`, `.venv/bin/pytest -q` (53 passed) и
  `git diff --check` — passed. S04 по-прежнему blocked: нет принятого чистого
  корпуса и полного QC обоих классов; обучение и новый split не проводились.


## S04 — 15.11.2026, проверка дополнительного источника

- Пользователь поручил закончить S04 и подтвердил минимум 5 000. Выполнены
  публичный поиск Kaggle и полный metadata inventory дополнительного источника
  dablsi/stamp-recognition-documents-with-stamps v1. Команда:
  `.venv/bin/python scripts/audit_kaggle_metadata.py dablsi/stamp-recognition-documents-with-stamps --raw-dir artifacts/data-audit/research-20261115/inventory --output reports/data/stamp-recognition-metadata-audit.json`.
  Exit 0, 20 страниц list; версии view до/после совпали, сумма байтов list
  совпала с view. Архив и изображения этого источника не скачивались.
- 3 919 PNG: по именам каталогов 1 696 отдельных изображений печатей и
  2 223 документа; ещё 1 AVI. Готовых labels не найдено, описание API пустое.
  Декларация CC BY 4.0 по API не подтверждает provenance каждого файла.
- Дополнение не принимается как размеченный корпус. Критерии S04 остаются
  невыполненными: нет принятого корпуса ≥5 000 с полной проверкой обоих классов
  и независимым вторым просмотром. Подтверждение двух исправленных рамок
  не покрывает остальную разметку. Group split и обучение не запускались.


## S04 — 15.11.2026, поиск чистой замены

- Пользователь поручил найти чистый источник и выполнить проверки. Проведены
  новые поиски Kaggle и web; найден mapo80/stamps на Hugging Face с заявленной
  очищенной редакцией, 7 854 изображениями и CC BY 4.0. Карточка одноклассовая;
  оригинальность и полнота подписей не установлены. Детали/URL/ограничения —
  reports/data/clean-source-search.md.
- Реальная попытка получить API huggingface.co через proxy/TLS: CONNECT 403,
  домен не разрешён текущей политикой. Запрошено добавление домена. Скачивание,
  revision pinning, CRC, hashes, counts и визуальный QC нового источника ещё
  не выполнены. Принимать набор или закрывать S04 по карточке нельзя.
- Не выбран gated hvpu/document-signature-stamp-dataset: требуются принятие
  условий аккаунтом пользователя и проверка лицензии/аннотаций. Условия не принимались.


## S04 — 15.11.2026, фактический аудит mapo80/stamps

- После открытия huggingface.co и us.aws.cdn.hf.co скачаны три ZIP ревизии
  998243bde1262ccb57ca28ddd6868b05fd1ddf49. SHA-256/размеры/команды — docs/18.
- Полный CRC, безопасный inventory, декодирование всех 7 854 файлов, геометрия
  12 659 stamp bbox и связи labels проверены: ошибок не обнаружено. 7 854 разных
  source SHA-256, 0 точных дублей; 0 ярко-зелёных кандидатов по прежнему порогу.
  Результат не доказывает 7 854 независимых оригиналов или полноту подписей.
- Проверены первичные карточки четырёх положительных upstream-источников: CC BY 4.0
  декларируется. Условия negatives RVL-CDIP/FUNSD и история каждого скана ещё
  не подтверждены. Предыдущие карточки иных ревизий не используются как counts.
- Из train seed=42 получены 50 исходных файлов, sample provenance в artifacts/;
  импорт 50/50, 84 stamp bbox, 7 пустых labels. Валидатор exit 0. Агент просмотрел
  пять контактных листов всех 50 страниц: заметны подписи без signature-labels,
  похожие шаблоны и повторяющиеся виды печатей. Это не полный QC каждой bbox,
  не второй просмотр и не принятие корпуса. Приватный review ZIP подготовлен.
- Дополнительный dHash-аудит всех файлов: 2 685 пар ≤2, из них 868 cross-split;
  просмотр первых 3 train/train пар показал разные письма с похожей компоновкой.
  CSV хранит только первые 1 000 кандидатов. Нельзя автоматически группировать
  все пары как дубли; разметка test для настройки не просматривалась.
- Добавлены scripts/audit_clean_zip.py и тест структурного контроля; реальная
  команда успешно завершена, .venv/bin/pytest -q — 54 passed, ruff check/format
  и git diff --check — passed. ZIP, PNG, sample labels остаются gitignored.
- S04 blocked: кандидат технически лучше прежнего компонента, но необходимо
  доразметить подписи на каждой используемой странице, выполнить независимый
  второй QC и подтвердить ≥5 000 независимых исходных страниц после группировки.
  Новый split/обучение не запускались; accepted_for_training=false.


## S04 — 15.11.2026, редактор первого просмотра

- По поручению пользователя подготовлен переносимый HTML-редактор текущего
  mapo80 pilot50. Встраиваются изображения и 84 stamp bbox; можно рисовать
  подписи/печати, менять класс/численные координаты, удалять объекты, отмечать
  просмотр обоих классов и экспортировать/загружать JSON. Нет внешнего backend.
- Код: src/sealsign/data/editor/editor.html; scripts/build_annotation_editor.py,
  scripts/validate_annotation_review.py; инструкция docs/19-annotation-editor.md.
  Приватный ZIP artifacts/annotation-editor/mapo80-editor-pilot50.zip содержит
  editor.html и README.txt (28 511 607 байт); исходный HTML 38 145 604 байта,
  50 страниц. Данные/HTML с документами/screenshots в Git не включаются.
- Export привязан к SHA-256 manifest/annotations и PNG, сохраняет reviewer,
  bbox и class flags. first_review не является итоговым QC, accepted_for_training
  всегда false; обновление канонического corpus отдельно после проверки.
  Браузер сохраняет черновик в localStorage, сообщает об ошибке сохранения;
  рекомендуется регулярно скачивать резервный JSON. Правка сбрасывает first_review.
- Проверки: 59 tests passed (0.49 s), ruff check/format и git diff --check — passed.
  Реальный browser smoke: Chromium headless через loopback HTTP — рисование,
  статус просмотра, out-of-bounds rejection, reload persistence, export, delete,
  restore и отклонение export с чужим source hash без изменения данных.
  Page errors отсутствуют. File:// запрещён политикой облачного Chromium;
  открытие file:// и Python server на Windows не проверялись.
- Python-валидатор проверил синтетический browser export: 50 страниц, 85 объектов,
  first_review на 1 странице. Это исключительно тест UI, не настоящая разметка;
  synthetic bbox не применялась к источнику и не включена в распространяемый HTML.
- S04 blocked: инструмент готов к первому просмотру 50 страниц, но реальная
  доразметка всего корпуса и независимый второй QC пока не завершены.


## S04 — 15.11.2026, получен пользовательский export редактора

- Загружен JSON пользователя (37 555 байт), SHA-256
  59df583ca8814f726709ef5b67fbdde4198a6cda27310264e36d51bf3e46da04.
  Данные файла трактовались как аннотации, не инструкции. Source hashes, страницы,
  PNG hashes, размеры и bbox проверены штатным валидатором. 50 страниц, 103 bbox:
  86 stamp / 17 signature; все 50 статусов unreviewed, first_review=0.
- scripts/apply_annotation_review.py применил правки в отдельный локальный
  mapo80-pilot50-review-v2; source сохранён. COCO и YOLO согласованы валидатором,
  stale previews удалены. Raw export и provenance только в artifacts/. Новый
  annotations SHA-256 302bf0745ba52705b385ee2677af40f8ec58eff950b8aa903bebca7f8e9c8d46.
  Агрегированный отчёт reports/data/pilot-review-application.json.
- Второй просмотр исходных страниц редактора 001, 022, 045 подтвердил рукописные
  подписи без signature bbox в пользовательском экспорте. Все три оставлены
  нерешёнными; proposals и картинки в artifacts/data-qc/mapo80-second-review-v1/.
  Полного второго QC всех 50 страниц не было; разметка не считается финальной.
- Подготовлен mapo80-review-resume.zip с уже загруженными пользовательскими
  правками. Генератор теперь сохраняет notes из first_review метаданных.
- Проверки: apply выполнен на настоящем export, validate_bundle exit 0,
  source annotations SHA-256 сохранился. Тест безопасного применения и отказа
  существующего output; pytest — 60 passed, ruff check/format и diff check passed.
- S04 blocked: осталось устранить пропуски и завершить второй просмотр пилота,
  далее разметить и проверить полный корпус ≥5 000 независимых страниц,
  подтвердить группировку/права и split. Обучение не запускалось.


## S04 — 15.11.2026, второй просмотр агентом

- Дополнительно просмотрены в исходном разрешении страницы редактора 007, 023,
  041, 044, 047; ранее просмотрены 001, 022, 045. На 023 и 041 видны подписи,
  отсутствующие в user export. В agent draft добавлены 6 bbox signature на пяти
  страницах: 001 (2), 022, 023, 041, 045. Это draft-разметка агента, не
  подтверждённый окончательный QC или автоматическое одобрение всех bbox.
- Локальная mapo80-pilot50-agent-v3: 109 объектов (86 stamp, 23 signature),
  все пользовательские объекты сохранены. Валидатор bundle exit 0; source
  review-v2 не менялся. Новый annotations SHA-256
  9a42ad91b03cbe86df2faa3526162bd8fbbb4841873e272f0319ee79b8c17218.
- 007, 044, 047 оставлены unresolved в заметках: печатное воспроизведение
  подписи/малые росчерки/подписи и обычный рукописный текст требуют различения.
  Не считать все рукописные элементы подписями, не закрывать reviewed_empty.
- Обнаружен и исправлен риск истории применения: при повторном apply старый
  review-source.json теперь сохраняется под review-history/<sha256>.json.
  Регрессионный тест подтверждает сохранение предыдущего export. Для реально
  созданного v3 исходный user export также отдельно сохранён в review-history.
- Приватный редактор продолжения artifacts/annotation-editor/mapo80-agent-v3.zip
  содержит пользовательские объекты, draft-добавления и нерешённые заметки.
  Старый JSON к новой версии не применяется напрямую. Координаты, изображения
  и user export не коммитятся; агрегат reports/data/pilot-agent-review-application.json.
- Проверки: .venv/bin/pytest -q — 60 passed, ruff check/format и diff check passed.
  S04 blocked: второй просмотр не завершён на всех 50 страницах; тем более
  не выполнен полный QC ≥5 000 оригиналов. Нового split и обучения нет.

## S04 — 15.11.2026, правило факсимиле и продолжение просмотра

- Пользователь согласовал включение визуальных подписей, включая факсимиле;
  обычный рукописный текст и галочки исключаются. Правило добавлено в docs/03
  и docs/08. Служебные штампы этим решением не согласованы.
- Просмотрены исходные страницы 015, 019, 024, 040, 044, 047 с текущими bbox.
  Для 007 учтён предыдущий исходный просмотр и новое правило. Добавлено 6
  draft signature bbox: 007 (1), 024 (2), 047 (3). На 047 крупный crop помог
  уточнить координаты без захвата соседнего обозначения смены в первую bbox.
  Никакие пользовательские объекты не удалялись.
- Рабочий bundle artifacts/data-import/mapo80-pilot50-agent-v4-adjusted:
  115 bbox (86 stamp/29 signature). Валидатор применения проверил bundle:
  50 images, 115 annotations, accepted_for_training=false. Annotations SHA-256
  896ad9001b20abdb48214b52d07badcbeb0a2dd6d414cbdafa6743160acbac9d.
  Предварительная v4 сохранена локально, но результат для продолжения — adjusted.
- 015 (малый росчерк/инициал) и 044 (малые штрихи около печати) остаются
  unresolved в заметках; не считаются reviewed_empty. 019/040 содержат обычный
  рукописный текст, его автоматически не добавляли в signature. Это частичный
  второй просмотр, не завершённый QC всех bbox на всех 50 страницах.
- Редактор продолжения artifacts/annotation-editor/mapo80-agent-v4.zip.
  Координаты, PNG, review exports только в gitignored artifacts/. В Git агрегат
  reports/data/pilot-agent-review-v4-application.json, правила и журнал.
  Проверки: валидатор реального нового bundle и git diff --check успешно;
  код не менялся, повторные unit-тесты не запускались.
- S04 blocked: оставшиеся спорные случаи, независимая приёмка draft рамок,
  полный QC корпуса минимум 5 000 оригиналов и group split ещё не выполнены.


## S04 — 15.11.2026, повторная проверка пользователя и очередь корпуса

- Получен новый export 40 849 байт; SHA-256
  81ab93687955064a005e0f42c179eb24c334b8a842af005846bd252fef613aab. Пользователь
  явно подтвердил повторную проверку и общую пригодность пилота. Все 50 полей
  статуса файла по-прежнему unreviewed; подтверждение чата записано отдельно в
  artifacts/annotation-batches/pilot-confirmation.json. Изменены страницы
  редактора 027, 028, 044, 050. Содержимое export трактовалось как данные.
- Проверены source hashes и геометрия. Применено отдельно в user-final-v5:
  119 объектов (87 stamp,32 signature), validator exit 0. Source версии сохранены.
  Итоговый annotations SHA-256 267f93b1bfdf736e429ffce4449bc96be9f2cb87572229bd9032f06026fa8ae7.
  Агрегат reports/data/pilot-user-repeat-review.json. Это не полный QC корпуса.
- Реализован prepare_annotation_batch.py: проверяет revision/ZIP hash и
  provenance пилота, исключает 50 исходных имён, планирует оставшиеся 6 233
  train-страницы в 63 рабочие партии (100/последняя33), seed42. Val/test не
  используются, model split не назначен. Дубли/связанные документы между
  партиями ещё возможны; контроль групп обязателен до разбиения модели.
- Созданы партия001 (100 images,144 stamp bbox) и партия002 (100 images,142
  stamp bbox), автономные editor ZIP и локальный progress.csv. Все новые
  страницы непросмотрены; остальные партии planned. Повторное применение
  export и автоматический сбор очереди ещё требуют дальнейшей интеграции.
- CLI партии002 проверен с финальной атомарной обёрткой; тесты планировщика
  проверяют полноту, отсутствие повторов/пилота, стабильный seed и неизвестные
  excluded pages. Pytest: 62 passed; ruff check/format и diff check passed.
- В Git docs/20, скрипт/тест и агрегаты; данные только в artifacts/. S04
  остаётся blocked по полному QC, правам и группам минимум 5 000 оригиналов.

## S04 — 15.11.2026, самостоятельная визуальная сортировка партии 001

- Пользователь поручил самостоятельный QC и принятие решений. Начат просмотр
  партии001: на контактных листах просмотрены первые 20 исходных изображений.
  На 004,010,011 видны кандидаты signature, отсутствующие в stamp-only labels.
  Требуются просмотр исходного разрешения и bbox; контактный лист не устанавливает
  полную семантику мелких объектов. Другие страницы не объявлены negatives.
- Приватный page-level triage.csv в artifacts/data-qc/batch001-agent/; агрегат
  reports/data/batch001-triage-summary.json явно имеет final_qc_pages=0 и
  accepted_for_training=false. Полный второй QC партии и корпуса не выполнен.
- Пустые исходные labels не могут подтвердить отсутствие обоих классов; для
  корпуса без signature labels требуется доразметка, а не только проверка схемы.

## S04 — 15.11.2026, партия001: исходные подписи и групповые кандидаты

- В полном разрешении просмотрены 004,010,011. Добавлены 2 draft signature bbox
  на 004/010 в отдельный artifacts/annotation-batches/batch-001-agent-v2.
  Рукописный текст письма на 010 не включался в bbox подписи. Закрывающие
  имена на 011 остаются спорными. FAXED на 004 требует отдельной оценки штампа.
- Применение и validator bundle успешно: 100 images,146 annotations,
  accepted_for_training=false. Source 144 bbox сохранён, экспорт/provenance
  и новый редактор только в artifacts/; полный QC страницы не объявлялся.
- Контактные листы просмотрены до 040 включительно. 036 и 038 визуально имеют
  тот же сертификат и подписи, но разные печати: кандидат одного background-group.
  022–025 имеют общий шаблон invoice: кандидат template-family, не доказательство
  одинаковых оригиналов. Model split не назначен. Ещё 16 страниц отмечены
  кандидатами для проверки подписей в исходном разрешении; bbox не угадывались
  по уменьшенным контактным листам.
- Приватный подробный findings-v2.json и aggregate reports/data/batch001-qc-progress.json.
  Final QC pages=0: первичная сортировка и две draft bbox не подменяют приёмку.
  Код не менялся; выполнены реальные apply/validator и git diff --check.

## S04 — 15.11.2026, партия001: сортировка 100 страниц и 51 новая рамка

- Завершена первичная сортировка всех 100 страниц на контактных листах.
  Дополнительно в исходном разрешении просмотрены 026–044,047,048,051–053,087
  для поиска подписей; просмотр подписей не означает полный QC печатей.
- Добавлена 51 draft signature bbox на 25 страницах, поверх ранее добавленных
  двух. Отдельный bundle artifacts/annotation-batches/batch-001-agent-v3:
  100 images,197 annotations (144 stamp,53 signature). Исходные stamp bbox
  сохранены; даты, рукописные пояснения и печатные имена не размечались как
  подписи. Малый знак (P) на 035 оставлен спорным без новой bbox.
- Рамки проверены на локальных изображениях с наложением; apply и повторный
  sealsign data validate успешны. Annotations SHA-256
  faced727bf0a166c0d833706cc61aa7049900952c38c753dfd152e3a23618253.
  Источники и версии сохранены, accepted_for_training=false; final_qc_pages=0.
- Приватные first-pass-v3.json, findings-v3.json, листы с рамками — в
  artifacts/data-qc/batch001-agent/. Автономный редактор с правками:
  artifacts/annotation-editor/batch001-agent-v3.zip. В Git только агрегат.
- Выявлены ещё кандидаты групп: 045/096 (одно письмо),046/099 (один бюллетень),
  051/052 (разные последовательные страницы договора),053/087 (персонализированные
  письма общего шаблона),064/085 (общий шаблон сертификата, разные получатели).
  Первые две пары требуют сравнения исходного разрешения; не объявлены точными
  дублями. Вместе с предыдущими — семь кандидатных наборов, model split не задан.
- Следующий шаг: рамки кандидатов signature на оставшихся страницах 054–098,
  проверка полноты stamp, разбор спорных отметок и второй QC. Полный S04 всё ещё
  не завершён: нужны принятые два класса на ≥5 000 независимых оригиналов,
  проверка прав компонентов и group split. Код не менялся; unit-тесты повторно
  не запускались, реальный bundle validator и git diff --check прошли.

## S04 — 15.11.2026, партия001: оставшиеся кандидаты подписей и пропуски печатей

- Визуально проверены ещё 26 страниц-кандидатов 054–064,066,067,070–073,
  082–086,091,093,095,098 с учётом исходного размера. Для крупных 083/086/093
  проверены также crops в нативном разрешении; рамки пересчитаны из координат
  обзорного изображения в исходные пиксели. Проверены листы наложений.
- Добавлены 44 draft signature bbox на 25 из этих страниц. На 072 мелкая
  отметка остаётся спорной. Повторно рассмотрена 011: рукописные закрывающие
  имена после Sincerely включены как подпись по роли подписанта; адрес, тело
  письма и архивные пометки исключены. Итого +45 signature за этот checkpoint.
  На 055 рамка подписи нотариуса уточнена, чтобы исключить дату под росчерком.
- Дополнительно просмотрены наложения обоих классов на 026–040. Добавлены три
  пропущенные draft stamp bbox: 026 частичный нотариальный оттиск у края,
  029 оттиск на сгибе,040 прямоугольная печать организации. Служебная отметка
  с датой на 030, серые эмблемы/оттиски на 027, разделение наложенных оттисков
  на 026 и другие неоднозначности записаны в notes; приёмка не объявлена.
- Отдельный artifacts/annotation-batches/batch-001-agent-v4 получен из v3,
  история прежнего review сохранена. 100 images,245 annotations:147 stamp,
  98 signature. Apply и повторный sealsign data validate успешны; annotations
  SHA-256 60fbc3ee61687558d9ced85f4411eb36f026cc70ce6fd5a2d6578650fb11ab09.
  First_review_pages=0,final_qc_pages=0,accepted_for_training=false: просмотр
  кандидатов и наложений не подтверждает полноту каждого объекта всей партии.
- Приватные first-pass-v4.json, findings-v4.json, новые рамки и визуальные
  доказательства в artifacts/data-qc/batch001-agent/. Редактор продолжения:
  artifacts/annotation-editor/batch001-agent-v4.zip. В Git только агрегат и журнал.
- Следующий шаг — проверка остальных stamp bbox/пропусков и спорных объектов,
  затем полный повторный QC. S04 остаётся незавершённым: объём ≥5 000 независимых
  оригиналов, права компонентов и group split ещё требуют доказательств.
  Код не менялся; проверены реальный bundle и git diff --check, unit-тесты
  повторно не запускались.

## S04 — 15.11.2026, партия001: полный просмотр наложений, первый просмотр 67 страниц

- На этом checkpoint просмотрены наложения обоих классов на 001–025 и 041–100;
  вместе с предыдущими 026–040 охвачены все 100 страниц. Для крупных страниц
  использовался обзор до 1000 px и целевые нативные crops (в том числе 094 для
  слабой печати). Это не утверждение просмотра каждого нативного пикселя.
- В рамках делегированного пользователем самостоятельного QC принято единое
  правило включения служебных оттисков: received/faxed/date/attested и почтовые
  штампы входят в stamp; логотипы, печатные реквизиты и архивные ID исключены.
  Правило и основание записаны в docs/03 и docs/08. Старый пилот нужно сверить
  по обновлённому правилу; неоднозначные инициалы/эмблемы пока disputed.
- Добавлены 10 stamp bbox (004,030,035,044,055,060,061,063 и две на 072).
  На 023 одна исходная объединённая bbox разделена на два отдельных оттиска
  (жёлтый рисунок/текст и чёрный телефон), net +1. Добавлены две пропущенные
  signature:012 в поле подписи карточки и 068 в поле составителя формы.
  Нативные crops проверены. На 041/044/053/098 уточнены signature bbox для
  исключения соседних печатных имён/закрывающего слова письма.
- Для 67 страниц записан first_review с обеими checked flags, включая 16 пустых
  страниц после визуального просмотра. Остальные 33 страницы unreviewed.
  Канонический manifest сохраняет общий unreviewed до второго QC, а первый
  просмотр записан отдельно; final_qc_pages=0,accepted_for_training=false.
- На 074–081 видны поворот/шум и прямоугольные края фрагментов печатей: восемь
  quarantine candidates. Их исходные пути/хеши и причины сохранены отдельно в
  artifacts/data-qc/batch001-agent/quarantine-candidates-v5.json. Независимые
  оригиналы для этих файлов не доказаны; их нельзя засчитывать в минимум 5000.
  Файлы и исходные bbox сохранены, автоматического удаления из bundle нет.
- Отдельный artifacts/annotation-batches/batch-001-agent-v5:100 images,
  258 annotations (158 stamp/100 signature). Apply и повторный bundle validator
  прошли; annotations SHA-256
  db008e2117803c4b2cb2b898dbb3d29e189338c8e657521d4ead14fbc7053c34.
  Новый редактор artifacts/annotation-editor/batch001-agent-v5.zip. Его UI
  стартует unreviewed; 67 записей первого просмотра находятся в bundle, их
  нельзя считать восстановленными редактором автоматически. Progress CSV обновлён.
- В Git только правила, агрегат и журнал. Код не менялся; unit-тесты повторно
  не запускались. Выполнены apply, реальный validator и git diff --check.
  Дальше: adjudication оставшихся 33 страниц, второй QC, анализ происхождения
  аугментаций/групп и проверка достаточного корпуса/прав. S04 ещё не завершён.

## S04 — 15.11.2026, партия001: adjudication и проверка происхождения

- Повторно рассмотрены 25 спорных страниц вне восьми quarantine candidates,
  проверены увеличенные фрагменты датирующих/нотариальных оттисков и росчерков.
  На 24 разрешены вопросы первого просмотра. На 072 мелкие слабые штрихи
  остаются неразличимыми; страница удерживается, не объявлена negative.
- Зафиксировано правило подписных парафов по роли заверения (docs/03,docs/08),
  без включения обычных рукописных заметок. Добавлены 6 signature bbox:
  027 параф сертификата,029 два подписных имени на поле договора,051/052 по
  одному малому парафу,059 авторизующий росчерк над печатью организации.
- Добавлены 8 stamp bbox:017 служебный блок клиппинга,027 печать офиса и дата,
  031/032 по два оттиска даты/нотариальной надписи,040 слабый овальный оттиск.
  На026 исходная общая bbox двух наложенных печатей разделена (net +1), на082
  bbox перенесена на полный слабый оттиск без рукописного Cancelled. Логотипы,
  декоративные эмблемы, даты от руки и заметки о копиях не добавлялись.
- V6 bundle получен отдельно от v5 с сохранением истории:100 images,
  273 annotations (167 stamp/106 signature),91 first_review,16 first-review empty,
  1 hold и8 quarantine candidates. Final QC=0,accepted_for_training=false.
  Apply и повторный validator успешны; annotations SHA-256
  d15643e609f7962bffe8b6cdaea16aed0476dcd79b8c07324d71b0749d99f6ea.
  Артефакты: first-pass-v6.json,changes-v6.json,findings-v6.json,листы с рамками
  под artifacts/data-qc/batch001-agent/; редактор batch001-agent-v6.zip.
- Проверены семь групп внутри партии. 036/038,045/096,046/099,064/085 имеют
  одинаковый исходный документ/фон с разными оттисками или масштабом. 051/052
  разные страницы одного договора;022–025 и053/087 — семьи шаблонов с разным
  содержанием. Private group-review-v6.json хранит page_id,тип и объяснение;
  в канонический manifest и model split группы пока не применены. Для91 файлов
  первого просмотра верхняя граница независимых фонов уже87, не принятые87.
- Инвентаризирован Stampa по именам архивов:369 train,46 val,46 test; всего461.
  Нового визуального просмотра val/test не было. Все8 просмотренных файлов этой
  семьи в партии001 имеют признаки поворота/шума и фрагментов печатей. Семья
  удерживается вне подсчёта независимых оригиналов до проверки provenance;
  это не классификация всех461 как синтетических. Вне семьи7393 файлов до
  глобальной дедупликации, их независимость тоже не доказана. Агрегат
  reports/data/stampa-originality-review.json, данные/пути только в artifacts/.
- Код не менялся; unit-тесты повторно не запускались. Проверены apply, реальный
  validator, сборка редактора и git diff --check. Следующий приоритет — аудит
  исходных фонов всего корпуса и второй QC, чтобы не доразмечать копии в счёт
  требования5000. S04 остаётся незавершённым по полному QC, правам и group split.

## S04 — 15.11.2026, полный аудит кандидатов повторного фона

- Реализован scripts/audit_backgrounds.py: безопасное чтение ZIP, исходных bbox,
  маска stamp, позиционные tile hashes и сравнение незакрытого фона по grayscale
  и тёмным штрихам. Все параметры и входные SHA-256 записаны. Скрипт не изменяет
  labels/manifest/split, не считает кандидаты принятыми оригиналами. Результат
  сохраняется через временный каталог, существующий output запрещён.
- Полностью обработаны 7854 файла трёх ZIP фиксированной ревизии.7666 страниц
  имеют≥4 активных блока;18414 предварительных пар,16776 кандидатов после
  сравнения,5514 между исходными ZIP. Частых исключённых buckets=0. CSV полный,
  без прежнего ограничения 1000 пар; файлы/пути только в gitignored artifacts/.
- Кандидатный граф:4040 файлов,583 компоненты. Если все компоненты окажутся
  одним оригиналом каждая, останется 4397 фонов до прочих исключений. Это только
  условный сценарий: граф не проверен, ложное ребро может объединить разные
  документы, пропуски также возможны. Реальное число оригиналов не объявлено.
- Алгоритм восстановил 4/4 ранее проверенных train-пар партии 001 без изменения
  критериев. Дополнительно просмотрены 8 train/train пар из разных компонент,
  seed42: во всех совпали текст, индивидуальные детали/подписи при разных
  печатях или масштабе. Журнал с решениями и изображениями приватный. Результат
  относится только к 8 парам; не объявлен precision/recall полного корпуса.
- Первая реализация сравнения Python-циклом завершила полный прогон до попытки
  её остановки; данные сохранены как background-audit-v1. Ускоренная ImageChops
  реализация повторена в background-audit-v2:полные CSV и inventory побайтово
  равны, report равен. SHA-256 CSV
  dc47ed4cfdc5543cb5ace56edb49ab8e7338c063288a8ea8558d274ec0633f4e.
  Пороги после просмотра train-пар не менялись; модель/test tuning отсутствуют.
- В Git скрипт,6 тестов реальных рисков,docs/21 и агрегаты background-*.
  Pytest 68 passed,ruff check/format и git diff --check успешны. Проверенная команда
  полного прогона приведена в docs/21. Веса/обучение не создавались.
- S04 не завершён: нужны проверенные группы, доказательства≥5000 независимых
  оригиналов и прав компонентов, полный двухклассовый QC и group split. Аудит
  повторных фонов приоритетнее автоматического переноса очереди на все файлы.

## S04 — 15.11.2026, визуальное разрешение шести крупнейших групп

- Подготовлена стабильная очередь 583 кандидатных компонент по полному CSV,
  размеры по убыванию, tie-break по SHA-256 отсортированных членов. Просмотрены
  все 130 файлов первых шести компонент:32,21,21,19,19,18. Обзорные листы,
  увеличенные поля адресатов/дат, референсные изображения приватные.
- Крупнейшая компонента разделена на два оригинала общего шаблона (21/11 файлов)
  по адресату, комнате, обращению и архивному номеру. Остальные пять компонент
  соответствуют пяти исходным документам. Итого семь визуально различных фонов,
  123 дополнительных варианта; все семь групп пересекают upstream ZIP/split.
  Из 1272 кандидатных рёбер внутри подмножества 130 соединяют разные оригиналы.
  Не экстраполировать этот результат на остальные 577 компонент или весь корпус.
- Исходные val/test визуально просмотрены исключительно для идентичности/утечки;
  новой bbox-разметки и выбора параметров детектора нет. Поиск фонов не перенастроен.
- Реализован validate_background_review.py: привязка review к трём source hashes,
  проверка graph/inventory, исчерпывающей partition каждой рассмотренной
  компоненты, запрет повторных/чужих/пропущенных членов, обязательные reviewer
  и evidence. Валидатор проверяет структуру решения, не истинность его содержания,
  не выдаёт final QC или accepted_for_training и не меняет model split.
- Реальный review-v2.json успешно валидирован; SHA-256
  5797cce078063ea69996acef8fc9d66fdd85a1675e3687364a9c64252deb15fc.
  Приватный background-registry-v1.json различает background_id и предлагаемую
  leakage family; два письма общего шаблона имеют разные background_id.
  В canonical manifest ничего не применено. Артефакты в
  artifacts/data-qc/background-group-review-v1/, прежний review трёх компонент
  сохранён отдельно. В Git агрегат reports/data/background-group-review.json.
- Семь новых тестов проверяют false-bridge split, неполное покрытие, повторные/
  чужие назначения, повтор компоненты, отсутствие evidence и изменение source.
  Полный pytest75 passed,ruff check/format и git diff --check прошли.
- S04 продолжается: ещё 577 кандидатных компонент, непойманные дубли/аугментации,
  права/оригинальность, полный двухклассовый QC и group split. Нельзя объявлять
  5000 оригиналов по числу файлов либо по неразрешённому графу кандидатов.

## S04 — 15.11.2026, расширение проверки до 18 компонент/340 файлов

- В стабильном порядке очереди просмотрены все члены компонент 007–018:
  шесть по 18 и шесть по 17 файлов, всего 210 новых файлов. Помимо обзорных листов
  просмотрены референсы с читаемыми полями; для спорной даты дипломатического
  письма увеличены квадратная и портретная версии. Различие формы цифры при
  уменьшении не является другой датой. Все 12 компонент имеют по одному фону.
- По индивидуальным полям сопоставлены датированные письма, научная статья,
  заполненная заявка, страница устава, свидетельство регистрации и официальные
  сообщения. Сходство заголовка само по себе не служило основанием объединения.
  Отдельная идентичность двух писем первой компоненты сохранена.
- Новый review-v4.json успешно прошёл validate_background_review.py:
  18 рассмотренных компонент,340 файлов,19 фоновых групп,321 дополнительный
  вариант,17 групп пересекают исходные архивы/split. Рассмотрены 2864 кандидатных
  ребра внутри подмножества;130 между двумя разными оригиналами общей семьи.
  Эти величины относятся к выбранным крупным группам, не ко всему корпусу.
- SHA-256 текущего журнала
  da314a87207c5cb670fde64d18bc896917c41b4546d6efa8ce8439f0ad20c809.
  Прежние review.json,review-v2.json,review-v3.json сохранены. Новый приватный
  background-registry-v2.json и queue-progress-v1.json с хешами исходной очереди
  и review фиксируют продолжение с позиции 19. Артефакты под
  artifacts/data-qc/background-group-review-v1/. В Git только агрегат и журнал.
- Исходные val/test просмотрены для идентичности/утечки. Рамки, параметры поиска
  и модель не менялись; accepted_for_training=false,canonical manifest/split
  не изменены. Код не менялся, поэтому unit-тесты повторно не запускались;
  выполнены реальная валидация нового журнала и git diff --check.
- S04 не завершён: ещё 565 кандидатных компонент, проверка происхождения/прав,
  двухклассовый QC и group split. Минимум 5000 оригиналов не подтверждён.

## S04 — 15.11.2026, расширение проверки до 30 компонент/526 файлов

- Просмотрены все186 файлов компонент019–030 по обзорным листам и референсам
  с индивидуальными полями. В каждой новой группе один визуально совпадающий
  фон при разных наложенных печатях/пропорциях. Скриншот договора не принят
  автоматически: происхождение и права остаются отдельными проверками.
- review-v5.json прошёл валидатор:30 компонент,526 файлов,31 фоновая группа,
  495 дополнительных вариантов;27 групп пересекают upstream ZIP/split.
  Рассмотрены4189 кандидатных рёбер,130 между разными оригиналами первой семьи.
- SHA-256 журнала:
  86be34a37f5d2f6d69ac7d7c4dc9b3a2f6c868395600f3a43b085f09d41b7554.
  Приватные background-registry-v3.json и queue-progress-v2.json фиксируют
  следующую позицию31. Предыдущие журналы сохранены; в Git только агрегат/доки.
- Проверены реальный журнал и git diff --check. Код не менялся, unit-тесты
  не повторялись. Рамки/модель не настраивались по upstream val/test;
  accepted_for_training=false,canonical manifest/split не менялись.
- S04 открыт:553 кандидатных компоненты, возможные непойманные совпадения,
  происхождение/права, двухклассовый QC и group split.5000 оригиналов не доказаны.

## S04 — 15.11.2026, расширение проверки до 42 компонент/699 файлов

- Просмотрены все 173 файла компонент 031–042: обзорные листы всех членов
  и увеличенные референсы для мелких полей. Совпадение установлено по содержимому,
  заполнению и деталям скана; в каждой новой компоненте один фон.
- review-v6.json прошёл валидатор: 42 компоненты, 699 файлов, 43 фоновые группы,
  656 дополнительных вариантов; 39 групп пересекают upstream ZIP/split.
  Рассмотрены 5237 кандидатных рёбер, 130 между разными оригиналами первой семьи.
- SHA-256 журнала:
  fc510eb34888edcb6b75c53fe5b743322cc1efd81e6cf44ab72816dbcb1f05ec.
  background-registry-v4.json и queue-progress-v3.json сохраняют накопленные
  решения и продолжение с позиции 43. Прежние версии сохранены в artifacts/.
- Проверены реальный журнал и git diff --check. Код не менялся, unit-тесты
  не повторялись; канонические группы, разметка и split не изменены,
  accepted_for_training=false. Просмотр upstream val/test только для утечки.
- S04 открыт: 541 кандидатная компонента, возможные пропущенные совпадения,
  происхождение/права, полный двухклассовый QC и group split; минимум 5000
  оригиналов пока не доказан.

## S04 — 15.11.2026, расширение проверки до 54 компонент/862 файлов

- Просмотрены все 163 файла компонент 043–054 на обзорных листах всех членов.
  Совпадают индивидуальное содержание, заполненные поля, подписи/заметки и
  детали скана. Во всех 12 новых компонентах один фон; новых false-bridge split нет.
- review-v7.json прошёл validate_background_review.py: 54 компоненты, 862 файла,
  55 фоновых групп, 807 дополнительных вариантов; 51 группа пересекает исходные
  архивы. В просмотренном подмножестве 6224 кандидатных ребра, 130 между разными
  оригиналами первой семьи. Глобальный объём этим не установлен.
- SHA-256 журнала:
  7686f7a545fedc47b8da29a26f5238fbc2696b54c9e69770fae5184d9b8b1ab8.
  Приватные background-registry-v5.json и queue-progress-v4.json сохраняют
  накопленные решения и следующую позицию 55. Прежние версии сохранены.
- Реальная валидация журнала и git diff --check прошли. Код не менялся,
  unit-тесты не повторялись. Просмотр upstream val/test только для идентичности;
  параметры модели/рамки, canonical manifest и split не менялись. Приёмка false.
- S04 открыт: 529 кандидатных компонент, возможные пропущенные совпадения,
  происхождение/права, полный двухклассовый QC, group split и минимум 5000
  независимых оригиналов ещё требуют подтверждения.

## S04 — 15.11.2026, расширение проверки до 66 компонент/1018 файлов

- Просмотрены все 156 файлов компонент 055–066 на обзорных листах всех членов.
  Каждая новая компонента соответствует одному визуально совпадающему фону.
- review-v8.json прошёл валидатор: 66 компонент, 1018 файлов, 67 фоновых групп,
  951 дополнительный вариант; 61 группа пересекает upstream архивы.
  Рассмотрены 7127 кандидатных рёбер, 130 между разными оригиналами первой семьи.
- SHA-256 журнала:
  0d990778b3549c6eddf485af6635c3a866f08940ce6a644ac7a8f9cb464437cb.
  Приватные background-registry-v6.json и queue-progress-v5.json фиксируют
  продолжение с позиции 67. Предыдущие версии сохранены.
- По просьбе пользователя введён явный прогресс очереди дублей: 11,32%
  (66/583), ранее 9,26% (54/583). Это не процент готовности всего S04:
  объём добора, прав и полного QC ещё не установлен, общий процент null.
- Реальный журнал и git diff --check проверены. Код не менялся, unit-тесты
  не повторялись; модель/рамки по upstream val/test не настраивались,
  canonical manifest/split не менялись, accepted_for_training=false.
- S04 открыт: ещё 517 кандидатных компонент, возможные непойманные совпадения,
  происхождение/права, двухклассовый QC, group split и подтверждение 5000 оригиналов.

## S04 — 15.11.2026, расширение проверки до 78 компонент/1164 файлов

- Просмотрены все 146 файлов компонент 067–078 по обзорным листам всех членов.
  В каждой из 12 новых компонент один фон по индивидуальному содержанию,
  заполнению, подписям и деталям скана; новых false-bridge split нет.
- review-v9.json прошёл валидатор: 78 компонент, 1164 файла, 79 фоновых групп,
  1085 дополнительных вариантов; 72 группы пересекают upstream архивы.
  Рассмотрены 7907 кандидатных рёбер, 130 между разными оригиналами первой семьи.
- SHA-256 журнала:
  9401fa50ea3b7611c3c55bf7ac30143ec8189274711b60ede8088c8883fe75a7.
  Приватные background-registry-v7.json и queue-progress-v6.json сохраняют
  решения и продолжение с позиции 79; предыдущие версии сохранены.
- Проверка фиксированной очереди: 13,38% (78/583), ранее 11,32% (66/583).
  Это не процент всего S04, для которого объём добора/прав/разметки неизвестен.
- Проверены реальный журнал и git diff --check. Код не менялся, unit-тесты
  не повторялись. Upstream val/test просмотрены только для идентичности;
  canonical manifest/split не менялись, accepted_for_training=false.
- S04 открыт: ещё 505 кандидатных компонент, возможные пропущенные совпадения,
  происхождение/права, полный двухклассовый QC, group split и 5000 оригиналов.

## S04 — 15.11.2026, проверка до 99 компонент

- Просмотрены компоненты 079–099, всего 243 файла; review-v11.json прошёл
  структурный валидатор. Накоплено 1407 файлов, 100 фоновых групп и 1307
  дополнительных вариантов; 93 группы пересекают исходные архивы.
- SHA-256 журнала: b895b1acbece22d6be17781087d6b539aa65c94d4607cf2eac766b9dac01b84f.
  Следующая позиция — 100, осталось 484 компоненты.
- Прогресс очереди: 16,98% (99/583), ранее 13,38% (78/583). Общий процент
  S04 не установлен. Приёмка, canonical manifest и split не изменены.
- S04 открыт: происхождение и права, полный QC двух классов, group split и
  минимум 5000 независимых оригиналов остаются неподтверждёнными.

## S04 — 15.11.2026, исправление evidence и проверка до 105 компонент

- Исправлены сдвинутые текстовые описания компонент 079–099 по обзорным листам;
  состав групп не менялся. Структурный валидатор не проверяет истинность текста.
  Прежние журналы сохранены; актуальный review-v12.json.
- Просмотрены все 66 файлов компонент 100–105; журнал прошёл валидатор.
  Накоплено 1473 файла, 106 фоновых групп, 1367 дополнительных вариантов;
  99 групп пересекают архивы. Осталось 478 компонент.
- SHA-256 review-v12.json:
  97138ac12f1b5604dad41e345d1399204f10f94d2d74492f676b1a4fc90743cb.
  background-registry-v10.json и queue-progress-v9.json указывают позицию 106.
- Прогресс очереди 18,01% (105/583), ранее 16,98%. Общий процент S04
  неизвестен; accepted_for_training=false, canonical manifest/split не менялись.
- Проверены валидатор журнала и git diff --check; код не менялся, unit-тесты
  не повторялись. Права, происхождение, полный QC и 5000 оригиналов не доказаны.

## S04 — 15.11.2026, проверка до 117 компонент

- Просмотрены все 132 файла компонент 106–117; review-v13.json прошёл
  структурную проверку. Накоплено 1605 файлов, 118 фоновых групп и 1487
  дополнительных вариантов; 111 групп пересекают архивы.
- SHA-256 журнала:
  026e71dc7945a36788ebbc150c6f76205517fe6c40e76b0a605dc8b7f8981e21.
  Приватные registry-v11 и queue-progress-v10 указывают позицию 118.
- Очередь проверена на 20,07% (117/583), ранее 18,01%; это не готовность S04.
  Остаются 466 компонент, права, происхождение, полный QC и group split.
  Минимум 5000 оригиналов не доказан; данные не приняты для обучения.
- Код не изменялся; проверены журнал и git diff --check.

## S04 — 15.11.2026, проверка до 129 компонент

- Просмотрены все 127 файлов компонент 118–129; review-v14.json прошёл
  структурную проверку. Накоплено 1732 файла, 130 фоновых групп, 1602
  дополнительных варианта; 122 группы пересекают исходные архивы.
- SHA-256 журнала:
  a534b83e8d460fc3271867b157fd02f63fe386389007667e55b7c73781e2342b.
  Приватные registry-v12 и queue-progress-v11 указывают позицию 130.
- Прогресс очереди 22,13% (129/583), ранее 20,07%; осталось 454 компоненты.
  Это не готовность всего S04: права, происхождение, полный двухклассовый QC,
  group split и минимум 5000 независимых страниц ещё не подтверждены.
- Код не менялся; проверены реальный журнал и git diff --check. Данные не
  приняты для обучения, canonical manifest и split не изменены.

## S04 — 15.11.2026, проверка до 141 компоненты

- Просмотрены 120 файлов компонент 130–141; review-v15.json прошёл структурную
  проверку. Накоплено 1852 файла, 142 фоновые группы, 1710 дополнительных
  вариантов; 132 группы пересекают исходные архивы.
- SHA-256 журнала:
  c36f0e82f71d8c2788a91e1b3324d8f22452e78b3f707656f32376f04ce474cd.
  Приватные registry-v13 и queue-progress-v12 указывают позицию 142.
- Прогресс очереди 24,19% (141/583), ранее 22,13%; остаются 442 компоненты.
  Общая готовность S04 неизвестна. Права, происхождение, полный двухклассовый
  QC, group split и минимум 5000 независимых страниц ещё не подтверждены.
- Код не менялся; проверены реальный журнал и git diff --check. Приёмка данных,
  canonical manifest и split не изменены.

## S04 — 15.11.2026, проверка до 153 компонент

- Просмотрены все 120 файлов компонент 142–153; review-v16.json прошёл
  структурную проверку. Накоплено 1972 файла, 154 фоновые группы и 1818
  дополнительных вариантов; 142 группы пересекают исходные архивы.
- SHA-256 журнала:
  f7114cbfc2ab90b009c6090306e496da328d3672e401efe5430111724798cb56.
  Приватные registry-v14 и queue-progress-v13 указывают позицию 154.
- Прогресс очереди 26,24% (153/583), ранее 24,19%; осталось 430 компонент.
  Общая готовность S04 неизвестна. Права, происхождение, полный QC двух классов,
  group split и минимум 5000 независимых страниц не подтверждены.
- Код не менялся; проверены реальный журнал и git diff --check. Приёмка данных,
  canonical manifest и split не изменены.

## S04 — 15.11.2026, проверка до 165 компонент

- Просмотрены все 119 файлов компонент 154–165; review-v17.json прошёл
  структурную проверку. Накоплено 2091 файл, 166 фоновых групп, 1925
  дополнительных вариантов; 153 группы пересекают исходные архивы.
- Письма для Род-Айленда и Мэриленда в разных компонентах различаются по
  тексту; общий шаблон отмечен для будущей проверки семьи при split.
- SHA-256 журнала:
  db0de18a053edafbcb4bafd4bb8a91c1a354ccfd09085bcd9b0fa76314fa7835.
  Приватные registry-v15 и queue-progress-v14 указывают позицию 166.
- Прогресс очереди 28,30% (165/583), ранее 26,24%; осталось 418 компонент.
  Общая готовность S04 неизвестна. Права, происхождение, полный QC двух классов,
  group split и минимум 5000 независимых страниц не подтверждены.
- Код не менялся; проверены реальный журнал и git diff --check. Приёмка данных,
  canonical manifest и split не изменены.

## S04 — 15.11.2026, проверка до 177 компонент

- Просмотрены все 108 файлов компонент 166–177; review-v18.json прошёл
  структурную проверку. Накоплено 2199 файлов, 178 фоновых групп и 2021
  дополнительный вариант; 163 группы пересекают исходные архивы.
- SHA-256 журнала:
  d58c5535807a540f0018a18c976a2bf1ff3eacbe3a7ee99404e7005cc5821e78.
  Приватные registry-v16 и queue-progress-v15 указывают позицию 178.
- Прогресс очереди 30,36% (177/583), ранее 28,30%; осталось 406 компонент.
  Общая готовность S04 неизвестна. Права, происхождение, полный QC двух классов,
  group split и минимум 5000 независимых страниц не подтверждены.
- Код не менялся; проверены реальный журнал и git diff --check. Приёмка данных,
  canonical manifest и split не изменены.

## S04 — 15.11.2026, проверка до 189 компонент

- Просмотрены все 108 файлов компонент 178–189; review-v19.json прошёл
  структурную проверку. Накоплено 2307 файлов, 190 внутриграфовых фоновых групп,
  2117 дополнительных вариантов; 172 группы пересекают исходные архивы.
- Обнаружено визуальное сходство компоненты 186 с ранее проверенной 35; связь
  требует проверки перед подсчётом оригиналов и split. Два письма одному
  адресату с разными подписантами учтены как разные документы.
- SHA-256 журнала:
  1ef41853788e88b9647408c44cace3b8410823cc6aa4766e27f96faa0ce97c51.
  Приватные registry-v17 и queue-progress-v16 указывают позицию 190.
- Прогресс очереди 32,42% (189/583), ранее 30,36%; осталось 394 компоненты.
  Общая готовность S04 неизвестна. Права, происхождение, полный QC двух классов,
  group split и минимум 5000 независимых страниц не подтверждены.
- Код не менялся; проверены реальный журнал и git diff --check. Приёмка данных,
  canonical manifest и split не изменены.

## S04 — 15.11.2026, проверка до 201 компоненты

- Просмотрены все 108 файлов компонент 190–201; review-v20.json прошёл
  структурную проверку. Накоплено 2415 файлов, 202 внутриграфовые группы и
  2213 дополнительных вариантов внутри компонент; 182 группы пересекают ZIP.
- Увеличенные референсы подтвердили один документ в компонентах 35 и 186:
  одинаковые дата, адресат, текст и подпись, разные факс-заголовки и архивные
  номера. Пары 157/197 и 87/199 требуют проверки. Приватный cross-component-
  links-v1.json сохраняет идентификаторы; canonical группы не менялись.
  Среди 202 внутриграфовых групп не более 201 разных фонов по этой связи;
  возможны другие совпадения и ошибки, глобальный объём не установлен.
- SHA-256 журнала:
  189445ff25721d52284c998c52190ddfcdea0b7452c9e5784265c9b8bae04283.
  Приватные registry-v18 и queue-progress-v17 указывают позицию 202.
- Прогресс очереди 34,48% (201/583), ранее 32,42%; осталось 382 компоненты.
  Общая готовность S04 неизвестна; права, происхождение, полный QC, split и
  минимум 5000 независимых страниц не подтверждены. Данные не приняты.
- Код не менялся; проверены реальный журнал и git diff --check.

## S04 — 15.11.2026, проверка до 207 компонент

- Просмотрены 54 файла компонент 202–207; review-v21.json прошёл структурную
  проверку. Накоплено 2469 файлов, 208 внутриграфовых групп и 2261 дополнительный
  вариант; 188 групп пересекают исходные архивы.
- Увеличенные изображения подтвердили межкомпонентные совпадения 157/197 и
  87/199. Вместе с 35/186 это три связи, не найденные графом. Подробности в
  приватном cross-component-links-v2.json; canonical группы не менялись.
- Компонента 208 содержит разные изображения на общем искусственном фоне и
  оставлена открытой для разбиения; следующая позиция очереди — 208.
- SHA-256 журнала:
  d59efc9ebdcbb934b5eecf421a50cc788bfc70087a5702be2e0fd83322cfe31c.
  Приватные registry-v19 и queue-progress-v18 сохраняют checkpoint.
- Прогресс очереди 35,51% (207/583), ранее 34,48%; осталось 376 компонент.
  Общая готовность S04 неизвестна; права, происхождение, полный QC, split и
  минимум 5000 независимых страниц не подтверждены. Данные не приняты.
- Код не менялся; проверены реальный журнал и git diff --check.

## S04 — 15.11.2026, группа 208 и проверка до позиции 213

- Девять изображений компоненты 208 просмотрены увеличенно. Различные фрагменты,
  почти пустые листы, поворот и шум не позволяют надёжно определить исходные
  страницы; компонента удержана и не засчитана как рассмотренная.
- Проверены 40 файлов компонент 209–213; review-v22.json прошёл структурную
  проверку. Накоплено 212 компонент, 2509 файлов, 213 внутриграфовых групп и
  2296 дополнительных вариантов. Общий шаблон дипломов 207 и 210 отмечен;
  получатели и регистрационные данные различаются.
- SHA-256 журнала:
  ee91b2c532ad386a952ebdf12f1014ac63276548b3ca292172f2fd1c95b7153f.
  Приватные registry-v20 и queue-progress-v19 фиксируют удержанную 208 и
  следующую непросмотренную позицию 214. Предыдущие версии сохранены.
- Прогресс очереди 36,36% (212/583), ранее 35,51%; осталось 371, включая 208.
  Готовность S04 неизвестна; права, происхождение, QC, split и 5000 оригиналов
  не подтверждены. Код не менялся; журнал и git diff --check проверены.

- Продолжена визуальная проверка групп фонов 214–225: 12 компонент и 96 файлов,
  по одной группе фона на компоненту. review-v23 прошёл структурную проверку;
  приватные registry-v21 и queue-progress-v20 сохранены. Группа 208 удерживается.
- Прогресс очереди: 38,42% (224/583), осталось 359, следующая позиция 226;
  это не процент готовности S04. Количество независимых оригиналов и права
  источников ещё не подтверждены, приёмка и split не выполнялись.

- Проверены группы 226–237: 12 компонент и 96 файлов, по одному фону на
  компоненту. Сертификаты 209 и 233 используют общий шаблон при разных
  учреждениях. review-v24 структурно проверен; приватные registry-v22 и
  queue-progress-v21 обновлены.
- Очередь проверена на 40,48% (236/583), осталось 347, включая удержанную 208;
  следующая непросмотренная позиция 238. Это не процент готовности S04.

- Проверены группы 238–249: 12 компонент и 96 файлов, по одному фону на
  компоненту. review-v25 структурно проверен; приватные registry-v23 и
  queue-progress-v22 обновлены.
- Очередь проверена на 42,54% (248/583), осталось 335, включая удержанную 208;
  следующая непросмотренная позиция 250. Это не процент готовности S04.

- Проверены группы 250–261: 12 компонент и 88 файлов, по одному фону на
  компоненту. Диплом 255 имеет общий шаблон с 207, 210 и 224 при другом
  получателе. review-v26 структурно проверен; приватные registry-v24 и
  queue-progress-v23 обновлены.
- Очередь проверена на 44,60% (260/583), осталось 323, включая удержанную 208;
  следующая непросмотренная позиция 262. Это не процент готовности S04.

- Проверены группы 262–273: 12 компонент и 84 файла, по одному фону на
  компоненту. Сходные шаблоны отчётов и дипломов отмечены для будущего split.
  review-v27 структурно проверен; приватные registry-v25 и queue-progress-v24
  обновлены.
- Очередь проверена на 46,66% (272/583), осталось 311, включая удержанную 208;
  следующая непросмотренная позиция 274. Это не процент готовности S04.

- Проверены группы 274–285: 12 компонент и 84 файла, по одному фону на
  компоненту. Возможные связи юридических страниц требуют дальнейшей проверки.
  review-v28 структурно проверен; приватные registry-v26 и queue-progress-v25
  обновлены.
- Очередь проверена на 48,71% (284/583), осталось 299, включая удержанную 208;
  следующая непросмотренная позиция 286. Это не процент готовности S04.

- Проверены группы 286–297: 12 компонент и 84 файла, по одному фону на
  компоненту. review-v29 структурно проверен; приватные registry-v27 и
  queue-progress-v26 обновлены.
- Очередь проверена на 50,77% (296/583), осталось 287, включая удержанную 208;
  следующая непросмотренная позиция 298. Это не процент готовности S04.

- Проверены 11 компонент из позиций 298–309 (66 файлов). Компонента 303 с
  неоднозначными фрагментами оставлена на удержании вместе с 208. review-v30
  структурно проверен; приватные registry-v28 и queue-progress-v27 обновлены.
- Очередь проверена на 52,66% (307/583), осталось 276, включая 208 и 303;
  следующая непросмотренная позиция 310. Это не процент готовности S04.

- Проверены группы 310–321: 12 компонент и 72 файла, по одному фону на
  компоненту. review-v31 структурно проверен; приватные registry-v29 и
  queue-progress-v28 обновлены. Группы 208 и 303 остаются на удержании.
- Очередь проверена на 54,72% (319/583), осталось 264; следующая непросмотренная
  позиция 322. Это не процент готовности S04.

- Проверены группы 322–333: 12 компонент и 66 файлов, по одному фону на
  компоненту. review-v32 структурно проверен; приватные registry-v30 и
  queue-progress-v29 обновлены. Группы 208 и 303 остаются на удержании.
- Очередь проверена на 56,78% (331/583), осталось 252; следующая непросмотренная
  позиция 334. Это не процент готовности S04.

- Проверены группы 334–345: 12 компонент и 60 файлов, по одному фону на
  компоненту. review-v33 структурно проверен; приватные registry-v31 и
  queue-progress-v30 обновлены. Группы 208 и 303 остаются на удержании.
- Очередь проверена на 58,83% (343/583), осталось 240; следующая непросмотренная
  позиция 346. Это не процент готовности S04.

- Проверены группы 346–357: 12 компонент и 60 файлов, по одному фону на
  компоненту. Дипломы 288 и 356 имеют общий шаблон при разных получателях.
  review-v34 структурно проверен; приватные registry-v32 и queue-progress-v31
  обновлены. Группы 208 и 303 остаются на удержании.
- Очередь проверена на 60,89% (355/583), осталось 228; следующая непросмотренная
  позиция 358. Это не процент готовности S04.

- Проверены группы 358–369: 12 компонент и 56 файлов. Установлена четвёртая
  межкомпонентная связь одинаковой страницы: 292 и 360; сохранена в приватном
  cross-component-links-v3. review-v35 структурно проверен; приватные
  registry-v33 и queue-progress-v32 обновлены.
- Очередь проверена на 62,95% (367/583), осталось 216, включая удержанные 208 и
  303; следующая позиция 370. Это не процент готовности S04.

- Проверены 10 компонент из позиций 370–381 (40 файлов). Компоненты 371 и 380
  с неоднозначными фрагментами удержаны вместе с 208 и 303. review-v36
  структурно проверен; приватные registry-v34 и queue-progress-v33 обновлены.
- Очередь проверена на 64,67% (377/583), осталось 206, включая четыре
  удержанные; следующая позиция 382. Это не процент готовности S04.

- Проверены группы 382–393: 12 компонент и 48 файлов, по одному фону на
  компоненту. review-v37 структурно проверен; приватные registry-v35 и
  queue-progress-v34 обновлены. Группы 208, 303, 371 и 380 удержаны.
- Очередь проверена на 66,72% (389/583), осталось 194; следующая непросмотренная
  позиция 394. Это не процент готовности S04.

- Проверены 9 компонент из позиций 394–405 (31 файл). Компоненты 395, 397 и
  403 с неоднозначными фрагментами удержаны вместе с 208, 303, 371 и 380.
  review-v38 структурно проверен; приватные registry-v36 и queue-progress-v35
  обновлены. Общий шаблон дипломов 396 и 404 отмечен для будущего split.
- Очередь проверена на 68,27% (398/583), осталось 185, включая семь удержанных;
  следующая позиция 406. Это не процент готовности S04.

- Проверены группы 406–417: 12 компонент и 36 файлов, по одному фону на
  компоненту. review-v39 структурно проверен; приватные registry-v37 и
  queue-progress-v36 обновлены. Семь неоднозначных групп остаются удержанными.
- Очередь проверена на 70,33% (410/583), осталось 173; следующая непросмотренная
  позиция 418. Это не процент готовности S04.

- Проверены 10 компонент из позиций 418–429 (22 файла), 424 и 427 удержаны из-за
  неоднозначных фрагментов. Совпадения 389/419 и 393/428 сохранены в приватном
  cross-component-links-v4. review-v40 структурно проверен; приватные registry-v38
  и queue-progress-v37 обновлены.
- Очередь проверена на 72,04% (420/583), осталось 163, включая девять удержанных;
  следующая позиция 430. Это не процент готовности S04.

- Проверены группы 430–441: 12 компонент и 24 файла, по одному фону на
  компоненту. review-v41 структурно проверен; приватные registry-v39 и
  queue-progress-v38 обновлены. Девять неоднозначных групп остаются удержанными.
- Очередь проверена на 74,10% (432/583), осталось 151; следующая непросмотренная
  позиция 442. Это не процент готовности S04.

- Проверены группы 442–453: 12 компонент и 24 файла, по одному фону на
  компоненту. review-v42 структурно проверен; приватные registry-v40 и
  queue-progress-v39 обновлены. Девять неоднозначных групп остаются удержанными.
- Очередь проверена на 76,16% (444/583), осталось 139; следующая непросмотренная
  позиция 454. Это не процент готовности S04.

- Проверены 11 компонент из позиций 454–465 (22 файла). Компонента 464 с
  неоднозначными фрагментами удержана. review-v43 структурно проверен;
  приватные registry-v41 и queue-progress-v40 обновлены.
- Очередь проверена на 78,04% (455/583), осталось 128, включая десять
  удержанных; следующая позиция 466. Это не процент готовности S04.

- Проверены группы 466–477: 12 компонент и 24 файла, по одному фону на
  компоненту. review-v44 структурно проверен; приватные registry-v42 и
  queue-progress-v41 обновлены. Десять неоднозначных групп остаются удержанными.
- Очередь проверена на 80,10% (467/583), осталось 116; следующая непросмотренная
  позиция 478. Это не процент готовности S04.

- Проверены 11 компонент из позиций 478–489 (22 файла). Компонента 488 с
  неоднозначными фрагментами удержана. review-v45 структурно проверен;
  приватные registry-v43 и queue-progress-v42 обновлены.
- Очередь проверена на 81,99% (478/583), осталось 105, включая 11 удержанных;
  следующая позиция 490. Это не процент готовности S04.

- Проверены группы 490–501: 12 компонент и 24 файла. Совпадение 382/500
  сохранено в приватном cross-component-links-v5. review-v46 структурно
  проверен; приватные registry-v44 и queue-progress-v43 обновлены.
- Очередь проверена на 84,05% (490/583), осталось 93, включая 11 удержанных;
  следующая позиция 502. Это не процент готовности S04.

- Проверены 11 компонент из позиций 502–513 (22 файла). Компонента 510 с
  неоднозначными фрагментами удержана. review-v47 структурно проверен;
  приватные registry-v45 и queue-progress-v44 обновлены.
- Очередь проверена на 85,93% (501/583), осталось 82, включая 12 удержанных;
  следующая позиция 514. Это не процент готовности S04.

- Проверены группы 514–525: 12 компонент и 24 файла. Совпадение 466/515
  сохранено в приватном cross-component-links-v6. review-v48 структурно
  проверен; приватные registry-v46 и queue-progress-v45 обновлены.
- Очередь проверена на 87,99% (513/583), осталось 70, включая 12 удержанных;
  следующая позиция 526. Это не процент готовности S04.

- Проверены группы 526–537: 12 компонент и 24 файла, по одному фону на
  компоненту. review-v49 структурно проверен; приватные registry-v47 и
  queue-progress-v46 обновлены.
- Очередь проверена на 90,05% (525/583), осталось 58, включая 12 удержанных;
  следующая позиция 538. Это не процент готовности S04.

- Проверены группы 538–549: 12 компонент и 24 файла, по одному фону на
  компоненту. review-v50 структурно проверен; приватные registry-v48 и
  queue-progress-v47 обновлены.
- Очередь проверена на 92,11% (537/583), осталось 46, включая 12 удержанных;
  следующая позиция 550. Это не процент готовности S04.

- Проверены 11 компонент из позиций 550–561 (22 файла). Компонента 556 с
  неоднозначными фрагментами удержана. review-v51 структурно проверен;
  приватные registry-v49 и queue-progress-v48 обновлены.
- Очередь проверена на 94,00% (548/583), осталось 35, включая 13 удержанных;
  следующая позиция 562. Это не процент готовности S04.

- Проверены группы 562–583: 22 компоненты и 44 файла, по одному фону на
  компоненту. review-v52 структурно проверен; приватные registry-v50 и
  queue-progress-v49 обновлены.
- Очередь проверена на 97,77% (570/583); остались 13 удержанных неоднозначных
  компонент, непросмотренных позиций нет. Это не процент готовности S04.

- Для 7854 изображений проверенного экспорта вычислена верхняя граница 4423
  оригинальных фонов (при условии правильности визуальных решений); для минимума
  5000 нужны как минимум 577 дополнительных независимых пригодных страниц.
  13 неоднозначных компонент остаются удержанными. Проверка очереди — 97,77%;
  общий процент готовности S04 не установлен.

- Проверен технический пилот DocLayNet-small фиксированной ревизии: архив и CRC
  проверены, 804 страницы декодированы, точных побайтовых совпадений с mapo80
  не найдено. Обзор 30 train-страниц выявил хотя бы одну подпись. Целевая
  разметка, визуальная дедупликация, происхождение и QC ещё не завершены;
  страницы не приняты. Детали: reports/data/clean-source-search.md.
- Проверка очереди исходных фонов остаётся на 97,77%; общая готовность S04 не
  измерена. Минимум 5000 независимых пригодных страниц ещё не подтверждён.
