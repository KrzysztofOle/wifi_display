#!/usr/bin/env python3
import time

from displayhatmini import DisplayHATMini
from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    # Rozmiar ekranu z biblioteki
    width = DisplayHATMini.WIDTH
    height = DisplayHATMini.HEIGHT

    # Bufor obrazu (to jest "buffer" wymagany przez DisplayHATMini)
    buffer = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(buffer)

    # Inicjalizacja wyświetlacza z buforem
    display = DisplayHATMini(buffer)
    display.set_backlight(1.0)  # pełna jasność

    # Tło na czarno
    draw.rectangle((0, 0, width, height), fill=(0, 0, 0))

    text = "Hello Wi-Fi!"

    # Czcionka – najpierw próbujemy DejaVu, jak brak to domyślna
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            20,
        )
    except Exception:
        font = ImageFont.load_default()

    # Pillow 12: zamiast draw.textsize -> draw.textbbox
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = (width - tw) // 2
    y = (height - th) // 2

    # Biały tekst na czarnym tle
    draw.text((x, y), text, font=font, fill=(255, 255, 255))

    # Wyślij bufor na ekran
    display.display()

    try:
        # Trzymaj obraz, aż wciśniesz Ctrl+C
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        display.set_backlight(0.0)


if __name__ == "__main__":
    main()

