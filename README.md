# icom-lan

Python-библиотека для управления трансиверами Icom по LAN (сетевой протокол).

Управляй IC-7610, IC-7300, IC-705, IC-9700 и другими Icom-трансиверами напрямую по сети — без wfview, без RS-BA1, без GUI.

## Зачем

- **wfview** — отличный, но это целое GUI-приложение. Иногда нужно просто `radio.frequency = 14_074_000` из скрипта.
- **RS-BA1** — платный, Windows-only, закрытый.
- **rigctld/hamlib** — работает по serial, для LAN нужен wfview как прокси.
- **Эта библиотека** — чистый Python, прямое подключение к радио по UDP, никаких зависимостей-посредников.

## Пример

```python
from icom_lan import IcomRadio

async with IcomRadio("192.168.1.100", username="user", password="pass") as radio:
    freq = await radio.get_frequency()
    print(f"Частота: {freq / 1e6:.3f} MHz")
    
    mode = await radio.get_mode()
    print(f"Режим: {mode.name}")
    
    s = await radio.get_s_meter()
    print(f"S-метр: {s}")
    
    await radio.set_frequency(7_074_000)
    await radio.set_mode("USB")
```

## Статус

✅ **Фаза 1-2 завершена** — CI-V команды работают (get/set frequency, mode, power, meters, PTT).

🚧 **В разработке:** Audio streaming (Фаза 3).

## Лицензия

MIT

## Благодарности

Протокол реверс-инжиниринг основан на анализе исходного кода [wfview](https://gitlab.com/eliggett/wfview) (GPLv3).
Эта библиотека — независимая чистая реализация на Python, не содержит код wfview.
