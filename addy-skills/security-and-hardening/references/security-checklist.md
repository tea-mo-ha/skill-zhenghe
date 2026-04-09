# Security Checklist

Pre-commit and pre-merge security verification. Use alongside the main `security-and-hardening` skill.

## Input Validation

- [ ] All user input validated at system boundaries (API routes, form handlers)
- [ ] Validation uses allow-lists, not deny-lists
- [ ] String length limits enforced on all text inputs
- [ ] Numeric ranges validated (no negative quantities, no integer overflow)
- [ ] File uploads restricted by type (magic bytes, not just extension) and size
- [ ] URL inputs validated against allow-listed schemes (`https://` only where applicable)
- [ ] JSON/XML request bodies validated against a schema (Zod, Joi, JSON Schema)

## Authentication

- [ ] Passwords hashed with bcrypt (≥12 rounds), scrypt, or argon2
- [ ] No plaintext passwords stored anywhere (DB, logs, config)
- [ ] Session tokens are cryptographically random, ≥128 bits
- [ ] Cookies: `httpOnly`, `secure`, `sameSite=lax` (or `strict`)
- [ ] Session expiration enforced (idle timeout + absolute timeout)
- [ ] Login endpoint has rate limiting (≤10 attempts per 15 min)
- [ ] Password reset tokens are single-use and expire within 1 hour
- [ ] Multi-factor authentication available for privileged accounts

## Authorization

- [ ] Every API endpoint checks user permissions (not just authentication)
- [ ] Users can only access/modify their own resources (object-level checks)
- [ ] Admin actions require explicit admin role verification
- [ ] Role escalation is audited and requires separate confirmation
- [ ] API keys and service tokens scoped to minimum required permissions

## Injection Prevention

- [ ] SQL queries use parameterized statements (no string concatenation)
- [ ] NoSQL queries use typed query builders (no raw object injection)
- [ ] OS command execution avoided; if unavoidable, inputs are shell-escaped
- [ ] LDAP, XPath, and template injection vectors addressed where applicable
- [ ] HTML output auto-escaped by framework; manual `innerHTML` uses DOMPurify

## Data Protection

- [ ] No secrets in source code, commit history, or client-side bundles
- [ ] `.env` files excluded from version control; `.env.example` committed
- [ ] Sensitive fields excluded from API responses (password hashes, tokens, internal IDs)
- [ ] PII encrypted at rest where required by policy or regulation
- [ ] Logging excludes sensitive data (passwords, tokens, credit card numbers)
- [ ] Error responses do not expose stack traces or internal details

## Transport Security

- [ ] HTTPS enforced for all external communication
- [ ] HSTS header set with `max-age ≥ 31536000`
- [ ] Certificate pinning considered for mobile apps
- [ ] Internal service-to-service communication encrypted (mTLS or equivalent)

## Headers and CORS

- [ ] Content-Security-Policy set and restrictive (`default-src 'self'`)
- [ ] X-Content-Type-Options: `nosniff`
- [ ] X-Frame-Options: `DENY` or `SAMEORIGIN`
- [ ] Referrer-Policy: `strict-origin-when-cross-origin`
- [ ] CORS restricted to specific origins (no wildcard `*` in production)
- [ ] Permissions-Policy restricts unnecessary browser features

## Dependencies

- [ ] `npm audit` (or equivalent) shows no critical or high vulnerabilities
- [ ] Direct dependencies are from trusted, actively maintained sources
- [ ] Lock file (`package-lock.json`, `yarn.lock`) committed and reviewed
- [ ] Dependency updates reviewed before merging (not auto-merged blindly)
- [ ] No deprecated or unmaintained packages in production dependencies

## Pre-Commit Verification

Run these checks before every commit that touches auth, input handling, or data paths:

```bash
# Check for accidentally staged secrets
git diff --cached | grep -iE "password|secret|api_key|token|private_key"

# Audit current dependencies
npm audit --production

# Lint for security patterns (if ESLint security plugin configured)
npx eslint --rule '{"no-eval": "error", "no-implied-eval": "error"}' src/
```

## Incident Indicators

If any of these are true, stop and escalate:

- [ ] Secret was committed to version control (rotate immediately)
- [ ] User data was logged in plaintext (purge logs, notify affected users)
- [ ] Authentication bypass discovered (disable affected endpoint, patch, audit)
- [ ] SQL injection confirmed (take endpoint offline, assess data exposure)
