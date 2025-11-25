#!/usr/bin/env python3
"""
High-level UI controller for Display HAT Mini Wi-Fi manager.

Features (EN):
- Manages a stack of screens (main overview and Wi-Fi module).
- Provides navigation helpers bound to physical buttons (X/Y/A/B).
- Integrates Wi-Fi scanning and connection handling with nmcli.

Funkcje (PL):
- Zarządza stosem ekranów (ekran główny oraz moduł Wi-Fi).
- Udostępnia obsługę nawigacji powiązaną z przyciskami X/Y/A/B.
- Integruje skanowanie i łączenie sieci Wi-Fi poprzez nmcli.

File: wifi_display_hat.py
"""

import re
import subprocess
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

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
    is_active: bool = False
    is_saved: bool = False


@dataclass
class InterfaceStatus:
    name: str
    description: str
    metric: str
    ip: str
    status: str


# --- poprawka: struktura danych dla interfejsu Ethernet — 2025-11-25T16:12:15Z ---
@dataclass
class EthernetDetails:
    link_state: str
    mode: str
    ip: str
    gateway: str
    dns: str


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


# --- poprawka: dodanie helperów profili Wi-Fi i adresów IP — 2025-11-24T20:49:24+01:00 ---
def get_saved_wifi_profiles() -> set[str]:
    """
    Zwraca zestaw nazw profili Wi-Fi zapisanych w NetworkManagerze.
    """
    result = subprocess.run(
        ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"],
        capture_output=True,
        text=True,
        check=True,
    )
    profiles = set()
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        name, conn_type = line.split(":", 1)
        if conn_type.strip() == "802-11-wireless":
            profiles.add(name.strip())
    return profiles


def get_ip_address(interface: str) -> Optional[str]:
    """
    Pobiera adres IPv4 przypisany do wskazanego interfejsu.
    """
    result = subprocess.run(
        ["ip", "-4", "addr", "show", interface],
        capture_output=True,
        text=True,
        check=False,
    )
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("inet "):
            return line.split()[1].split("/")[0]
    return None


def gather_interface_statuses(active_ssid: Optional[str]) -> List[InterfaceStatus]:
    """
    Buduje listę statusów interfejsów na potrzeby ekranu głównego.
    """
    wifi_ip = get_ip_address("wlan0") or "—"
    wifi_status = "ONLINE" if active_ssid else "OFFLINE"
    wifi_desc = active_ssid or "Brak połączenia"
    wifi_metric = "—"
    eth_details = get_ethernet_details()
    eth_status = "ONLINE" if eth_details.link_state.upper() == "UP" else "OFFLINE"
    statuses = [
        InterfaceStatus(
            name="WiFi",
            description=wifi_desc,
            metric=wifi_metric,
            ip=wifi_ip,
            status=wifi_status,
        ),
        InterfaceStatus(
            name="ETH",
            description=eth_details.mode,
            metric=eth_details.link_state,
            ip=eth_details.ip,
            status=eth_status,
        ),
        InterfaceStatus(
            name="ZeroTier",
            description="—",
            metric="—",
            ip="—",
            status="WIP",
        ),
    ]
    return statuses


# --- poprawka: definicja bazowego ekranu oraz menedżera — 2025-11-24T20:49:24+01:00 ---
class Screen:
    def __init__(self, manager: "ScreenManager"):
        self.manager = manager

    def on_show(self) -> None:
        self.refresh_data()
        self.render()

    def refresh_data(self) -> None:
        raise NotImplementedError

    def render(self) -> None:
        raise NotImplementedError

    def handle_button(self, button_name: str) -> None:
        raise NotImplementedError

    def tick(self) -> None:
        """
        Opcjonalny hook aktualizujący logikę ekranów.
        """


class ScreenManager:
    def __init__(
        self,
        *,
        width: int,
        height: int,
        draw: ImageDraw.ImageDraw,
        display: DisplayHATMini,
        font_large,
        font_medium,
        font_small,
    ):
        self.width = width
        self.height = height
        self.draw = draw
        self.display = display
        self.font_large = font_large
        self.font_medium = font_medium
        self.font_small = font_small

        self._factories: Dict[str, Callable[["ScreenManager"], Screen]] = {}
        self._instances: Dict[str, Screen] = {}
        self._stack: List[Screen] = []

    def register_screen(self, name: str, factory: Callable[["ScreenManager"], Screen]) -> None:
        self._factories[name] = factory

    def get_screen(self, name: str) -> Screen:
        if name not in self._instances:
            if name not in self._factories:
                raise KeyError(f"Brak fabryki dla ekranu '{name}'")
            self._instances[name] = self._factories[name](self)
        return self._instances[name]

    def push(self, name: str) -> None:
        screen = self.get_screen(name)
        self._stack.append(screen)
        screen.on_show()

    def pop(self) -> None:
        if len(self._stack) > 1:
            self._stack.pop()
            self._stack[-1].on_show()

    def handle_button(self, button_name: str) -> None:
        if self._stack:
            self._stack[-1].handle_button(button_name)

    def tick(self) -> None:
        if self._stack:
            self._stack[-1].tick()

    @property
    def draw_context(self) -> ImageDraw.ImageDraw:
        return self.draw

    def clear(self) -> None:
        self.draw.rectangle((0, 0, self.width, self.height), fill=(0, 0, 0))

    def show(self) -> None:
        self.display.display()


# --- poprawka: ekran główny i ekran Wi-Fi — 2025-11-24T20:49:24+01:00 ---
class MainScreen(Screen):
    def __init__(self, manager: "ScreenManager"):
        super().__init__(manager)
        self.interfaces: List[InterfaceStatus] = []
        self.cursor = 0
        self.last_refresh = 0.0
        self.refresh_interval = 5.0

    def refresh_data(self) -> None:
        active_ssid = get_active_ssid()
        self.interfaces = gather_interface_statuses(active_ssid)
        if self.interfaces:
            self.cursor = max(0, min(self.cursor, len(self.interfaces) - 1))
        else:
            self.cursor = 0
        self.last_refresh = time.monotonic()

    def render(self) -> None:
        draw = self.manager.draw_context
        self.manager.clear()
        draw.rectangle((0, 0, self.manager.width, 30), fill=(0, 100, 255))
        draw.text((5, 3), "INTERFEJSY:", font=self.manager.font_large, fill=(0, 0, 0))

        start_y = 40
        line_h = 34
        max_rows = (self.manager.height - start_y) // line_h
        for idx, iface in enumerate(self.interfaces[:max_rows]):
            y = start_y + idx * line_h
            prefix = ">" if idx == self.cursor else " "
            text_main = f"{prefix}{iface.name} {iface.status}"
            text_sub = f"{iface.description} | {iface.ip}"
            draw.text((5, y), text_main, font=self.manager.font_large, fill=(255, 255, 255))
            draw.text((5, y + 20), text_sub, font=self.manager.font_small, fill=(150, 150, 150))
        self.manager.show()

    def handle_button(self, button_name: str) -> None:
        if button_name == "UP":
            if self.interfaces:
                self.cursor = max(0, self.cursor - 1)
                self.render()
        elif button_name == "DOWN":
            if self.interfaces:
                self.cursor = min(len(self.interfaces) - 1, self.cursor + 1)
                self.render()
        elif button_name == "A":
            selected = self.interfaces[self.cursor] if self.interfaces else None
            if selected and selected.name == "WiFi":
                self.manager.push("wifi")
            elif selected and selected.name == "ETH":
                self.manager.push("eth")
        elif button_name == "B":
            # B to miejsce na narzędzia diagnostyczne (w przyszłości)
            pass

    def tick(self) -> None:
        if time.monotonic() - self.last_refresh > self.refresh_interval:
            self.refresh_data()
            self.render()


class WifiScreen(Screen):
    def __init__(self, manager: "ScreenManager"):
        super().__init__(manager)
        self.networks: List[WifiNetwork] = []
        self.cursor = 0
        self.last_refresh = 0.0
        self.refresh_interval = 10.0

    def refresh_data(self) -> None:
        self.networks = scan_wifi_iwlist()
        active_ssid = get_active_ssid()
        saved_profiles = get_saved_wifi_profiles()
        for net in self.networks:
            net.is_active = net.ssid == active_ssid
            net.is_saved = net.ssid in saved_profiles
        if self.networks:
            self.cursor = max(0, min(self.cursor, len(self.networks) - 1))
        else:
            self.cursor = 0
        self.last_refresh = time.monotonic()

    def render(self) -> None:
        draw = self.manager.draw_context
        self.manager.clear()
        draw.rectangle((0, 0, self.manager.width, 30), fill=(0, 100, 255))
        draw.text((5, 3), "SIECI WI-FI:", font=self.manager.font_large, fill=(0, 0, 0))

        start_y = 45
        line_h = 32
        max_rows = (self.manager.height - start_y) // line_h
        for idx, net in enumerate(self.networks[:max_rows]):
            y = start_y + idx * line_h
            cursor_mark = ">" if idx == self.cursor else " "
            active_mark = "★" if net.is_active else " "
            saved_label = "SAVED" if net.is_saved else "OPEN"
            status_line = (
                f"{cursor_mark}{active_mark} {net.ssid:<12} "
                f"{(net.quality or 0):>3}% {saved_label}"
            )
            draw.text((5, y), status_line, font=self.manager.font_medium, fill=(255, 255, 255))
        self.manager.show()

    def handle_button(self, button_name: str) -> None:
        if button_name == "UP":
            if self.networks:
                self.cursor = max(0, self.cursor - 1)
                self.render()
        elif button_name == "DOWN":
            if self.networks:
                self.cursor = min(len(self.networks) - 1, self.cursor + 1)
                self.render()
        elif button_name == "A":
            self._connect_selected()
        elif button_name == "B":
            self.manager.pop()

    def _connect_selected(self) -> None:
        if not self.networks:
            return
        chosen = self.networks[self.cursor]
        draw = self.manager.draw_context
        self.manager.clear()
        draw.text((5, 40), "Łączenie z:", font=self.manager.font_large, fill=(255, 255, 255))
        draw.text((5, 80), chosen.ssid, font=self.manager.font_large, fill=(255, 255, 0))
        self.manager.show()
        connect_to_wifi(chosen.ssid)
        time.sleep(2)
        self.refresh_data()
        self.render()

    def tick(self) -> None:
        if time.monotonic() - self.last_refresh > self.refresh_interval:
            self.refresh_data()
            self.render()


# --- poprawka: szczegóły i ekran interfejsu Ethernet — 2025-11-25T16:12:15Z ---
def _parse_nmcli_device_show(interface: str) -> Dict[str, str]:
    try:
        result = subprocess.run(
            ["nmcli", "device", "show", interface],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return {}
    if result.returncode != 0:
        return {}
    data: Dict[str, str] = {}
    for line in result.stdout.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def get_ethernet_details(interface: str = "eth0") -> EthernetDetails:
    data = _parse_nmcli_device_show(interface)
    ip_raw = data.get("IP4.ADDRESS[1]", "—")
    ip = ip_raw.split("/")[0] if ip_raw and "/" in ip_raw else (ip_raw or "—")
    gateway = data.get("IP4.GATEWAY", "—")
    dns = data.get("IP4.DNS[1]", "—")
    mode_raw = data.get("IP4.METHOD", "unknown")
    link_raw = data.get("GENERAL.STATE", "disconnected")
    mode = mode_raw.replace("manual", "STATIC").replace("auto", "DHCP").upper()
    link_state = "UP" if "connected" in link_raw.lower() else "DOWN"
    if mode not in {"STATIC", "DHCP"}:
        mode = mode_raw.upper()
    if ip == "—":
        fallback_ip = get_ip_address(interface)
        if fallback_ip:
            ip = fallback_ip
    return EthernetDetails(
        link_state=link_state,
        mode=mode,
        ip=ip or "—",
        gateway=gateway or "—",
        dns=dns or "—",
    )


class EthernetScreen(Screen):
    def __init__(self, manager: "ScreenManager"):
        super().__init__(manager)
        self.details = EthernetDetails("DOWN", "UNKNOWN", "—", "—", "—")
        self.last_refresh = 0.0
        self.refresh_interval = 5.0

    def refresh_data(self) -> None:
        self.details = get_ethernet_details()
        self.last_refresh = time.monotonic()

    def render(self) -> None:
        draw = self.manager.draw_context
        self.manager.clear()
        draw.rectangle((0, 0, self.manager.width, 30), fill=(0, 100, 255))
        draw.text((5, 3), "ETHERNET", font=self.manager.font_large, fill=(0, 0, 0))

        lines = [
            f"Status: {self.details.link_state}",
            f"Tryb: {self.details.mode}",
            f"IP: {self.details.ip}",
            f"Gateway: {self.details.gateway}",
            f"DNS: {self.details.dns}",
        ]
        y = 50
        for text in lines:
            draw.text((5, y), text, font=self.manager.font_medium, fill=(255, 255, 255))
            y += 28
        draw.text((5, self.manager.height - 20), "A=odśwież  B=powrót", font=self.manager.font_small, fill=(120, 120, 120))
        self.manager.show()

    def handle_button(self, button_name: str) -> None:
        if button_name == "A":
            self.refresh_data()
            self.render()
        elif button_name == "B":
            self.manager.pop()

    def tick(self) -> None:
        if time.monotonic() - self.last_refresh > self.refresh_interval:
            self.refresh_data()
            self.render()


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

    try:
        font_large = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            22
        )
    except:
        font_large = ImageFont.load_default()

    # --- poprawka: dodanie czcionki pośredniej — 2025-11-24T20:49:24+01:00 ---
    try:
        font_medium = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            18
        )
    except:
        font_medium = ImageFont.load_default()

    font_small = ImageFont.load_default()

    # --- poprawka: implementacja menedżera ekranów — 2025-11-24T20:49:24+01:00 ---
    manager = ScreenManager(
        width=width,
        height=height,
        draw=draw,
        display=display,
        font_large=font_large,
        font_medium=font_medium,
        font_small=font_small,
    )
    manager.register_screen("main", MainScreen)
    manager.register_screen("wifi", WifiScreen)
    manager.register_screen("eth", EthernetScreen)
    manager.push("main")

    button_map: Dict[int, str] = {
        BUTTON_X: "UP",
        BUTTON_Y: "DOWN",
        BUTTON_A: "A",
        BUTTON_B: "B",
    }
    debounce = {
        "UP": 0.0,
        "DOWN": 0.0,
        "A": 0.0,
        "B": 0.0,
    }
    debounce_delay = 0.25

    try:
        while True:
            now = time.monotonic()
            for pin, name in button_map.items():
                if GPIO.input(pin) == GPIO.LOW and now - debounce[name] > debounce_delay:
                    manager.handle_button(name)
                    debounce[name] = now
            manager.tick()
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
        display.set_backlight(0.0)


if __name__ == "__main__":
    main()
