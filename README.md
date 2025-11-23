# 📟 WiFi Display Manager for Raspberry Pi  
### Sterowanie sieciami Wi-Fi z poziomu wyświetlacza Pimoroni Display HAT Mini

Projekt umożliwia zarządzanie sieciami Wi-Fi na Raspberry Pi Zero 2W  
bez klawiatury i monitora — tylko za pomocą 1.3" wyświetlacza HAT Mini i przycisków.

---

## 🚀 Funkcje

- 🔍 Skanowanie dostępnych sieci Wi-Fi (`iwlist`)
- 📶 Wyświetlanie listy sieci z dużą czcionką
- ⭐ Oznaczenie aktualnie podłączonej sieci
- 🎛 Nawigacja przyciskami:
  - X — góra  
  - Y — dół  
  - B — odśwież  
  - A — połącz  
- 🔓 Obsługa `sudo nmcli` (łączenie między zapisanymi profilami)
- 🔁 Autostart usługi systemd po starcie Raspberry
- 💡 Prosty i czytelny interfejs na ekranie 240×240

---

## 📦 Wymagania

### Sprzęt
- Raspberry Pi Zero 2W (lub inne RPi)
- Pimoroni Display HAT Mini
- Połączenie Wi-Fi

### Oprogramowanie
- Raspberry Pi OS Lite
- Python 3.11+
- python3-venv, pip
- NetworkManager
- Biblioteki:
  - displayhatmini
  - Pillow
  - RPi.GPIO

---

## 🛠 Instalacja środowiska

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip network-manager
```

Utworzenie virtualenv:

```bash
cd ~/wifi_display
python3 -m venv .venv
source .venv/bin/activate
pip install displayhatmini pillow RPi.GPIO
```

---

## 📜 Uruchomienie aplikacji

```bash
cd ~/wifi_display
source .venv/bin/activate
python wifi_display_hat.py
```

---

## 🔐 Uprawnienia `sudo nmcli`

Aplikacja używa:

```bash
sudo nmcli dev wifi connect "SSID"
```

Dodaj wyjątek sudoers:

```bash
sudo visudo
```

Dopisz:

```
krzysztof ALL=(ALL) NOPASSWD: /usr/bin/nmcli
```

---

## 🔁 Autostart (systemd)

Utwórz usługę:

```bash
sudo nano /etc/systemd/system/wifi-menu.service
```

Wklej:

```
[Unit]
Description=Wi-Fi Menu on Display HAT Mini
After=network.target

[Service]
Type=simple
User=krzysztof
WorkingDirectory=/home/krzysztof/wifi_display
ExecStart=/home/krzysztof/wifi_display/.venv/bin/python /home/krzysztof/wifi_display/wifi_display_hat.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Włącz usługę:

```bash
sudo systemctl daemon-reload
sudo systemctl enable wifi-menu.service
sudo systemctl start wifi-menu.service
```

---

## 🧭 Sterowanie

| Przycisk | Funkcja |
|---------|---------|
| X | przewiń w górę |
| Y | przewiń w dół |
| B | odśwież |
| A | połącz |

---

## 🔧 Struktura projektu

```
wifi_display/
├── wifi_display_hat.py
├── wifi_scan.py
├── wifi_scan_iwlist.py
├── hello_display.py
├── .gitignore
└── README.md
```

---

## 📚 Jak działa aplikacja?

- Skan Wi-Fi: `sudo iwlist wlan0 scan`
- Sortowanie według siły sygnału
- Renderowanie UI przez PIL + DisplayHATMini
- Reakcja na przyciski przez GPIO
- Automatyczne przełączanie sieci przez `sudo nmcli`

---

## 📝 Plany rozwoju

- [ ] Ikony siły sygnału
- [ ] Wprowadzanie hasła na ekranie
- [ ] Ekran statusu (IP, RSSI, uptime)
- [ ] Tryb offline/diagnostyczny
- [ ] Wersja angielska README

---

## 👤 Autor

**Krzysztof Olejnik**  
Projekt opracowany na Raspberry Pi Zero 2W  
przy wsparciu ChatGPT 🚀

---

## ⭐ Licencja

MIT — pełna dowolność użycia i modyfikacji.
