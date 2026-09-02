# OWASP Top 10:2025 — краткая карта VulnNotes

Источник: https://owasp.org/Top10/2025/

| ID | Категория | Где | Как проверить |
|----|-----------|-----|---------------|
| **A01** | Broken Access Control | IDOR `/confidential/<id>`, `/api/notes/<id>`; SSRF `/fetch` | alice → `/confidential/1`; `curl …/api/notes/1`; fetch loopback |
| **A02** | Security Misconfiguration | DEBUG, hardcode secret, `/debug/config` | `curl http://localhost:5050/debug/config` |
| **A03** | Software Supply Chain Failures | Flask 2.3.3 без hash-pinning / SBOM | `pip show flask`; смотри `requirements.txt` |
| **A04** | Cryptographic Failures | plaintext passwords, HTTP | `SELECT username,password FROM users` |
| **A05** | Injection | SQLi `/login`,`/search`; XSS `/search` | `' OR '1'='1' --`; `<script>alert(1)</script>` |
| **A06** | Insecure Design | нет rate limit / MFA / password policy | brute force login |
| **A07** | Authentication Failures | слабые пароли, cookie без HttpOnly | DevTools → Cookies |
| **A08** | Software or Data Integrity Failures | `/import` → `pickle.loads` | hex pickle payload |
| **A09** | Security Logging and Alerting Failures | failed login не логируется | `docker logs` после bad login |
| **A10** | Mishandling of Exceptional Conditions | SQL/exception text в ответе | `/search?q='` |

## Privesc (Ubuntu)

```bash
docker exec -u appuser psiiz-vulnnotes /usr/local/bin/backup-tool -p -c id
# uid=0(root)
```

Подробности — в [README.md](README.md).
