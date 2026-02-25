# icom-lan

Python-библиотека для управления трансиверами Icom по LAN (сетевой протокол).

Управляй IC-7610, IC-7300, IC-705, IC-9700 и другими Icom-трансиверами напрямую по сети — без wfview, без RS-BA1, без GUI.

## Зачем

- **wfview** — отличный, но это целое GUI-приложение. Иногда нужно просто `radio.frequency = 14_074_000` из скрипта.
- **RS-BA1** — платный, Windows-only, закрытый.
- **rigctld/hamlib** — работает по serial, для LAN нужен wfview как прокси.
- **Эта библиотека** — чистый Python, прямое подключение к радио по UDP, никаких зависимостей-посредников.

## Пример (цель)

```python
from icom_lan import IcomRadio

async with IcomRadio("192.168.1.100") as radio:
    print(f"Частота: {radio.frequency / 1e6:.3f} MHz")
    print(f"Режим: {radio.mode}")
    print(f"S-метр: {radio.s_meter} dBm")

    radio.frequency = 7_074_000
    radio.mode = "USB"
    radio.power = 50  # ватт
```

## Статус

🚧 **Ранняя стадия разработки** — протокол исследуется, API проектируется.

## Лицензия

MIT

## Благодарности

Протокол реверс-инжиниринг основан на анализе исходного кода [wfview](https://gitlab.com/eliggett/wfview) (GPLv3).
Эта библиотека — независимая чистая реализация на Python, не содержит код wfview.
