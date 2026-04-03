# Environment Variable Management

## Decision

Use [`django-environ`](https://django-environ.readthedocs.io/) for environment variable management.

## Considered Alternatives

**`python-dotenv`** was considered but rejected. It only loads `.env` files into `os.environ` — all access is still via `os.getenv()`, which returns `None` silently for missing variables and leaves type coercion (e.g. casting `"True"` to a boolean) to the developer.

## Rationale

`django-environ` is purpose-built for Django and addresses both of `python-dotenv`'s shortcomings:

- **Fail-fast validation** — `env("VAR")` raises `ImproperlyConfigured` at startup if a required variable is missing, rather than failing silently at runtime
- **Type safety** — types and defaults are declared explicitly (e.g. `DEBUG=(bool, False)`), so values are coerced automatically rather than always being raw strings
- **`DATABASE_URL` support** — the `env.db()` helper parses a single connection URL into Django's full `DATABASES` dict, which is also the standard format used by most deployment platforms (Heroku, Render, Railway, etc.), making environment parity straightforward
