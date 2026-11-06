# Паспорт выбора данных — S02

Дата: 06.11.2026. **Статус: blocked; обучающий корпус ещё не принят.**
Обязательный минимум: 5 000 уникальных исходных страниц. YAT-19 исключён.
Это результаты проверки доступных метаданных, не завершённый визуальный аудит изображений.
Актуальное продолжение с реальным ZIP — раздел 6; сетевые ограничения ниже относятся к первоначальной проверке.

## 1. Sig & Stamps — приоритетный кандидат

- Первичная карточка: https://universe.roboflow.com/sig-and-stamps/sig-stamps
- Зеркало по ссылке автора: https://www.kaggle.com/datasets/mertaslayilmaz/signature-stamp-segmentation-dataset
- Источник связи: [README автора](https://github.com/mertyilmaz5/kaggle_signature_stamp_segmentation/blob/main/README.md), Git blob `d02bffb56ef72a75d49516ab9ab156f4e58ee189`, повторно прочитан 06.11.
- 06.11 запрос `curl -L --max-time 25 https://universe.roboflow.com/sig-and-stamps/sig-stamps` остановлен облачным proxy: `CONNECT tunnel failed, response 403`. Это отказ сетевой политики окружения, а не доказательство недоступности самого сайта.
- Проверка environment_status: observations_current=true, политика restricted/enforced; Roboflow и Kaggle не входят в разрешённые домены. Пользователю отправлен запрос изменения доступа.
- Версия, лицензия, число оригиналов/объектов, размер архива, checksum и полнота разметки **не установлены**. ZIP/экспорт не получен. Пилот не выполнялся.

## 2. SignverOD — аудит конкретного GitHub-зеркала

Репозиторий: https://github.com/mk-chang/SignverOD_Datset

Зафиксированная ревизия: `c24bbbcc079138b9740cdc8f3afaed37c6ff5b0a`.
Прочитан полный recursive Git tree (truncated=false), скачаны пять текстовых файлов: categories.csv, image_ids.csv, train.csv, test.csv, labelmap.txt. **Изображения не скачивались и не декодировались.**

Измерения и SHA-256 файлов: [signverod-metadata-audit.json](signverod-metadata-audit.json).

| Проверка | Фактический результат |
|---|---:|
| Файлы изображений в Git tree | 2 765 |
| Различные Git blob ID изображений | 2 761 |
| Группы побайтовых дублей / лишние копии | 4 / 4 |
| Сумма размеров изображений в Git tree | 796 962 784 байт |
| Строки image_ids.csv / различные id | 2 765 / 2 133 |
| Значения id с несколькими filename | 632 |
| Строки bbox train / test | 7 549 / 1 666 |
| Строки signature train / test | 4 189 / 855 |
| Строки с неоднозначным image_id train / test | 4 613 / 1 255 |
| Невалидные нормализованные xywh в CSV | 0 |
| Совпадающие значения image_id между train/test | 160 |

Важные ограничения:

- 2 761 — число разных байтовых представлений по Git blob ID, **не подтверждённое число уникальных исходных страниц**: near duplicates, повторные сканы и повреждения ещё не проверены. Даже этот верхний предел ниже 5 000.
- 632 коллизии image ID означают, что нельзя делать обычный join аннотаций с image_ids.csv по id: строки начнут относиться к нескольким изображениям. Требуется первичный экспорт с пространствами имён источников/однозначными ключами. Разбиение восстанавливать после исправления идентичности страниц.
- Пересечение 160 числовых ID не доказывает утечку конкретных страниц: сами ID неоднозначны. Не использовать этот split в обучении без восстановления происхождения.
- Сумма строк bbox — 9 215, а во вторичном каталоге заявлено 8 022. Это разные наблюдения, не взаимозаменяемые версии статистики. Число строк с подписью не выдаётся за число проверенных корректных объектов.
- bbox в CSV выглядят как нормализованные xywh и проходят числовую проверку. Геометрия относительно реальных изображений визуально не подтверждена; не считать их COCO pixel bbox.
- Классы: upstream 1 signature, 2 initials, 3 redaction, 4 date. Печатей нет. Только signature→наша 1; остальные категории не объединять с подписью. Страницы потребуют проверки на оба целевых класса.
- [Вторичный каталог декларирует CC0 1.0](https://github.com/dataset-ninja/signver-od/blob/main/LICENSE.md), blob `272b3a8e717df5795d7d27c8cecd5ae962c2fac9`. Первичная Kaggle-карточка и условия конкретного зеркала пока не проверены. MIT библиотеки SignVer не является автоматической лицензией данных.

**Решение:** это зеркало не принимать как готовый обучающий набор. Оно полезно для исследования; при выборе SignverOD получить первичный экспорт и проверить идентичность/лицензию/полноту разметки.

### Воспроизведение аудита

В локальном `artifacts/data-audit/signverod/` лежат пять текстовых файлов и `tree.json`. Их URL/revision и SHA-256 указаны в JSON-отчёте; tree берётся по зафиксированной GitHub REST ссылке из того же отчёта. В текущем окружении tree получен через GitHub connector, CSV — по raw.githubusercontent.com. Артефакты исключены из Git.

Проверенная команда из корня проекта (без сети, Python standard library):

```console
python scripts/audit_signver_metadata.py artifacts/data-audit/signverod --output reports/data/signverod-metadata-audit.json
```

На другой машине предварительно получить входные файлы по указанным URL. Скрипт не скачивает данные, не исправляет коллизии и не даёт разрешение на обучение; он записывает наблюдения и причины отказа.

## 3. StaVer — резерв для печатей

- [Карточка и заявленные counts](https://github.com/dataset-ninja/staver): 427 изображений и 377 объектов stamp (описание из предыдущего исследования, не новый подсчёт файлов).
- [Лицензия](https://github.com/dataset-ninja/staver/blob/main/LICENSE.md): unknown; Git blob `ea104ec3a73f1eab6fe1c62684e3330341e6af73`, прочитан 06.11.
- [DOWNLOAD.md](https://github.com/dataset-ninja/staver/blob/main/DOWNLOAD.md), blob `d4319ce9a91ccdd4d2bbd9a58edbe3360e50383a`, направляет на http://madm.dfki.de/downloads-ds-staver . Первичные условия и файлы не получены.
- Даже сумма заявленных 2 765 + 427 = 3 192 ниже минимума, ещё до удаления дублей и исключений. SignverOD+StaVer больше не является достаточным резервом по объёму.

## 4. Дополнительные источники

| Источник | Проверено 06.11 | Решение |
|---|---|---|
| [sadjava/stamp-detection](https://github.com/sadjava/stamp-detection) | README blob `a836d336fa1a01d43610a8cc488d564d8da52b33`: заявлены 3 000 изображений, часть синтетическая; проверенного архива и лицензии данных нет | Не засчитывать заявленные 3 000 как уникальные реальные страницы |
| [Stamp-Signature-Segregate](https://github.com/KumarShivam1908/Stamp-Signature-Segregate) | README blob `60ebc760a6e2884b94a479d3aa609fb0c4b2f327`: ссылка на Kaggle segment-overlapping-sign-stamp, заявлены 1 422 train и 82 val; источник Roboflow | Проверить как дополнительный источник после доступа к Kaggle; GPL кода не подтверждает лицензию данных; аугментации и test неизвестны |
| [NanoNets/SignatureDetectionDataset](https://github.com/NanoNets/SignatureDetectionDataset) | Полный tree SHA `89e4735717c73037bceb892b6ac89f3aca050111`: 197 изображений images/, 197 разных blob. README blob `6b1613145b8a2659a9a55da7c054cf9370f96ca3` сообщает Google/Bing; в tree не найден LICENSE | Не решает объём, права на исходные изображения не подтверждены |
| [DocLayNet](https://github.com/DS4SD/DocLayNet) | Первичный README blob `7eb63995ef0745358d74499a4cadcf878bff62f2` заявляет 80 863 уникальные страницы; LICENSE blob `b13f50ebccb1948aec15ab1fbab45f15e345ae61` — CDLA-Permissive-1.0; core 1.0.0 заявлен как 28 GiB | Возможный источник дополнительных реальных страниц, но нет готовых целевых классов. Нужны скачивание, пилот, поиск релевантных документов и полная разметка обоих классов. Не выбирать ради одного числа страниц |

DocLayNet core URL из первичного README:
https://codait-cos-dax.s3.us.cloud-object-storage.appdomain.cloud/dax-doclaynet/1.0.0/DocLayNet_core.zip

Архив не скачан, checksum и размер не измерены. При сохранении полного ZIP и распаковки заранее проверить бюджет 100 GB вместе с окружением/логами/весами. 28 GiB — утверждение источника, не оценка объёма распакованных данных. Указанные примеры HF split в README включают повторные аннотации; сумму записей нельзя выдавать за число оригиналов.

## Критерии продолжения

1. Открыть доступ к `storage.googleapis.com` для экспортов Kaggle; решить доступ Roboflow Universe и лицензию Sig & Stamps (подробности ниже).
2. Проверить Sig & Stamps и дополнительный Kaggle-кандидат; не считать изображения после аугментаций уникальными страницами.
3. Если оригиналов недостаточно — подобрать дополнительные источники, включая пилот DocLayNet при необходимости; после дедупликации должно остаться ≥5 000 пригодных исходных страниц.
4. Получить checksum реального экспорта, проверить оба класса на пилоте до 200 страниц, совместно разобрать спорные примеры и оценить доразметку.
5. Только после этого выбрать корпус и закрыть S02. До тех пор accepted_for_training=false; полное обучение не запускать.


## 5. Продолжение S02 после изменения сети — 06.11.2026

### Доступ

Проверено в облачной Linux-среде через штатный proxy с включённой проверкой TLS.
`environment_status`: observations_current=true, restricted/enforced; разрешены
api.roboflow.com, universe.roboflow.com, kaggle.com, www.kaggle.com.
Секреты и outbound identities не настроены; аутентифицированные операции не проверены.

- `https://api.roboflow.com/` — HTTP 200 JSON. Это доступ к API, не к экспорту.
- `https://api.roboflow.com/sig-and-stamps/sig-stamps` без ключа — HTTP 401.
- `https://universe.roboflow.com/` — HTTP 403 при разрешённом домене.
  Причина на стороне сайта/защиты не установлена; прежний CONNECT denial для этого
  домена больше не описывает текущую проверку.
- Публичные Kaggle `datasets/list` (поиск), `datasets/view/{owner}/{slug}` и
  `datasets/list/{owner}/{slug}` — HTTP 200 без входа в аккаунт.
- Version-pinned download основного кандидата (v1) и SignverOD (v15) — HTTP 302
  на `storage.googleapis.com`. При переходе основного download: proxy CONNECT 403;
  домен отсутствует в allowlist. Подписанные URL не сохраняются в Git.
  Доступ запрошен пользователю; обход proxy не выполнялся.

### Полные списки файлов Kaggle

Машиночитаемое evidence: [kaggle-metadata-audit.json](kaggle-metadata-audit.json).
Все страницы API list дочитаны до отсутствия nextPageToken; размер страницы 200.
View проверен до и после списка: version/lastUpdated/totalBytes не изменились.
Сам endpoint list не фиксирует версию, поэтому это наблюдение текущего состояния,
а не immutable export. Сумма размеров всех записей совпала с totalBytes view.
Размеры ниже относятся к содержимому, **не к ZIP**. Search API возвращает другие
значения totalBytes; не смешивать их с view/list.

| Kaggle ref | Версия | Лицензия по API | Изображения в полном list | Байты всех файлов |
|---|---:|---|---:|---:|
| mertaslayilmaz/signature-stamp-segmentation-dataset | 1 | Unknown | 2 452 | 182 376 303 |
| victordibia/signverod | 15 | CC0: Public Domain | 2 765 | 1 597 426 836 |
| zeadekrame/document-signature-stamp-detection | 1 | CC BY-NC-SA 4.0 | 17 110 | 2 179 225 436 |
| azharhasannsaif/arabic-official-documents | 1 | CC BY 4.0 | 842 | 782 090 884 |
| igorkarayman/signatures-and-stamps | 1 | Unknown | 1 000 | 546 187 901 |

Результаты и решения:

1. **Sig & Stamps / Kaggle mirror v1**: train 1 941, valid 257, test 254;
   2 452 изображения и 2 452 labels плюс data.yaml. После удаления `.rf.`-суффикса
   в имени остаётся 1 045 различных префиксов. Это только признак повторных
   экспортов/преобразований: алгоритм не доказывает ни дубли, ни число оригиналов.
   Даже верхний предел 2 452 меньше 5 000. Лицензия зеркала Unknown, описание пустое;
   первичная лицензия Roboflow не установлена. Набор не принимать как единственный корпус.
2. **Первичный SignverOD v15**: лицензия CC0 подтверждена полем API владельца
   victordibia. В описании заявлены 2 576 сканов и 7 103 bbox; list содержит
   2 765 изображений. Это разные наблюдения; расхождение требует проверки экспорта.
   Описаны источники Tobacco800, NIST, bank cheques, GSA. Есть синтезированные формы
   среди upstream-источников: не считать всё реальными уникальными страницами без QC.
   Предыдущий аудит коллизий относится к GitHub-зеркалу, а не автоматически к v15.
   Stamp отсутствует в заявленном словаре; необходим просмотр обоих классов.
3. **Новый составной кандидат zeadekrame v1**: 16 000 изображений в `rvl_cdip/`
   (16 папок по 1 000), 810 в `signatures/` (648/81/81), 300 в `stamps/`
   (240/60 train/val). Имеются 1 110 файлов labels, но в `rvl_cdip/` целевых labels нет.
   Это не готовый двухклассовый корпус из 17 110 размеченных страниц. Неразмеченные
   страницы нельзя считать negatives. Описание Kaggle пустое; декларация CC BY-NC-SA 4.0
   на сборке не устанавливает автоматически условия всех upstream-компонентов.
   Приоритетный дополнительный кандидат для пилота после загрузки: проверить README,
   YAML, происхождение, лицензии компонентов, долю целевых объектов и стоимость
   полной разметки ≥5 000 независимых страниц. Не переносить single-class labels без QC.
4. **Arabic official documents v1**: 842 изображения, целевых labels в list нет.
   Лицензия в API CC BY 4.0, описание содержит рекомендательный текст о выборе лицензии;
   это требует уточнения условий. Самостоятельно не решает минимальный объём.
5. **Signatures and stamps v1**: 1 000 изображений, labels в list нет, Unknown.
   Заявлены русскоязычные документы; встречаются имена с `(1)` и одинаковыми размерами,
   что требует проверки дублей по содержимому. Не принимать без условий использования.

Ни одно из чисел изображений не является подтверждённым числом пригодных уникальных
исходных страниц. Архивы, SHA-256 ZIP, геометрия labels, число объектов и визуальный
пилот не получены. Все кандидаты имеют accepted_for_training=false.

### Воспроизведение новой проверки

Скрипт использует только Python standard library и публичный API; ключи не нужны.
Сырые ответы с именами файлов остаются в игнорируемом `artifacts/`; в Git только
агрегаты, номера версий и SHA-256 каждого ответа. Пагинационные токены в отчёт не входят.

Проверенная команда из корня репозитория (нужен сетевой доступ к www.kaggle.com):

```console
python scripts/audit_kaggle_metadata.py mertaslayilmaz/signature-stamp-segmentation-dataset victordibia/signverod zeadekrame/document-signature-stamp-detection azharhasannsaif/arabic-official-documents igorkarayman/signatures-and-stamps --raw-dir artifacts/data-audit/kaggle/inventory --output reports/data/kaggle-metadata-audit.json
```

Скрипт завершится ошибкой при повторном пути/токене, превышении лимита 100 страниц
или изменении version/lastUpdated/totalBytes во время сбора; частичный список не
выдаётся за полный. Результат не разрешает обучение и не заменяет importer S03.

**Следующий шаг:** добавить storage.googleapis.com в сетевую политику, получить
version-pinned экспорты и SHA-256, начать с README/YAML/лицензий и пилота нового
составного кандидата; параллельно установить первичные условия Sig & Stamps.
S02 остаётся blocked: нет принятого корпуса ≥5 000, подтверждённых условий всех
выбранных компонентов и совместного визуального пилота.


## 6. Реальный экспорт Kaggle и проверка ZIP — 06.11.2026

Повторная проверка: Roboflow root API 200 JSON, карточка Universe 403;
публичный Kaggle search 200. В текущей политике restricted/enforced разрешён
также storage.googleapis.com. Экспорт Sig & Stamps получен через штатный proxy/TLS
без аккаунта; прежний блокер скачивания этого ZIP снят. Секреты не настроены.

Загрузка зафиксированной версии:

```console
curl --fail --location --max-time 120 --silent --show-error 'https://www.kaggle.com/api/v1/datasets/download/mertaslayilmaz/signature-stamp-segmentation-dataset?datasetVersionNumber=1' -o artifacts/data-audit/exports/signature-stamp-segmentation-dataset-v1.zip
python scripts/audit_dataset_zip.py artifacts/data-audit/exports/signature-stamp-segmentation-dataset-v1.zip --output reports/data/sig-stamps-zip-audit.json
```

Каталог назначения предварительно создан через `mkdir -p artifacts/data-audit/exports`.
Подписанный redirect URL в Git не сохраняется. ZIP и исходные документы остаются
в игнорируемом artifacts/. Evidence: [sig-stamps-zip-audit.json](sig-stamps-zip-audit.json).

- ZIP: 169 435 546 байт, SHA-256
  `f5719c8acb7dcf903b84c3ca0f68fe5523031e809b514d1c8f32493e4bbc6617`.
- Все члены прочитаны с проверкой CRC; распаковка не выполнялась.
- 2 452 изображения, 2 452 различных SHA-256, побайтовых копий нет.
  Это не проверка near duplicates/аугментаций и не число исходных страниц.
- 2 452 файла labels, из них 16 пустых. Пустота не подтверждает reviewed_empty.
- 5 265 строк: исходный класс 0 — 3 431, класс 1 — 1 834.
  `data.yaml` определяет `names: ["signature", "stamp"]`, `nc: 2`.
  Для SealSign необходимо **0→1, 1→0**. Эти counts относятся к строкам экспорта,
  не к визуально подтверждённым объектам.
- Строки имеют от 11 до 339 токенов (не фиксированные 5 для bbox YOLO).
  Нельзя читать их как готовые cx/cy/w/h: требуется проверка polygon-геометрии
  и отдельное получение охватывающих рамок на S03.
- YAML содержит абсолютные Kaggle-пути: они не являются переносимой конфигурацией
  SealSign. В ZIP не найден README/Markdown или файл с license в имени;
  декларация лицензии зеркала остаётся Unknown. Нельзя вывести лицензию из YAML.

Скрипт использует standard library, не извлекает файлы, отклоняет небезопасные/
повторные пути и symlink, ограничивает общий распакованный объём 20 GiB и текстовый
член 4 MiB. Повреждённый CRC прекращает аудит; отчёт публикуется только после
успешного чтения. Скрипт не декодирует изображения, не проверяет координаты и
не разрешает обучение. Тесты покрывают CRC, опасные пути и отличие дублей/пустых
labels от подтверждённых оригиналов/negatives.

**Решение:** Sig & Stamps v1 не принимать единственным корпусом: верхний предел
2 452 меньше обязательных 5 000, права и визуальная полнота не подтверждены.
S02 остаётся blocked до выбора допустимого корпуса ≥5 000 и совместного пилота.

### Составной кандидат: проверка полного архива

Получен `zeadekrame/document-signature-stamp-detection` v1 по endpoint
`https://www.kaggle.com/api/v1/datasets/download/zeadekrame/document-signature-stamp-detection?datasetVersionNumber=1`.
Размер ZIP 1 989 701 019 байт; SHA-256
`ed41b57f00a2d91ce218fcc7f333fd70300c67f9b0d926ffc7c206d62d156594`.
Первый curl с лимитом 180 секунд прерван по timeout после 466 631 251 байт;
загрузка продолжена HTTP Range, остаток получен шестью параллельными диапазонами
с проверкой Content-Range/длины. После объединения проверены CRC всех членов.
Временный загрузчик использовал только standard library, без изменения proxy/TLS.
Для повторной загрузки подходит тот же version-pinned endpoint с достаточным
таймаутом; контроль результата — размер, SHA-256 и команда ниже.

Проверенная команда:

```console
python scripts/audit_dataset_zip.py artifacts/data-audit/exports/document-signature-stamp-detection-v1.zip --output reports/data/composite-zip-audit.json
```

Evidence: [composite-zip-audit.json](composite-zip-audit.json).

| Компонент | Изображений | Различных SHA-256 | Labels | Строк / исходный класс | Пустых labels |
|---|---:|---:|---:|---|---:|
| rvl_cdip | 16 000 | 15 980 | 0 | — | 0 |
| signatures | 810 | 810 | 810 | 4 148 / 0 | 56 |
| stamps | 300 | 285 | 300 | 486 / 0 | 0 |

Всего 17 075 различных байтовых изображений из 17 110; 35 лишних копий.
В stamps найдены 3 группы одинаковых SHA-256 между исходными train/val;
этот split нельзя использовать без перегруппировки. В остальных компонентах
побайтовых пересечений распознаваемых split не найдено; это не проверка near duplicates.
Это верхняя граница, не число пригодных оригиналов. Изображения ещё не декодированы,
near duplicates/синтетика/читаемость и оба класса на каждой странице не проверены.
Все строки в двух компонентах имеют 5 токенов; корректность bbox не подтверждена.
Отсутствующие labels RVL-CDIP и 56 пустых signature-labels не подтверждают negatives.

`signatures/data.yaml`: `nc: 1`, `names: ['signatures']`, upstream version 1,
декларация `CC BY 4.0`, источник
https://universe.roboflow.com/zeadekrames-workspace/signature-yolo-t661e/dataset/1 .
Это сведения экспортного YAML, первичные условия страницы ещё не проверены.
`stamps/data.yaml`: `nc: 1`, `names: ['Stamp']`, train/val; источник и лицензия
не указаны. В архиве не найден README/Markdown или filename с license.
Mapping по компонентам различается: signatures 0→SealSign 1, stamps 0→SealSign 0.
Склеивание labels без provenance ошибочно смешает подписи и печати.

Декларация CC BY-NC-SA 4.0 для сборки по Kaggle API не заменяет проверку прав
компонентов RVL-CDIP/stamps и первичных условий signatures. **Не принимать набор
для supervised обучения до проверки прав, обоих классов и пилота.**
Следующий шаг: установить upstream-источник stamps и условия RVL-CDIP;
после этого декодирование, поиск near duplicates, воспроизводимый совместный пилот
до 200 страниц и оценка полной доразметки ≥5 000 пригодных исходных страниц.
