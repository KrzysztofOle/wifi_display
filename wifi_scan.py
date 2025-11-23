#!/usr/bin/env python3
import subprocess
from dataclasses import dataclass


@dataclass
class WifiNetwork:
    active: bool
    ssid: str
    signal: int


def scan_wifi() -> list[WifiNetwork]:
    """
    Używa nmcli do pobrania listy sieci Wi-Fi.
    Zwraca listę WifiNetwork (aktywna?, SSID, siła).
    """
    # -t: format "prostoliniowy"
    # -f: wybieramy tylko interesujące nas pola
    cmd = ["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL", "dev", "wifi"]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )

    networks: list[WifiNetwork] = []

    for line in result.stdout.splitlines():
        if not line.strip():
            continue

        # Format: ACTIVE:SSID:SIGNAL
        parts = line.split(":", maxsplit=2)
        if len(parts) != 3:
            continue

        active_str, ssid, signal_str = parts
        active = active_str.upper() == "YES"

        try:
            signal = int(signal_str)
        except ValueError:
            signal = 0

        # Pomijamy puste SSID (ukryte sieci) na początek
        if not ssid:
            continue

        networks.append(WifiNetwork(active=active, ssid=ssid, signal=signal))

    return networks


def main() -> None:
    try:
        networks = scan_wifi()
    except subprocess.CalledProcessError as e:
        print("Błąd przy wywołaniu nmcli:")
        print(e)
        print(e.stderr)
        return

    if not networks:
        print("Brak widocznych sieci Wi-Fi.")
        return

    # Posortujmy od najsilniejszego sygnału
    networks.sort(key=lambda n: n.signal, reverse=True)

    print("Znalezione sieci Wi-Fi:")
    print()
    for net in networks:
        mark = "*" if net.active else " "
        print(f"{mark} {net.ssid:30} {net.signal:3d} %")


if __name__ == "__main__":
    main()

