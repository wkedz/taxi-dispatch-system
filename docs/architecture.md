#  Architektura

- **dispatcher-service** – główny serwis zarządzający taksówkami i zleceniami:
  - rejestracja / wyrejestrowanie taksówek
  - przypisywanie najbliższej dostępnej taksówki do kursu
- **taxi-service** – mikroserwis reprezentujący pojedynczą taksówkę:
  - rejestracja w dispatcherze
  - odbieranie przydzielonych kursów
- **grid-service** – prosty frontend pokazujący stan systemu na siatce 100x100:
  - pozycje taksówek oraz ich status available(blue), busy(orange), offline(gray),
  - licznik kursów w różnych statusach,
  - licznik taksowek,
- **client-simulator** – generator losowych zamówień klientów
- **common** – współdzielone kontrakty (schematy Pydantic, statusy)
