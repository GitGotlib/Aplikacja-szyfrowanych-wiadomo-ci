Struktura pakietu backend/app jest zaprojektowana tak, aby:
- separować warstwy (API/transport, domena, persystencja, kryptografia),
- wspierać testowalność przez dependency injection FastAPI,
- minimalizować ryzyko błędów bezpieczeństwa przez jednoznaczne granice odpowiedzialności modułów.

W tej fazie repozytorium zawiera wyłącznie strukturę katalogów i opisy odpowiedzialności; implementacja kodu aplikacyjnego jest kolejnym krokiem.
