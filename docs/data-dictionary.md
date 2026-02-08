# Data Dictionary

## Purpose

This document defines the backend data structures at the **field level**.
It serves as the authoritative reference for what data is stored, how it
is interpreted, and why it exists.

This document is intentionally framework-agnostic and focuses on
conceptual data definitions rather than implementation details.

---

## Person

Represents a known individual who has meaningfully interacted with the
organization (e.g., donors, volunteers, partner contacts).

| Field | Type | Description |
|-----|-----|-------------|
| id | UUID | Primary identifier |
| email | string | Primary contact email (unique) |
| first_name | string | Given name |
| last_name | string | Family name |
| phone | string (optional) | Contact phone number |
| created_at | datetime | Record creation timestamp |
| updated_at | datetime | Last update timestamp |

---

## Donation

Represents a single donation attempt or completed transaction.

| Field | Type | Description |
|-----|-----|-------------|
| id | UUID | Primary identifier |
| person_id | UUID (optional) | References donor (nullable for anonymous donations) |
| event_id | UUID (optional) | References related event |
| amount | integer | Donation amount in smallest currency unit (e.g., cents) |
| currency | string | ISO 4217 currency code (e.g., USD) |
| status | string | Donation state (e.g., pending, succeeded, failed) |
| payment_processor | string | External payment provider identifier |
| processor_reference_id | string | Payment intent / transaction ID |
| created_at | datetime | Donation creation timestamp |

**Notes**
- No card or bank data is stored.
- All payment processing occurs via a third-party provider (e.g., Stripe).

---

## Event

Represents a real-world or virtual activity organized by the nonprofit.

| Field | Type | Description |
|-----|-----|-------------|
| id | UUID | Primary identifier |
| title | string | Event name |
| description | text | Event description |
| start_datetime | datetime | Event start time |
| end_datetime | datetime | Event end time |
| location | string (optional) | Physical or virtual location |
| is_active | boolean | Indicates whether event is active |
| created_at | datetime | Record creation timestamp |

---

## VolunteerProfile

Stores volunteer-specific data associated with a person.

| Field | Type | Description |
|-----|-----|-------------|
| id | UUID | Primary identifier |
| person_id | UUID | References associated person |
| availability | text (optional) | Availability notes |
| interests | text (optional) | Areas of interest |
| onboarding_complete | boolean | Indicates onboarding completion |
| created_at | datetime | Record creation timestamp |

---

## ContactMessage

Represents a message submitted via the contact form.

| Field | Type | Description |
|-----|-----|-------------|
| id | UUID | Primary identifier |
| person_id | UUID (optional) | References sender if known |
| email | string | Reply-to email address |
| category | string | Message category (general, volunteer, partner, donation) |
| subject | string | Message subject |
| message | text | Message body |
| created_at | datetime | Submission timestamp |

**Notes**
- Messages may be anonymous.
- Serves as a communication audit log.

---

## PartnerOrganization

Represents an external partner organization.

| Field | Type | Description |
|-----|-----|-------------|
| id | UUID | Primary identifier |
| name | string | Organization name |
| description | text (optional) | Organization description |
| website | string (optional) | Organization website |
| created_at | datetime | Record creation timestamp |

---

## PartnerContact

Associates a person with a partner organization.

| Field | Type | Description |
|-----|-----|-------------|
| id | UUID | Primary identifier |
| person_id | UUID | References associated person |
| organization_id | UUID | References partner organization |
| role | string | Contact role or title |
| created_at | datetime | Record creation timestamp |

---

## NewsletterSubscriber

Represents a low-commitment email subscription.

| Field | Type | Description |
|-----|-----|-------------|
| id | UUID | Primary identifier |
| email | string | Subscriber email (unique) |
| source | string (optional) | Subscription source |
| subscribed_at | datetime | Subscription timestamp |
| is_active | boolean | Indicates active subscription |

**Notes**
- No relationship to Person.
- Designed for minimal data retention and easy opt-out.

---

## Data Integrity Notes

- All records include timestamps for auditability.
- Foreign key relationships enforce referential integrity.
- Nullable relationships are intentional to support anonymous interactions.
- Sensitive data is minimized and delegated to third-party services.

---

## Change Management

Any changes to fields or relationships should be reflected in:
- `er-diagram.md`
- `data-model.md`
- this document

This ensures architectural consistency.
