# План обучения и экспериментов

## До запуска

Обучение начинается после аудита внешнего корпуса, принятия правил разметки, QC и фиксации split. Собрать статистику размеров bbox, объектов/страницу, долей негативов и класса, повреждений, распределений по split. Указать реальные GPU, VRAM, RAM, CPU, ОС, Python, CUDA, PyTorch и версии пакетов. Рекомендация для планирования — GPU 12–24 GB VRAM; это не доказанная минимальная конфигурация. Сделать пробу 20–50 шагов, измерить память и скорость; определить batch по фактической VRAM. Без GPU организовать малый smoke run и отдельную согласованную среду полного обучения.

## Базовый протокол

Transfer learning двух классов с pretrained small detector. Стартовые предложения: imgsz=1024, epochs=100, patience=20, seed=42, batch=4, optimizer=AdamW, lr0=0.001. Все значения требуют smoke-проверки и точного отображения в параметры выбранной версии библиотеки. Сохранять effective config, включая унаследованные настройки; не смешивать auto optimizer с ручными утверждениями о learning rate. Early stopping и best checkpoint только по val mAP50-95. Не обучать «до красивого test».

Сначала проверить способность переобучиться на 10–20 положительных страницах: адекватные рамки и падение loss. Затем реальный baseline на train, с reviewed negatives и неизменной validation. Сохранять best и last, эпоху, seed, hash начальных и итоговых весов; при resume фиксировать точку и состояние optimizer.

## Последовательность опытов

| ID | Изменение | Зачем | Решение |
|---|---|---|---|
| E00 | Проверка 10–20 страниц | найти ошибки формата/классов/координат | baseline не запускать при провале |
| E01 | Целая страница, 1024 | измерить исходный уровень | опорная конфигурация |
| E02 | Только разрешение 1536 | проверить мелкие объекты | оценить качество против памяти/времени |
| E03 | Tiling вместо full page | проверить сохранение деталей | сравнить итоговые page-level метрики |
| E04 | Только умеренные аугментации | устойчивость к сканам | принять по val и срезам ошибок |
| E05 | Второй размер/архитектура при необходимости | предел качества и скорости | запускать при бюджете/обосновании |

Каждый опыт меняет одну гипотезу относительно явно указанного parent. E03/E04 стартуют от зафиксированного parent; не складывать изменения без отдельной строки. Для финального кандидата желательно 3 seed при наличии ресурсов, сообщать среднее/разброс; при одном seed прямо обозначить ограничение.

## Аугментации и дисбаланс

Умеренные повороты (начально ±5°), яркость/контраст, blur, JPEG деградация в реалистичных пределах. Horizontal/vertical flip отключить; сильные перспективы, mosaic и mixup в первом baseline отключить и сравнивать отдельно. Печатный/рукописный контекст не должен исчезать систематически. Не применять случайные train transforms к val/test. Oversampling допускается только внутри train; не удалять все negatives и не менять оценочное распределение.

## Tiling как отдельный эксперимент

Начальный кандидат: tile=1024 px, overlap=20%. Сохранять page_id, offset и геометрию. Объекты на границе не превращать в ложные negatives: назначать полную bbox в содержащий tile, а частичные пересечения либо сопровождать корректным clipping и признаком truncated, либо исключать соответствующий tile из supervised набора. Окончательную политику документировать до запуска и проверять визуально. При inference remap в page pixels, объединение рамок class-aware NMS с фиксированным IoU, сохранение разных классов в перекрытии. Сравнивать на исходных страницах; tile-level AP не заменяет итоговый AP.

## Оценка и выбор порогов

На val выбрать class-specific thresholds по F1 либо целевому recall, записать функцию выбора и значения. NMS и tile параметры тоже выбирать только на val. На test один финальный прогон фиксированного bundle: AP50, AP50-95 IoU=.50:.05:.95, precision/recall/F1 на выбранном рабочем пороге, поклассовые support, FP на страницу, page presence recall как дополнительная метрика. AP считать по ранжированным confidence с низким фиксированным cutoff (например 0.001) и достаточно большим max_det; UI порог не должен обрезать AP. Зафиксировать backend метрик, matching и max_det.

Отдельные срезы: слабые печати, подписи поверх текста, пересечения классов, маленькие объекты (дать определение), negatives, неполные объекты, семейства документов. Измерить preprocess/inference/postprocess и end-to-end время отдельно, warmup, минимум 100 страниц при наличии, median/p95, batch=1, оборудование, включён ли I/O. Bootstrap интервалы по группам документов при достаточном числе групп; при малом числе описать ограничение.

## Воспроизводимость

Каждая строка experiments.csv содержит commit, dataset revision/hash, annotation hash, split hash, config path/hash, seed, model identifier, весовой hash, среду, метрики, длительность, артефакты и замечания. Заполнять только измеренными значениями. Model card включает назначение, данные, лицензионные ограничения, пороги, результаты и известные ошибки. Ссылка на веса должна вести к реально проверяемому артефакту с checksum; не коммитить веса в Git.

## Конфигурация расширенного корпуса

Источник — `mapo80/stamps`, проверенные статусы и геометрия собраны на S04.
Используйте приватные артефакты из [инструкции передачи](22-handoff-3000.md)
и завершённые решения QC. Три файла `manifest.jsonl`, `annotations.json` и
`split.json` фиксируют выборку. Сводка и SHA-256 доступны в `qc-report.json`.
Сборка создаёт новую папку, существующий экспорт остаётся доступен.

```console
python -m scripts.finalize_s04 --output artifacts/data-qc/s04-expanded-v1
```

Для S05 используется YOLO11n с COCO-весами, CUDA 12.8 и версиями из
[`requirements-s05.txt`](../requirements-s05.txt). Эксперименты используют один
seed. Конфигурация `s05-yolo11n.json` задаёт до 30 эпох baseline, раннюю
остановку с patience 10, разрешение 1024 и batch 4. Малый вариант YOLO11n и
лимит эпох выбраны для первого измеренного baseline на локальной RTX 4070.
Прогон E00 использует 16 положительных страниц только из train и оценивается
на тех же страницах для проверки пайплайна. Оценка E01 и последующих
экспериментов использует замороженный val.

Из корня репозитория с установленными ML-зависимостями выполните E00 и оцените
`results.csv`. Для последующих запусков используйте тот же входной экспорт.
Команды E00, E01, E02 и E04 выполнены на Windows с RTX 4070. Для Colab
подготовлен [ноутбук](../notebooks/s05-training.ipynb) с теми же entrypoints.

```console
python -m scripts.train_s05 E00 --dataset artifacts/data-qc/s04-expanded-v1 --config configs/s05-yolo11n.json --runs artifacts/s05-runs
python -m scripts.train_s05 E01 --dataset artifacts/data-qc/s04-expanded-v1 --config configs/s05-yolo11n.json --runs artifacts/s05-runs
python -m scripts.evaluate_s05 --experiment E01 --split val --data artifacts/data-qc/s04-expanded-v1/dataset.yaml --config configs/s05-yolo11n.json --weights artifacts/s05-runs/E01/weights/best.pt --output artifacts/s05-runs/E01/validation
```

Для вариантов E02 и E04 подставьте их идентификаторы в команды обучения
и оценки. `run-inputs.json` фиксирует использованные параметры, контрольные
суммы и окружение. `args.yaml` содержит эффективные параметры Ultralytics.
Скрипт `package_s05` выбирает лучшую модель по mAP50–95 на val и проверяет
загрузку на CPU.

```console
python -m scripts.package_s05 --runs artifacts/s05-runs --experiments E01 E02 E04 --output artifacts/s05-runs/bundle-v1
python -m scripts.evaluate_s05 --experiment E01 --split test --data artifacts/data-qc/s04-expanded-v1/dataset.yaml --config configs/s05-yolo11n.json --weights artifacts/s05-runs/bundle-v1/model.pt --thresholds-from artifacts/s05-runs/E01/validation/metrics.json --output artifacts/s05-runs/test-expanded
```

На втором, прежнем учебном test использованы те же веса и `--thresholds-from`.
Его каталог `artifacts/data-qc/s04-teaching-v1/yolo` содержит прежний экспорт.
Для оценки используется YAML с
`train`, `val` и `test`, указывающими на `images/test`, и `names: [stamp, signature]`.
Команда оценки с `--split test` обрабатывает только test. Реальные метрики,
ограничения и ссылки на пример приведены в [отчёте S05](../reports/s05-training.md).

Скорость замерена на 100 страницах val. Параметры бенчмарка и метрики выводятся
в JSON.

```console
python -m scripts.benchmark_s05 --bundle artifacts/s05-runs/bundle-v1 --dataset artifacts/data-qc/s04-expanded-v1 --device 0 --output artifacts/s05-runs/benchmark-gpu.json
```
