# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest on `main` | ✅ |
| Older commits | ❌ |

## Reporting a Vulnerability

**Do not open a public issue for security vulnerabilities.**

Use [GitHub's private vulnerability reporting](../../security/advisories/new) to submit a report. We will respond within 7 days and follow a 90-day disclosure timeline.

Include in your report:
- Description of the vulnerability
- Steps to reproduce
- Affected versions
- Known mitigations (if any)

## Scope

agent-crews generates configuration files for AI agents. Security concerns include:

- **Prompt injection** — YAML that could override agent behavioral boundaries
- **Data leakage** — personal project data appearing in committed/generated files
- **Credential exposure** — secrets in fleet.yaml, steering, or generated output

## Out of Scope

- Agents behaving unexpectedly (that's a [bug report](../../issues/new?template=bug_report.yml))
- Theme naming conflicts
- Generated JSON formatting
