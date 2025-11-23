#!/usr/bin/env python3
import re
import subprocess
import time
from dataclasses import dataclass

from displayhatmini import DisplayHATMini
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont


# --- Konfiguracja GPIO dla przycisków Display HAT Mini ---

GPIO.setmode(GPIO.BCM)

BUTTON_X = 5    # góra
BUTTON_Y = 6    # dół
BUTTON_A = 16   # połącz
BUTTON_B = 24   # odśwież

GPIO.setup(BUTTON_X, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_Y, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)


@dataclass
class WifiNetwork:
    ssid: str
    quality: int | None


def scan_wifi_iwlist(iface: str = "wlan0") -> list[WifiNetwork]:
    result = subprocess.run(
        ["sudo", "iwlist", iface, "scan"],
        capture_output=True,
        text=True,
        check=True,
    )

    essid_re = re.compile(r'ESSID:"(.*)"')
    qual_re = re.compile(r"Quality=(\d+)/(\d+)")

    networks_raw = []

    ssid = None
    quality = None

    for line in result.stdout.splitlines():
        line = line.strip()

        m_qual = qual_re.search(line)
        if m_qual:
            try:
                q_val = int(m_qual.group(1))
                q_max = int(m_qual.group(2))
                quality = int(q_val * 100 / q_max)
            except:
                quality = None

        m_essid = essid_re.search(line)
        if m_essid:
            ssid = m_essid.group(1)
            if ssid:
                networks_raw.append(WifiNetwork(ssid, quality))
            ssid = None
            quality = None

    # wybór najlepszego AP dla każdego SSID
    best = {}
    for n in networks_raw:
        if n.ssid not in best or (n.quality or 0) > (best[n.ssid].quality or 0):
            best[n.ssid] = n

    networks = list(best.values())
    networks.sort(key=lambda x: (x.quality or 0), reverse=True)
    return networks


def get_active_ssid():
    result = subprocess.run(
        ["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"],
        capture_output=True,
        text=True,
        check=True,
    )

    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        active, ssid = line.split(":", 1)
        if active.lower() == "yes":
            return ssid
    return None


def connect_to_wifi(ssid: str) -> None:
    """
    Próba połączenia z podaną siecią przez nmcli jako root (sudo).
    """
    subprocess.run(
        ["sudo", "nmcli", "dev", "wifi", "connect", ssid],
        check=False,
    )


def main():
    width = DisplayHATMini.WIDTH
    height = DisplayHATMini.HEIGHT

    buffer = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(buffer)

    display = DisplayHATMini(buffer)
    display.set_backlight(1.0)

    # --- DUŻA CZCIONKA (22 px) ---
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            22
        )
    except:
        font = ImageFont.load_default()

    cursor = 0

    def redraw(networks, active_ssid, cursor_idx):
        draw.rectangle((0, 0, width, height), fill=(0, 0, 0))

        draw.text((5, 5), "Sieci Wi-Fi:", font=font, fill=(0, 200, 255))

        start_y = 40
        line_h = 30                     # większa czcionka = większy odstęp
        max_rows = (height - start_y) // line_h

        shown = networks[:max_rows]

        for idx, net in enumerate(shown):
            y = start_y + idx * line_h

            cursor_mark = ">" if idx == cursor_idx else " "
            active_mark = "*" if active_ssid == net.ssid else " "

            quality = f"{net.quality or 0}%"

            text = f"{cursor_mark}{active_mark} {net.ssid}   {quality}"
            draw.text((5, y), text, font=font, fill=(255, 255, 255))

        display.display()

    networks = scan_wifi_iwlist()
    active_ssid = get_active_ssid()
    redraw(networks, active_ssid, cursor)

    try:
        while True:
            if GPIO.input(BUTTON_X) == GPIO.LOW:   # góra
                cursor = max(0, cursor - 1)
                redraw(networks, active_ssid, cursor)
                time.sleep(0.25)

            if GPIO.input(BUTTON_Y) == GPIO.LOW:   # dół
                cursor = min(len(networks) - 1, cursor + 1)
                redraw(networks, active_ssid, cursor)
                time.sleep(0.25)

            if GPIO.input(BUTTON_B) == GPIO.LOW:   # odśwież
                networks = scan_wifi_iwlist()
                active_ssid = get_active_ssid()
                cursor = min(cursor, len(networks) - 1)
                redraw(networks, active_ssid, cursor)
                time.sleep(0.4)

            if GPIO.input(BUTTON_A) == GPIO.LOW:   # połącz
                chosen = networks[cursor].ssid

                draw.rectangle((0, 0, width, height), fill=(0, 0, 0))
                draw.text((5, 40), "Łączenie z:", font=font, fill=(255, 255, 255))
                draw.text((5, 80), chosen, font=font, fill=(255, 255, 0))
                display.display()

                connect_to_wifi(chosen)
                time.sleep(3)

                active_ssid = get_active_ssid()
                redraw(networks, active_ssid, cursor)
                time.sleep(0.4)

            time.sleep(0.05)

    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
        display.set_backlight(0.0)


if __name__ == "__main__":
    main()

