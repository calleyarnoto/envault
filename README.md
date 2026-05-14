# envault

> Secure `.env` file manager that encrypts secrets per-project and integrates with common CI providers.

---

## Installation

```bash
pip install envault
```

Or with pipx for isolated installation:

```bash
pipx install envault
```

---

## Usage

**Initialize a project vault:**

```bash
envault init
```

**Add a secret:**

```bash
envault set DATABASE_URL "postgres://user:pass@localhost/db"
```

**Encrypt and lock your `.env`:**

```bash
envault lock
```

**Decrypt and load secrets into your environment:**

```bash
envault unlock --export
```

**Use with CI (GitHub Actions, GitLab CI, CircleCI):**

```bash
envault ci inject --provider github
```

Envault stores encrypted secrets in a `.envault` file that is safe to commit. The encryption key is managed separately via your CI provider's secret store or a local keyring.

---

## CI Integration

| Provider       | Supported |
|----------------|-----------|
| GitHub Actions | ✅        |
| GitLab CI      | ✅        |
| CircleCI       | ✅        |
| Bitbucket      | ✅        |

---

## License

This project is licensed under the [MIT License](LICENSE).