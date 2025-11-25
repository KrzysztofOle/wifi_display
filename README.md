# 📟 WiFi Display Manager for Raspberry Pi

## Sterowanie sieciami Wi-Fi z poziomu wyświetlacza Pimoroni Display HAT Mini

Projekt umożliwia zarządzanie sieciami Wi-Fi na Raspberry Pi Zero 2W  
bez klawiatury i monitora — tylko za pomocą 1.3" wyświetlacza HAT Mini i przycisków.

---

## 🚀 Funkcje

- 🔍 Skanowanie dostępnych sieci Wi-Fi (`iwlist`)
- 📶 Wyświetlanie listy sieci z dużą czcionką
- ⭐ Oznaczenie aktualnie połączonej sieci
- 🎛 Nawigacja przyciskami: X/Y – wybór, A – połącz, B – odśwież
- 🔓 Obsługa `nmcli`
- 🔁 Autostart systemd
- 💡 Czytelny UI
- 🌐 Podgląd statusu Ethernet (link, tryb, adres IP)
- 🛠 Menu akcji Ethernet (DHCP/Static/DHCP server)
- 🧾 Logowanie zdarzeń do pliku `wifi_display.log`

### Sterowanie usługą `wifi-menu.service`

| Co chcesz zrobić | Komenda |
|------------------|---------|
| Zatrzymać aplikację teraz | `sudo systemctl stop wifi-menu.service` |
| Wyłączyć autostart | `sudo systemctl disable wifi-menu.service` |
| Sprawdzić status | `systemctl status wifi-menu.service` |
| Ręcznie uruchomić w przyszłości | `sudo systemctl start wifi-menu.service` |
| Przywrócić autostart | `sudo systemctl enable wifi-menu.service` |

---

## 📦 Wymagania

(same as earlier...)

---

## 🧩 **Plan aplikacji – kolejny krok (multi-network manager)**

### **1. Ekran główny – podsumowanie wszystkich połączeń**

Po uruchomieniu aplikacji użytkownik widzi ekran główny z listą dostępnych interfejsów:

| Interfejs | Opis / Nazwa | Siła / Tryb | Adres IP | Status |
|----------|---------------|-------------|----------|--------|
| WiFi     | HASKO         | 70%         | 192.168.9.33 | ONLINE |
| ETH      | —             | STATIC      | 192.168.2.2 | LINK UP |
| ZeroTier | 2873fd…b48a   | —           | 10.14.55.30 | ONLINE |

**Sterowanie:**

- `X/Y` – wybór interfejsu  
- `A` – szczegóły modułu  
- `B` – narzędzia diagnostyczne (ping, skan hostów)

---

### 2. Moduł Wi‑Fi

#### Widok listy sieci':'

- Lista SSID + siła sygnału
- Aktualna sieć oznaczona `★`
- Informacja "SAVED" jeśli istnieje profil

#### Akcje':'

- `A` – połączenie (z profilem lub w przyszłości hasło)
- `B` – odświeżanie
- Zaplanowane:
  - [ ] zapomnienie sieci
  - [ ] szczegóły sieci (RSSI, kanał)
  - [ ] przełączanie profili

---

### 3. Moduł Ethernet (ETH)

#### Widok

- LINK UP/DOWN  
- Tryb: STATIC / DHCP CLIENT / DHCP SERVER  
- Aktualne IP/GW
- `A` – otwiera „Akcje Ethernet”
- `B` – powrót

#### Akcje

| Tryb | Opis |
|------|------|
| DHCP client | Pobiera IP z routera |
| Static | Ręczne ustawienia IP |
| DHCP server | RPi przydziela adresy innym |

Wprowadzanie adresów planowane jako edycja IP po oktetach.

#### Akcje Ethernet – ekran

- Lista trybów (DHCP client / Static / DHCP server) z opisami.
- `A` – wykonuje akcję (nmcli: auto/manual/shared).
- `B` – powrót do widoku ETH.

**Zmienne środowiskowe dla statycznych ustawień:**

| Nazwa | Domyślna wartość | Opis |
|-------|------------------|------|
| `ETH_STATIC_IP` | `192.168.50.10/24` | Adres IP/prefix dla trybu Static |
| `ETH_STATIC_GATEWAY` | `192.168.50.1` | Brama domyślna w trybie Static |
| `ETH_STATIC_DNS` | `1.1.1.1` | DNS w trybie Static |
| `ETH_SHARED_IP` | `10.42.0.1/24` | Adres interfejsu przy DHCP server (`ipv4.method shared`) |

**Edycja adresu statycznego w UI:**

- `X (UP)` / `Y (DOWN)` – zwiększ/zmniejsz bieżący segment (IP, prefix, gateway, DNS).
- `A` – przejdź do kolejnego segmentu, a po ostatnim zapisz i zastosuj ustawienia.
- `B` – powrót do menu akcji bez zapisu.

### Logowanie

- Wszystkie kluczowe zdarzenia aplikacji są zapisywane do pliku `wifi_display.log` (w katalogu projektu).
- Log obejmuje m.in. skanowania Wi-Fi, wywołania `nmcli`, przełączenia ekranów i wyniki operacji sieciowych.

---

### 4. Moduł ZeroTier

#### Widok

Lista sieci:

| Network ID | IP | Status |
|------------|----|--------|
| 2873fd00f222b48a | 10.14.55.30 | ONLINE |

#### Akcje

- `A` – szczegóły i przełączenie ONLINE/OFFLINE
- `B` – menu:
  - [ ] dołączenie do nowej sieci
  - [ ] opuszczenie
  - [ ] diagnostyka klienta ZT

---

### **5. Narzędzia wspólne (WiFi/ETH/ZT)**

#### **Ping**

- wybór adresu
- wynik: OK/FAIL, avg ms, packet loss

#### **Skan sieci**

- wykorzystanie ARP + ICMP
- lista: IP + MAC

Przykład:

| IP | MAC |
|----|-----|
| 192.168.9.1 | aa:bb:cc:dd:ee:ff |
| 192.168.9.33 | 11:22:33:44:55:66 |

#### Dodatkowe

- [ ] test dostępu do internetu
- [ ] szybki ping do gateway/dns/wybranego hosta

---

### **6. Architektura ekranów**

1. **Ekran główny**
2. **Moduły**: WiFi / ETH / ZeroTier
3. **Narzędzia diagnostyczne**

`B` = zawsze wyjście o poziom wyżej.

---

## 👤 Autor

Krzysztof Olejnik

MIT License
