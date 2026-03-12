<![CDATA[# Security Policy

## Scope

CyberLens is a **portfolio / demonstration project**. It is not designed for production deployment handling real security telemetry. The guidance below applies to the codebase itself and its development dependencies.

## Supported Versions

| Version | Supported |
|---|---|
| 0.1.x (current) | ✅ |

## Reporting a Vulnerability

If you discover a security vulnerability in CyberLens, please report it responsibly:

1. **Do not** open a public GitHub issue for security vulnerabilities.
2. Email the maintainer directly or use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) feature on this repository.
3. Include a clear description of the vulnerability, steps to reproduce, and the potential impact.
4. Allow reasonable time for a fix before public disclosure.

## Security Measures in Place

- **CodeQL** scans run on every push to `main` and on a weekly schedule for both Python and TypeScript.
- **Bandit** static analysis runs as part of the CI pipeline to detect common Python security anti-patterns.
- **Dependency pinning** — all Python and npm dependencies are pinned to exact versions to avoid supply-chain drift.
- **Environment variables** — secrets and credentials are loaded from environment variables, never committed to the repository.
- **`.gitignore`** — `.env` files, virtual environments, and build artifacts are excluded from version control.

## Default Credentials

The `.env.example` file ships with default development credentials (e.g., `MYSQL_PASSWORD=cyberlens`). These are intended **only** for local development. If you deploy CyberLens in any networked environment, replace all default credentials immediately.
]]>
