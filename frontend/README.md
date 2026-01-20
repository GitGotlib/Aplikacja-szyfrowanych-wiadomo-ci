Frontend (React + Vite + TypeScript)

Założenia bezpieczeństwa:
- frontend jest niezaufany: nie wykonuje kryptografii i nie przechowuje sekretów,
- autoryzacja jest oparta o cookie HttpOnly ustawiane przez backend (przez NGINX/HTTPS),
- wszystkie wywołania API używają `credentials: 'include'`.

Struktura warstw (`frontend/src/`):
- `api/`        – klient HTTP + endpointy backendu
- `auth/`       – kontekst sesji (me/login/logout)
- `pages/`      – widoki: Register/Login/2FA/Inbox/Message/Compose
- `components/` – małe komponenty UI
- `hooks/`      – logika współdzielona
- `router/`     – routing i ochrona tras
- `types/`      – DTO zgodne z backendem

Uruchomienie (zalecane): przez Docker/NGINX (HTTPS) – patrz README w katalogu głównym.

Uruchomienie lokalne (ograniczone):
- `npm install`
- `npm run dev`

Uwaga: pełne logowanie sesyjne wymaga HTTPS i tej samej domeny co backend (cookie Secure + SameSite=strict), więc pełna integracja jest docelowo przez NGINX.
