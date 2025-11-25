"""Unit tests for parsing Wi-Fi/Ethernet helpers in wifi_display_hat.

Scope (EN):
- Validates iwlist parsing, nmcli profile filtering, Ethernet normalization.
- Ensures interface summary aggregation marks correct statuses.
- Covers logging initialization to disk.

Zakres (PL):
- Weryfikuje parsowanie iwlist, filtrowanie profili nmcli i normalizację ETH.
- Sprawdza, że zbiorcze statusy interfejsów mają właściwe flagi.
- Testuje inicjalizację loggera plikowego.

File: tests/test_network_info.py
"""

# --- poprawka: dodanie testów helperów sieciowych — 2025-11-25T16:12:15Z ---

import logging
import sys
import types

import pytest


def _ensure_stubbed_dependencies() -> None:
    """Provide lightweight stand-ins for hardware modules."""

    if "displayhatmini" not in sys.modules:
        class _DummyDisplay:
            WIDTH = 320
            HEIGHT = 240

            def __init__(self, buffer):
                self.buffer = buffer

            def set_backlight(self, value):
                self.backlight = value

            def display(self):
                return self.buffer

        display_module = types.ModuleType("displayhatmini")
        display_module.DisplayHATMini = _DummyDisplay
        sys.modules["displayhatmini"] = display_module

    if "RPi" not in sys.modules:
        rpi_module = types.ModuleType("RPi")
        gpio_module = types.ModuleType("GPIO")
        gpio_module.BCM = 0
        gpio_module.IN = 1
        gpio_module.PUD_UP = 2
        gpio_module.LOW = 0

        def _noop(*args, **kwargs):
            return None

        gpio_module.setmode = _noop
        gpio_module.setup = _noop
        gpio_module.input = lambda pin: 1
        gpio_module.cleanup = _noop

        rpi_module.GPIO = gpio_module
        sys.modules["RPi"] = rpi_module
        sys.modules["RPi.GPIO"] = gpio_module

    if "PIL" not in sys.modules:
        pil_module = types.ModuleType("PIL")

        class _DummyImage:
            @staticmethod
            def new(mode, size):
                return {"mode": mode, "size": size}

        class _DummyImageDraw:
            class ImageDraw:
                def __init__(self, buffer):
                    self.buffer = buffer

                def rectangle(self, *_args, **_kwargs):
                    return None

                def text(self, *_args, **_kwargs):
                    return None

        class _DummyImageFont:
            @staticmethod
            def truetype(*_args, **_kwargs):
                return object()

            @staticmethod
            def load_default():
                return object()

        pil_module.Image = _DummyImage
        pil_module.ImageDraw = _DummyImageDraw
        pil_module.ImageFont = _DummyImageFont
        sys.modules["PIL"] = pil_module
        sys.modules["PIL.Image"] = _DummyImage
        sys.modules["PIL.ImageDraw"] = _DummyImageDraw
        sys.modules["PIL.ImageFont"] = _DummyImageFont


_ensure_stubbed_dependencies()
import wifi_display_hat  # noqa: E402  pylint: disable=wrong-import-position


class _DummyCompletedProcess:
    def __init__(self, stdout: str, returncode: int = 0):
        self.stdout = stdout
        self.returncode = returncode


def test_scan_wifi_iwlist_sorts_by_best_quality(monkeypatch):
    sample = """
          Cell 01 - Address: aa:bb
                    Quality=20/70  Signal level=-80 dBm
                    ESSID:"Cafe"
          Cell 02 - Address: cc:dd
                    Quality=40/70  Signal level=-70 dBm
                    ESSID:"Home"
          Cell 03 - Address: ee:ff
                    Quality=60/70  Signal level=-60 dBm
                    ESSID:"Cafe"
    """

    def _fake_run(cmd, **_kwargs):
        assert cmd[:2] == ["sudo", "iwlist"]
        return _DummyCompletedProcess(stdout=sample)

    monkeypatch.setattr(wifi_display_hat.subprocess, "run", _fake_run)

    networks = wifi_display_hat.scan_wifi_iwlist()
    assert [net.ssid for net in networks] == ["Cafe", "Home"]
    qualities = {net.ssid: net.quality for net in networks}
    assert qualities["Cafe"] == pytest.approx(int((60 / 70) * 100))


def test_get_saved_wifi_profiles_filters_wireless(monkeypatch):
    sample = """
Office:802-11-wireless
Lab:802-3-ethernet
Cafe:802-11-wireless
    """

    def _fake_run(cmd, **_kwargs):
        assert cmd[:3] == ["nmcli", "-t", "-f"]
        return _DummyCompletedProcess(stdout=sample)

    monkeypatch.setattr(wifi_display_hat.subprocess, "run", _fake_run)
    profiles = wifi_display_hat.get_saved_wifi_profiles()
    assert profiles == {"Office", "Cafe"}


def test_get_ethernet_details_normalizes_fields(monkeypatch):
    sample = {
        "IP4.ADDRESS[1]": "192.168.0.10/24",
        "IP4.GATEWAY": "192.168.0.1",
        "IP4.DNS[1]": "8.8.8.8",
        "IP4.METHOD": "auto",
        "GENERAL.STATE": "connected (100Mbps)",
    }
    monkeypatch.setattr(wifi_display_hat, "_parse_nmcli_device_show", lambda iface: sample)
    details = wifi_display_hat.get_ethernet_details("eth0")
    assert details.link_state == "UP"
    assert details.mode == "DHCP"
    assert details.ip == "192.168.0.10"
    assert details.gateway == "192.168.0.1"
    assert details.dns == "8.8.8.8"


def test_gather_interface_statuses_combines_wifi_and_eth(monkeypatch):
    monkeypatch.setattr(wifi_display_hat, "get_ip_address", lambda iface: "10.0.0.5" if iface == "wlan0" else "10.0.0.2")
    fake_eth = wifi_display_hat.EthernetDetails("UP", "STATIC", "10.0.0.2", "10.0.0.1", "1.1.1.1")
    monkeypatch.setattr(wifi_display_hat, "get_ethernet_details", lambda: fake_eth)
    statuses = wifi_display_hat.gather_interface_statuses("Office")
    wifi_status = next(item for item in statuses if item.name == "WiFi")
    eth_status = next(item for item in statuses if item.name == "ETH")
    assert wifi_status.status == "ONLINE"
    assert wifi_status.ip == "10.0.0.5"
    assert eth_status.description == "STATIC"
    assert eth_status.status == "ONLINE"


def test_setup_logger_writes_to_file(tmp_path, monkeypatch):
    log_file = tmp_path / "wifi_display.log"
    monkeypatch.setattr(wifi_display_hat, "LOG_FILE", log_file)
    logger = logging.getLogger("wifi_display")
    logger.handlers.clear()
    if hasattr(logger, "_wifi_display_configured"):
        delattr(logger, "_wifi_display_configured")
    wifi_display_hat.setup_logger()
    logger.info("Test log entry")
    for handler in logger.handlers:
        handler.flush()
    assert log_file.read_text().strip() != ""
