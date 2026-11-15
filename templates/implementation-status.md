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
