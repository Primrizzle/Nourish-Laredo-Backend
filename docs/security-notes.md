# Security and Data Handling Notes

## Purpose

This document outlines the security considerations and data-handling
decisions for the backend system. It is intended to clarify how sensitive
data is protected, what data is intentionally not stored, and how
third-party services are used responsibly.

These notes reflect architectural intent rather than legal policy.

---

## Payment Data Handling

- The application **does not store** credit card numbers, bank account
  details, CVV codes, or payment authorization data.
- All payment processing is handled by a third-party payment processor
  (e.g., Stripe).
- The backend stores **only external payment identifiers** (such as
  payment intent or transaction IDs) for reconciliation, reporting, and
  audit purposes.
- Payment-related configuration values are stored in environment
  variables and are never committed to source control.

---

## Personally Identifiable Information (PII)

- The system stores a **minimal amount of PII**, limited to what is
  necessary for operational use (e.g., name and email).
- Newsletter subscriptions store **email only** and are not linked to
  identity records.
- Anonymous donations and contact messages are supported to reduce
  unnecessary data collection.
- No government-issued identifiers or sensitive personal attributes are
  collected or stored.

---

## Access Control

- Write access to backend data is restricted to server-side operations.
- Direct database access is limited to authorized administrative users.
- Administrative interfaces are protected by authentication and role-
  based access controls.
- The frontend has no direct access to sensitive credentials or database
  connections.

---

## Data Transmission

- All communication between the frontend and backend is expected to
  occur over HTTPS.
- Sensitive tokens and credentials are transmitted only when necessary
  and never exposed in client-side code.
- Third-party service integrations use secure, documented APIs.

---

## Environment Configuration

- Secrets and credentials (API keys, database URLs, webhook secrets)
  are stored in environment variables.
- Different configurations are used for development, testing, and
  production environments.
- Environment files are excluded from version control.

---

## Data Integrity and Auditability

- Records include timestamps to support auditing and traceability.
- Referential integrity is enforced through database relationships.
- Nullable relationships are intentional and support anonymous
  interactions without compromising data consistency.

---

## Third-Party Dependencies

- External services are used only where they provide security or
  compliance benefits (e.g., payment processing).
- Dependencies are reviewed periodically and updated as needed.
- The application relies on reputable, widely-used services with
  published security practices.

---

## Change Management

Security-related changes should be reviewed alongside updates to:
- the data model
- the ER diagram
- this document

This ensures that security decisions remain aligned with system
architecture as the project evolves.
