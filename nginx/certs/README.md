Ten katalog przechowuje certyfikat i klucz prywatny TLS używane przez NGINX (TLS termination).

Wymagane pliki (nie są częścią repozytorium):
- tls.crt — certyfikat X.509 (PEM)
- tls.key — klucz prywatny (PEM)

Uzasadnienie:
- Repozytorium nie może zawierać kluczy prywatnych.
- NGINX realizuje wymuszenie HTTPS oraz polityki nagłówków bezpieczeństwa na brzegu systemu.
