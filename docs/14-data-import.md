# Исследовательский импорт S03

Статус: реализация YOLO bbox/polygon → канонический bundle; корпус S02 не принят.
Команда не принимает решение о лицензии, полноте разметки или пригодности для обучения.
Все страницы остаются `unreviewed`, `accepted_for_training=false`, итоговый `split=null`.

## Входной контракт

ZIP с JPEG/PNG/TIFF/BMP/WebP (только одностраничные изображения) и текстовыми YOLO
labels. JSON-конфигурация фиксирует `archive_id`, SHA-256 ZIP и массив `sources`:

- `images`: относительный каталог изображений внутри ZIP;
- `labels`: относительный каталог labels, либо null для полностью неразмеченного источника;
- `format`: `bbox` (class cx cy w h) либо `polygon` (class x1 y1 ... xn yn);
- `class_map`: явное преобразование исходных строковых ID в целые 0=stamp/1=signature;
- `original_split`: метка upstream, сохраняется только как provenance.

Координаты нормализованы относительно **исходной растровой матрицы до EXIF**.
Это контракт импортёра, а не доказательство поведения любого upstream-экспортёра.
При другом соглашении источник сначала требует отдельного адаптера/проверки.
ImageOps.exif_transpose и преобразование точек согласованно применяют ориентации 1–8.
Полученная PNG имеет ту же ориентацию, что и канонические pixel bbox.
CSV, COCO и raster instance masks пока не поддерживаются как входные форматы.
Автоматического угадывания формата по числу токенов или словаря по YAML нет.

Для polygon каждая строка даёт отдельную bbox по min/max вершин; экземпляры не
объединяются. Проверяются конечность, диапазон координат, число значений, класс,
положительная площадь bbox и повтор рамки. Полная топология polygon не проверяется.
Численная погрешность границы bbox до 1e-9 в нормализованных координатах допускается;
для неё применяется ограничение на [0,1]. Остальные выходы за границу исключаются.

## Выход и ошибки

Новый каталог создаётся через временный соседний каталог с финальным rename.
Существующий output не перезаписывается. Исходные пути никогда не распаковываются:
выходные PNG и labels именуются только стабильным page_id SHA-256 от archive_id/пути.
ZIP проверяется до обработки: traversal, абсолютные/Windows-пути, symlink,
повтор имени и неоднозначная связь image→label запрещены. Лимиты: 20 GiB суммарного
распакованного содержимого, 64 MiB на изображение, 4 MiB на label, 50 млн пикселей.
Orphan label в выбранных каталогах и отсутствие изображений — ошибка всего запуска.
Неподдерживаемые файлы вне выбранных источников не импортируются.

Повреждённое изображение или невалидная разметка остаются в manifest с причиной
исключения; частичные аннотации страницы не сохраняются. Ошибка ZIP CRC прекращает
весь запуск без публикации bundle. Успешный exit 0 означает завершённый учёт,
а не отсутствие исключений: необходимо читать `report.json` и manifest.

Выход:

- `manifest.jsonl`: source SHA-256, размеры, decode/annotation/review status,
  исходный путь/split/class mapping, normalized checksum и причина исключения;
- `annotations.json`: COCO-подобные `images/annotations/categories`, pixel xywh,
  schema version `sealsign-data-v1`; source polygon остаётся в исходном ZIP;
- `images/`: PNG после EXIF и RGB conversion;
- `unreviewed-yolo/`: производные labels для проверки, **не принятый train dataset**;
- `previews/`: первые N допустимых страниц в сортировке путей с красными рамками
  stamp и синими signature; это технический preview, не случайный пилот S02;
- `import-config.json`, `report.json`: эффективная конфигурация/hash и агрегаты.

Отсутствующий label → `missing`, пустой → `empty_unreviewed`, непустой корректный →
`present`, ошибочный → `invalid`. Ни один статус не означает reviewed_empty.
Exact-дубли отмечаются по source SHA-256; document/group IDs остаются null до S04.
Превью и исходные документы остаются только в игнорируемом artifacts/; публикация
возможна после проверки прав и персональных данных.

## Проверенные команды

Из корня репозитория, после установки из uv.lock и получения соответствующих ZIP:

```console
uv run --no-sync sealsign data import --help
uv run --no-sync sealsign data import artifacts/data-audit/exports/signature-stamp-segmentation-dataset-v1.zip --config configs/import-sig-stamps-v1.json --output artifacts/data-import/sig-stamps-v1 --preview-limit 12
uv run --no-sync sealsign data validate artifacts/data-import/sig-stamps-v1
uv run --no-sync sealsign data import artifacts/data-audit/exports/document-signature-stamp-detection-v1.zip --config configs/import-composite-labels-v1.json --output artifacts/data-import/composite-labels-v1 --preview-limit 12
uv run --no-sync sealsign data validate artifacts/data-import/composite-labels-v1
```

Вторая конфигурация выбирает только 1 110 изображений signatures/stamps; 16 000
RVL-CDIP не входят в этот запуск. Нельзя выдавать число импортированных страниц за
размер всего ZIP или число проверенных оригиналов. Повторный запуск требует нового
выходного каталога. ZIP hashes и provenance — паспорт S02, раздел 6.

Валидатор проверяет schema/categories, уникальность ID, связи страниц/изображений,
существование и SHA-256 PNG, размеры, рамки, отсутствие повторных аннотаций и
совпадение производных YOLO с каноническими bbox. Он не проверяет семантику рамок,
права, полноту двух классов и near duplicates; обучение не разрешает.
