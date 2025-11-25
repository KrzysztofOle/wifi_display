"""Unit tests for ScreenManager navigation stack and delegation.

Scope (EN):
- Confirms push/pop logic, top-of-stack delegation and tick handling.
- Uses dummy draw/display objects to avoid hardware dependencies.

Zakres (PL):
- Potwierdza logikę push/pop, delegację metod i obsługę tick.
- Korzysta z atrap rysowania/wyświetlacza bez sprzętu.

File: tests/test_screen_manager.py
"""

# --- poprawka: testy ScreenManagera i obsługi przycisków — 2025-11-25T16:12:15Z ---

from __future__ import annotations

from dataclasses import dataclass

import wifi_display_hat


@dataclass
class _DummyDraw:
    def rectangle(self, *_args, **_kwargs):
        return None

    def text(self, *_args, **_kwargs):
        return None


class _DummyDisplay:
    def __init__(self):
        self.buffer = None

    def display(self):
        return self.buffer

    def set_backlight(self, *_args, **_kwargs):
        return None


class _TrackingScreen(wifi_display_hat.Screen):
    def __init__(self, manager):
        super().__init__(manager)
        self.events: list[str] = []

    def refresh_data(self):
        self.events.append("refresh")

    def render(self):
        self.events.append("render")

    def handle_button(self, button_name: str):
        self.events.append(f"button:{button_name}")

    def tick(self):
        self.events.append("tick")


def _make_manager():
    draw = _DummyDraw()
    display = _DummyDisplay()
    font = object()
    manager = wifi_display_hat.ScreenManager(
        width=320,
        height=240,
        draw=draw,
        display=display,
        font_large=font,
        font_medium=font,
        font_small=font,
    )
    manager.register_screen("dummy", _TrackingScreen)
    return manager


def test_screen_manager_push_creates_single_instance_and_calls_on_show():
    manager = _make_manager()
    manager.push("dummy")
    screen = manager.get_screen("dummy")
    assert screen.events == ["refresh", "render"]
    screen.events.clear()
    manager.push("dummy")
    assert screen.events == ["refresh", "render"]


def test_screen_manager_pop_restores_previous_screen():
    manager = _make_manager()
    manager.register_screen("second", _TrackingScreen)
    manager.push("dummy")
    manager.push("second")
    second = manager.get_screen("second")
    second.events.clear()
    manager.pop()
    assert second.events == []
    dummy = manager.get_screen("dummy")
    assert dummy.events[-2:] == ["refresh", "render"]
    manager.pop()
    assert dummy.events[-2:] == ["refresh", "render"]


def test_screen_manager_delegates_button_and_tick_to_top_screen():
    manager = _make_manager()
    manager.push("dummy")
    screen = manager.get_screen("dummy")
    screen.events.clear()
    manager.handle_button("A")
    manager.tick()
    assert screen.events == ["button:A", "tick"]


def test_ethernet_screen_button_a_opens_actions(monkeypatch):
    manager = wifi_display_hat.ScreenManager(
        width=320,
        height=240,
        draw=_DummyDraw(),
        display=_DummyDisplay(),
        font_large=object(),
        font_medium=object(),
        font_small=object(),
    )
    fake_eth = wifi_display_hat.EthernetDetails("UP", "DHCP", "10.0.0.2", "10.0.0.1", "1.1.1.1")
    monkeypatch.setattr(wifi_display_hat, "get_ethernet_details", lambda: fake_eth)
    manager.register_screen("eth", wifi_display_hat.EthernetScreen)
    manager.register_screen("eth_actions", wifi_display_hat.EthernetActionsScreen)
    manager.register_screen("eth_static_config", wifi_display_hat.EthernetStaticConfigScreen)
    manager.push("eth")
    actions = manager.get_screen("eth_actions")
    # zapobiegamy rzeczywistemu renderowaniu
    monkeypatch.setattr(actions, "render", lambda: None)
    manager.handle_button("A")
    assert manager._stack[-1] is actions


def test_wifi_screen_button_a_opens_actions(monkeypatch):
    manager = wifi_display_hat.ScreenManager(
        width=320,
        height=240,
        draw=_DummyDraw(),
        display=_DummyDisplay(),
        font_large=object(),
        font_medium=object(),
        font_small=object(),
    )
    monkeypatch.setattr(wifi_display_hat, "get_active_ssid", lambda: "Office")
    monkeypatch.setattr(wifi_display_hat, "get_ip_address", lambda iface: "10.0.0.5")
    monkeypatch.setattr(wifi_display_hat, "get_saved_wifi_profiles", lambda: {"Office"})
    monkeypatch.setattr(wifi_display_hat, "scan_wifi_iwlist", lambda: [])
    manager.register_screen("wifi", wifi_display_hat.WifiScreen)
    manager.register_screen("wifi_actions", wifi_display_hat.WifiActionsScreen)
    manager.push("wifi")
    actions = manager.get_screen("wifi_actions")
    monkeypatch.setattr(actions, "render", lambda: None)
    manager.handle_button("A")
    assert manager._stack[-1] is actions


def test_ethernet_actions_executes_handler(monkeypatch):
    called: dict[str, bool] = {}

    def _handler():
        called["ran"] = True
        return True, "OK"

    fake_action = wifi_display_hat.EthernetAction("Test", "Opis", _handler)
    monkeypatch.setattr(wifi_display_hat, "ETHERNET_ACTIONS", [fake_action])

    manager = wifi_display_hat.ScreenManager(
        width=320,
        height=240,
        draw=_DummyDraw(),
        display=_DummyDisplay(),
        font_large=object(),
        font_medium=object(),
        font_small=object(),
    )
    manager.register_screen("eth_actions", wifi_display_hat.EthernetActionsScreen)
    manager.push("eth_actions")
    screen = manager.get_screen("eth_actions")
    monkeypatch.setattr(screen, "render", lambda: None)
    monkeypatch.setattr(screen, "_show_status", lambda *_args, **_kwargs: None)
    screen.handle_button("A")
    assert called.get("ran") is True


def test_ethernet_actions_static_opens_config(monkeypatch):
    static_action = wifi_display_hat.EthernetAction(
        "Static",
        "desc",
        handler=None,
        screen="eth_static_config",
    )
    monkeypatch.setattr(wifi_display_hat, "ETHERNET_ACTIONS", [static_action])

    manager = wifi_display_hat.ScreenManager(
        width=320,
        height=240,
        draw=_DummyDraw(),
        display=_DummyDisplay(),
        font_large=object(),
        font_medium=object(),
        font_small=object(),
    )
    manager.register_screen("eth_actions", wifi_display_hat.EthernetActionsScreen)
    manager.register_screen("eth_static_config", wifi_display_hat.EthernetStaticConfigScreen)
    manager.push("eth_actions")
    actions = manager.get_screen("eth_actions")
    monkeypatch.setattr(actions, "render", lambda: None)
    actions.handle_button("A")
    top = manager._stack[-1]
    assert isinstance(top, wifi_display_hat.EthernetStaticConfigScreen)


def test_static_config_screen_applies_changes(monkeypatch):
    base_cfg = wifi_display_hat.StaticIpConfig([192, 168, 0, 10], 24, [192, 168, 0, 1], [8, 8, 8, 8])
    monkeypatch.setattr(wifi_display_hat, "STATIC_IP_CONFIG", base_cfg)

    applied: dict[str, wifi_display_hat.StaticIpConfig] = {}

    def _fake_set(cfg):
        applied["cfg"] = wifi_display_hat.StaticIpConfig(list(cfg.ip), cfg.prefix, list(cfg.gateway), list(cfg.dns))

    monkeypatch.setattr(wifi_display_hat, "set_static_config", _fake_set)
    monkeypatch.setattr(wifi_display_hat, "_configure_eth_static", lambda: (True, "OK"))

    manager = wifi_display_hat.ScreenManager(
        width=320,
        height=240,
        draw=_DummyDraw(),
        display=_DummyDisplay(),
        font_large=object(),
        font_medium=object(),
        font_small=object(),
    )
    manager.register_screen("eth_static_config", wifi_display_hat.EthernetStaticConfigScreen)
    manager.push("eth_static_config")
    screen = manager.get_screen("eth_static_config")
    monkeypatch.setattr(screen, "render", lambda: None)
    monkeypatch.setattr(screen, "_show_feedback", lambda *_args, **_kwargs: None)

    screen.cursor = 0
    screen.handle_button("UP")
    screen.cursor = len(screen.segments) - 1
    screen.handle_button("A")

    assert applied["cfg"].ip[0] == (base_cfg.ip[0] + 1) % 256


# --- poprawka: testy menu narzędzi — 2025-11-25T17:36:04Z ---
def test_main_screen_opens_tools_screen(monkeypatch):
    monkeypatch.setattr(
        wifi_display_hat,
        "gather_interface_statuses",
        lambda active: [
            wifi_display_hat.InterfaceStatus(
                name="TOOLS",
                description="Reboot",
                metric="MENU",
                ip="—",
                status="READY",
            )
        ],
    )
    monkeypatch.setattr(wifi_display_hat, "get_active_ssid", lambda: None)

    manager = wifi_display_hat.ScreenManager(
        width=320,
        height=240,
        draw=_DummyDraw(),
        display=_DummyDisplay(),
        font_large=object(),
        font_medium=object(),
        font_small=object(),
    )
    manager.register_screen("main", wifi_display_hat.MainScreen)
    manager.register_screen("tools", wifi_display_hat.ToolsScreen)
    manager.push("main")
    tools = manager.get_screen("tools")
    manager.handle_button("A")
    assert manager._stack[-1] is tools


def test_tools_screen_executes_selected_action(monkeypatch):
    captured: dict[str, list[str]] = {}

    def _fake_runner(command):
        captured["cmd"] = command
        return True, "OK"

    monkeypatch.setattr(wifi_display_hat, "run_system_action", _fake_runner)

    manager = wifi_display_hat.ScreenManager(
        width=320,
        height=240,
        draw=_DummyDraw(),
        display=_DummyDisplay(),
        font_large=object(),
        font_medium=object(),
        font_small=object(),
    )
    manager.register_screen("tools", wifi_display_hat.ToolsScreen)
    manager.push("tools")
    screen = manager.get_screen("tools")
    monkeypatch.setattr(screen, "_show_feedback", lambda *_args, **_kwargs: None)
    screen.handle_button("A")
    assert captured["cmd"] == wifi_display_hat.TOOLS_ACTIONS[0].command
