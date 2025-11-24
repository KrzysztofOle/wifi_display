# Zasady pracy asystenta (AGENTS)

Poniższy dokument określa zasady współpracy przy rozwoju projektu „wifi_display”. Celem jest jasna, spójna i weryfikowalna komunikacja oraz bezpieczne wprowadzanie zmian w lokalnym środowisku.

## Ogólny opis projektu

Projekt umożliwia zarządzanie sieciami Wi-Fi na Raspberry Pi Zero 2W  
bez klawiatury i monitora — tylko za pomocą 1.3" wyświetlacza HAT Mini i przycisków.

Szczegółowy opis projektu znajdziesz w pliku: README.md.

Projekt uruchamiany będzie na Raspberry Pi Zero 2 W z nakładkami:

- Waveshare 20894
- Display HAT Mini

Projekt edytujemy na systemie macOS, aby CODEX miał dostęp do plików. Niestety nie możemy go uruchamiać ze względu na brak nakładek. Projekt przez GitHub będę synchronizował z Raspberry i tam uruchamiał.

## Definicje

- **Środowisko robocze**: lokalny katalog projektu w systemie MacOS lub Windows, w którym wprowadzane są zmiany.
- **Środowisko testowe**: lokalny katalog projektu na docelowym urządzeniu Raspberry Pi, w którym wprowadzane są zmiany.
- **Wiadomość commita**: opis zmian przygotowany w stylu Git zgodnie z sekcją „Zarządzanie zmianami i opisami”.
- **Oznaczenie „— fragment”**: adnotacja stosowana, gdy prezentujemy wycinek dłuższej funkcji/klasy; zapewnij kontekst co najmniej 3–5 linii przed i po kluczowej zmianie.
- **Format ISO 8601**: standard zapisu daty i czasu, np. `2025-09-08T17:45:12+02:00`.

## 2. Ogólne zasady pracy

1. Odpowiadaj zawsze po polsku.
2. Formatuj wszystkie odpowiedzi w Markdown dla czytelności.
3. Na czacie pokazuj wyłącznie zmodyfikowane lub dodane linie (diff); przy większych zmianach pomijaj wyświetlanie kodu na czacie i podawaj jedynie ścieżki plików.
4. Dopuszczalne są małe fragmenty kodu, o ile następnie samodzielnie wprowadzisz odpowiadające zmiany w plikach projektu.
5. Poprawki oznacz komentarzem zawierającym datę i godzinę w formacie ISO 8601 (lokalny czas lub UTC) — dotyczy plików kodu; dla dokumentacji nie jest wymagane. Przykład:

   ```python
   # --- poprawka: krótki opis zmiany — 2025-09-08T17:45:12+02:00 ---
   ```

6. Jeśli funkcja ma więcej niż 100 linii, użyj wyraźnego oznaczenia (np. „setup(...) — fragment”) oraz wskaż pominięcia:

   ```python
   # ... (fragment pominięty) ...
   ```

7. Przestrzegaj standardu PEP 8.
8. Nazwy zmiennych i funkcji zapisuj w języku angielskim.
9. Nigdy nie pomijaj istniejących komentarzy w prezentowanym kodzie.
10. Wprowadzaj zmiany stopniowo, tak aby możliwe było przetestowanie każdej zmiany.
11. Jeśli instrukcje są niejasne, poproś o doprecyzowanie.
12. Pracuj w sposób czytelny, profesjonalny i uporządkowany.
13. Wprowadzaj zmiany wyłącznie w lokalnych plikach projektu; nie wykonuj operacji na repozytorium (brak commitów/pushów).

## 3. Zarządzanie zmianami i opisami

1. Nie twórz changeloga automatycznie.
2. Generuj rozbudowany opis zmian (wiadomość commita) tylko na wyraźne polecenie użytkownika.
3. Format wiadomości commita:
    - Nagłówek: `# wifi_display <wersja>` (np. `# wifi_display 0.1.0`)
    - Krótki opis zmian (1–2 zdania, zwięźle – jak w dzisiejszym przykładzie).
    - Szczegółowe zmiany umieszczaj w pliku `docs/commits/<YYYY-MM-DD>.md` (np. `docs/commits/2025-09-11.md`) i odwołuj się do niego w treści commita.
    - Osobne sekcje dla każdego zmodyfikowanego pliku:
      - Wypunktuj zmienione/dodane funkcje lub parametry.
      - Dodaj 1–2 krótkie zdania wyjaśnienia przy każdej pozycji (bez wchodzenia w implementację).
    - Styl: schludny, profesjonalny, bez emotikonów i grafik.

## 4. Aktualizacja README.md

1. Aktualizuj `README.md` tylko przy istotnych zmianach funkcjonalnych (np. nowy moduł, obsługa nowego sprzętu).
2. Przy drobnych poprawkach interfejsu graficznego (GUI) lub zmianach kosmetycznych — nie aktualizuj `README.md`.
3. Zachowuj strukturę `README`: Opis projektu, Instrukcja uruchomienia, Struktura projektu, Historia zmian.

## 5. Testowanie kodu

1. Zawsze używaj pytest. Dla nowo tworzonego kodu twórz testy w stylu pytest.
2. Po wprowadzeniu nowych funkcji, testów lub poprawek — natychmiast uruchom odpowiedni, pojedynczy plik testowy i zaraportuj wynik.
3. Nie proponuj nowych funkcjonalności ani ulepszeń, dopóki bieżący kod nie przejdzie testów.
4. W przypadku konfliktów lub ograniczeń środowiska (np. długotrwałe lub zasobożerne uruchomienia) — najpierw poinformuj i uzyskaj zgodę.
5. Testy muszą działać zarówno w tym projekcie, jak i po dołączeniu jako submoduł do innego projektu (poprawne importy, względne ścieżki, brak zależności od lokalnych ustawień IDE).
6. Jeżeli z przyczyn technicznych test nie może działać w trybie submodułu — oznacz go `pytest.mark.skip` lub `pytest.mark.skipif(...)` z czytelnym uzasadnieniem w komunikacie.
7. Priorytet: w razie konfliktu pierwszeństwo ma poprawne działanie testów w tym projekcie.
8. Wymagane jest pełne pokrycie testami (100%) w tym projekcie; używaj `pytest-cov` i egzekwuj próg (np. `--cov-fail-under=100`).

## 6. Dodatkowe zasady

1. Wszystkie zmiany dokonuj w środowisku roboczym.
2. Testy wymagające dostępu do Raspberry Pi i nakładek uruchamiane będą w środowisku testowym.
3. Zawsze pracuj na aktualnej wersji kodu — sprawdzaj, czy w repozytorium nie ma nowszej wersji.
4. Jeśli pojawi się konflikt zasad — zgłoś go od razu do rozstrzygnięcia.
5. Synchronizacja zmian między środowiskami będzie odbywać się przez dedykowaną gałąź repozytorium `temp/data`, np. `temp/2025-11-24`.

## 7. Polecenie wzorcowe

📋 Polecenie wzorcowe do wygenerowania opisu zmian do commita:

Przygotuj rozbudowany opis zmian do commita na podstawie ostatnich zmian w plikach, w formacie Markdown.

## 8. Nagłówek modułu (docstring)

1. Na początku każdego modułu (`.py`) umieść nagłówek w postaci potrójnego cudzysłowu (`""" ... """`).
2. Struktura nagłówka składa się z trzech części w podanej kolejności:
   - Pierwsza linia: krótki, ogólny opis modułu (jedno zdanie).
   - Część środkowa: rozwinięcie opisu (kilka zdań lub lista wypunktowana z kluczowymi cechami/opcjami). Część środkowa ma być dwujęzyczna: najpierw wersja angielska, następnie polska.
   - Ostatnia linia: względna ścieżka do pliku w repozytorium w formacie `File: <ścieżka/względna/do/pliku.py>`.
3. Stosuj spójne formatowanie (puste linie między częściami opcjonalne); nie dodawaj zbędnych informacji poza trzema częściami.
4. Przykład wzorcowy:

   ```python
   """
   Find duplicate files by file name only (not by content).

   Features (EN):
   - Default excluded dirs and files.
   - User-provided --exclude-dirs / --exclude-files extend defaults.
   - Optional file extensions filter (comma-separated).
   - Case-insensitive/Case-sensitive switch.

   Funkcje (PL):
   - Domyślnie wykluczane katalogi i pliki.
   - Parametry --exclude-dirs / --exclude-files rozszerzają wartości domyślne.
   - Opcjonalne filtrowanie po rozszerzeniach plików (lista rozdzielona przecinkami).
   - Przełącznik czułości na wielkość liter.

   File: tools/find_duplicate_files_by_name.py
   """
   ```

5. Umiejscowienie: docstring musi znajdować się na początku pliku — może być poprzedzony wyłącznie:
   - wierszem shebang (np. `#!/usr/bin/env python3`), oraz/lub
   - deklaracją kodowania (np. `# -*- coding: utf-8 -*-`).
6. Zakazane przed docstringiem: nie umieszczaj innych komentarzy ani linii opisowych (np. `# py_tools/tools/...`). Informację o ścieżce do pliku podawaj wyłącznie w ostatniej linii docstringa w postaci `File: ...`.

## 9. Precedencja zasad (wiele plików AGENTS.md)

- Zasada: „Najbliższy AGENTS.md wygrywa”. W obrębie katalogu `py_tools/` obowiązują zasady z tego pliku. Dla innych części repozytorium stosuj najbliższy `AGENTS.md` w górę drzewa katalogów.
- Zakres: dotyczy wszystkich punktów polityki, w tym progów pokrycia testów, stylu komunikacji i zasad prezentacji zmian.
- Przykłady:
  - Zmiany w `py_tools/...` → stosuj `py_tools/AGENTS.md` (np. wyższy próg pokrycia może obowiązywać tu lokalnie).
  - Zmiany poza `py_tools/...` → stosuj główny `AGENTS.md` repozytorium.
- Kolizje: nie łącz reguł między dokumentami; jeśli pojawi się niejednoznaczność, zgłoś do wyjaśnienia.
