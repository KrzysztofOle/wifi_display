# Audyt gałęzi — 2026-11-21

Zakres: zdalne gałęzie GitHub na tle `main` **przed dodaniem tego raportu**. `Ahead/behind`: commity unikalne na gałęzi / brakujące na niej względem `main`. Opis bazuje na porównaniu plików i typów zmian; ocena funkcjonalna wymaga kwalifikacji kodu i testów. Lokalne gałęzie i worktree nie są widoczne w GitHub API.

Gałąź z dłuższym, wyłącznie unikalnym ciągiem commitów; potrzeba kwalifikacji na fizycznym Raspberry Pi i zgodności sterowania siecią.

| Gałąź | Ostatni commit UTC | Ahead/behind | Zawartość techniczna / uzasadnienie | Rekomendacja |
|---|---|---:|---|---|
| `temp/2025-11-24` | 2025-11-25 | 12/0 | Kod `wifi_display_hat.py`, `test.sh`, testy sieci i screen managera, obsługa restartu/wyłączenia oraz README. | **[DO PRZEGLĄDU]** |

Przed integracją uruchomić testy oraz sprawdzić, czy komendy poweroff/reboot wymagają osobnych uprawnień; nie wykonywano żadnej akcji sieciowej ani shutdown.

Nie dokonano merge, kasowania gałęzi, force-push ani uruchomienia systemów zewnętrznych. Sam fakt obecności unikalnych commitów nie dowodzi gotowości do integracji.
