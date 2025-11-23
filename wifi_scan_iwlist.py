#!/usr/bin/env python3
import re
import subprocess
from dataclasses import dataclass


@dataclass
class WifiNetwork:
    ssid: str
    frequency_ghz: float | None
    quality: int | None  # 0–100, jeśli uda się policzyć


def scan_wifi_iwlist(iface: str = "wlan0") -> list[WifiNetwork]:
    # uruchamiamy: sudo iwlist wlan0 scan
    result = subprocess.run(
        ["sudo", "iwlist", iface, "scan"],
        capture_output=True,
        text=True,
        check=True,
    )

    networks: list[WifiNetwork] = []

    essid_re = re.compile(r'ESSID:"(.*)"')
    freq_re = re.compile(r"Frequency:([0-9.]+) GHz")
    qual_re = re.compile(r"Quality=(\d+)/(\d+)")

    ssid = None
    freq = None
    quality = None

    for line in result.stdout.splitlines():
        line = line.strip()

        m_freq = freq_re.search(line)
        if m_freq:
            try:
                freq = float(m_freq.group(1))
            except ValueError:
                freq = None

        m_qual = qual_re.search(line)
        if m_qual:
            try:
                q_val = int(m_qual.group(1))
                q_max = int(m_qual.group(2))
                quality = int(q_val * 100 / q_max)
            except ValueError:
                quality = None

        m_essid = essid_re.search(line)
        if m_essid:
            ssid = m_essid.group(1)

            # gdy mamy SSID, zapisujemy bieżący „pakiet” info
            if ssid:
                networks.append(
                    WifiNetwork(
                        ssid=ssid,
                        frequency_ghz=freq,
                        quality=quality,
                    )
                )

            # reset na następny AP
            ssid = None
            freq = None
            quality = None

    return networks


def main() -> None:
    try:
        nets = scan_wifi_iwlist("wlan0")
    except subprocess.CalledProcessError as e:
        print("Błąd przy wywołaniu iwlist:")
        print(e)
        print(e.stderr)
        return

    if not nets:
        print("Brak widocznych sieci (iwlist).")
        return

    # sortowanie: najpierw jakość, potem nazwa
    nets.sort(key=lambda n: (n.quality or 0), reverse=True)

    print("Znalezione sieci wg iwlist:\n")
    for n in nets:
        q = f"{n.quality:3d} %" if n.quality is not None else "  ? %"
        f = f"{n.frequency_ghz:.3f} GHz" if n.frequency_ghz is not None else "   ? GHz"
        print(f"{n.ssid:20}  {f}  {q}")


if __name__ == "__main__":
    main()

