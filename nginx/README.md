NGINX pełni rolę reverse proxy z terminacją TLS.

Odpowiedzialności:
- wymuszenie HTTPS (redirect 80 -> 443),
- bezpieczne nagłówki HTTP,
- proxy /api do backendu w sieci Docker,
- ograniczenia rozmiaru żądań oraz podstawowy rate limiting (defense-in-depth).
