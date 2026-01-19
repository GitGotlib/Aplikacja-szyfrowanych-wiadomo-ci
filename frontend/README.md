Frontend (React + Vite + TypeScript) to warstwa prezentacji.

Założenia bezpieczeństwa:
- brak kryptografii po stronie klienta (zgodnie z wymaganiami),
- frontend nie przechowuje sekretów; używa wyłącznie mechanizmów uwierzytelnienia wystawianych przez backend (np. ciasteczka HttpOnly Secure),
- jedynym punktem wejścia do systemu z Internetu jest NGINX (HTTPS-only).
