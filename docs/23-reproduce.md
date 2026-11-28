# Воспроизведение результатов SealSign

Рабочая версия проекта находится в ветке [work](https://github.com/chrtxachok/SealSign/tree/work).
Чтобы проверить готовую модель, достаточно пакета весов и среды. Для
повторного обучения дополнительно нужны архивы источника и зафиксированная
разметка команды. Команды запускаются из корня клона.

## Пакет весов и разметки

Веса выбранного E01 хранятся вне GitHub. Для передачи вместе с отчётом
подготовлен файл `SealSign-weights-and-metadata.zip`. Пакет выдаёт команда
проекта. Внутри находятся веса, конфигурация модели и итоговые метаданные S04.
На компьютере команды файл находится в `artifacts/submission/`.

Распакуйте пакет в `artifacts/`. После распаковки модель будет доступна в
`artifacts/s05-runs/bundle-v1/model.pt`, а вход для восстановления корпуса —
в `artifacts/submission/s04-metadata/`.

| Файл | SHA-256 |
|---|---|
| `model.pt` | `e6948a69a1e4c6055f99db1d0da954b49f25fd122e01052ff2b7e50cba19b27a` |
| `SealSign-weights-and-metadata.zip` | `0f6223b9cbb0e1ce8dfdf7e71d0a63492459a4c5f5784a00232e744b3aa15228` |

Для запуска существующего детектора используйте [PowerShell-команду из README](../README.md#локальная-проверка-страницы).
На новой машине установите пакеты из [requirements-s05.txt](../requirements-s05.txt)
в окружение Python 3.11 или 3.12. Обучение проверено на NVIDIA RTX 4070
с CUDA 12.8. Локальный интерфейс выполняет инференс на CPU.

## Исходные архивы

В зафиксированной редакции `998243bde1262ccb57ca28ddd6868b05fd1ddf49`
доступны [train.zip](https://huggingface.co/datasets/mapo80/stamps/resolve/998243bde1262ccb57ca28ddd6868b05fd1ddf49/train.zip),
[val.zip](https://huggingface.co/datasets/mapo80/stamps/resolve/998243bde1262ccb57ca28ddd6868b05fd1ddf49/val.zip)
и [test.zip](https://huggingface.co/datasets/mapo80/stamps/resolve/998243bde1262ccb57ca28ddd6868b05fd1ddf49/test.zip).
Сохраните их под этими именами в `artifacts/data-audit/mapo80/` и сверьте
[контрольные суммы архивов](18-mapo80-audit.md#проверенные-файлы).
Исходные имена train, val и test относятся к набору Mapo80.
Разбиение SealSign записано отдельно в `split.json`.

## Собрать данные и повторить эксперименты

Скрипт восстанавливает 2 577 страниц и сверяет SHA-256 каждой исходной страницы,
экспортированного PNG и YOLO-метки с зафиксированным manifest.

```console
python -m scripts.restore_s04_export --metadata artifacts/submission/s04-metadata --archives artifacts/data-audit/mapo80 --output artifacts/data-qc/s04-expanded-v1
```

Для обучения передайте папку экспорта в `scripts.train_s05`. Команды E00,
E01, E02 и E04, проверка val, выбор модели и финальная оценка приведены
в [протоколе обучения](04-training.md#конфигурация-расширенного-корпуса).
Используйте отдельную папку запусков, если рядом лежит пакет готовых весов.
Прежний учебный test из 9 страниц имеет отдельный экспорт у команды.
Основные результаты на новом test из 396 страниц повторяются из этого пакета
разметки и трёх исходных архивов.

Готовый E01 можно оценить без повторного обучения. В пакет включены пороги,
зафиксированные на val.

```console
python -m scripts.evaluate_s05 --experiment E01 --split test --data artifacts/data-qc/s04-expanded-v1/dataset.yaml --config configs/s05-yolo11n.json --weights artifacts/s05-runs/bundle-v1/model.pt --thresholds-from artifacts/s05-runs/bundle-v1/val-metrics.json --output artifacts/submission/replayed-test
```
