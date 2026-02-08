# Backend Data Model

## Purpose

This document defines the core backend data model at a conceptual level.
It describes the primary entities, their responsibilities, and how they
relate to one another. This document is intended to provide architectural
context and orientation prior to implementation details.

For a visual overview of entity relationships, see:
- `er-diagram.md`
- `er-diagram.png`

For field-level definitions, see:
- `data-dictionary.md`

---

## Model List

The backend consists of the following core models:

- **Person** — Centralized identity record for known individuals
- **Donation** — Records donation attempts and completed transactions
- **Event** — Represents organized activities and initiatives
- **VolunteerProfile** — Stores volunteer-specific data for a person
- **ContactMessage** — Stores inbound contact form submissions
- **PartnerOrganization** — Represents external partner organizations
- **PartnerContact** — Associates a person with a partner organization
- **NewsletterSubscriber** — Stores low-commitment email subscriptions

---

## Model Descriptions

### Person

Represents a known individual who has meaningfully interacted with the
organization.

A person may:
- make one or more donations
- submit one or more contact messages
- have one volunteer profile
- serve as a contact for one or more partner organizations

A person record is **not required** for anonymous actions.

---

### Donation

Represents a single donation attempt or completed transaction.

Key characteristics:
- Donations may be anonymous
- Donations may optionally be associated with an event
- Donations reference an external payment processor via stored identifiers

No card or banking data is stored by the application.

---

### Event

Represents a real-world or virtual activity organized by the nonprofit.

Events:
- may receive multiple donations
- may involve multiple volunteers
- exist independently of donations or volunteers

---

### VolunteerProfile

Represents volunteer-specific information for a person.

- Each volunteer profile belongs to exactly one person
- A person may or may not have a volunteer profile
- Volunteer participation in events may be tracked separately if needed

This model isolates volunteer data from general identity data.

---

### ContactMessage

Represents a message submitted through the contact form.

- Messages may be anonymous
- Messages may optionally be associated with a person
- A person may submit multiple contact messages

This model serves as a communication audit trail.

---

### PartnerOrganization

Represents an external organization such as a business, nonprofit, or
institution.

- Partner organizations exist independently of individuals
- An organization may have multiple partner contacts

---

### PartnerContact

Represents a person’s role within a partner organization.

- Each partner contact belongs to one person
- Each partner contact belongs to one partner organization
- A person may serve as a contact for multiple organizations

This model acts as a meaningful bridge between people and organizations.

---

### NewsletterSubscriber

Represents a low-commitment email subscription.

Characteristics:
- Stores email only
- No person record required
- No relationships to other models
- Supports opt-in and opt-out compliance

Newsletter subscribers are intentionally modeled separately from identity
records.

---

## Relationship Summary

- Person → Donation: optional one-to-many
- Event → Donation: one-to-many
- Person → ContactMessage: optional one-to-many
- Person → VolunteerProfile: one-to-zero-or-one
- VolunteerProfile ↔ Event: many-to-many (conceptual)
- PartnerOrganization → PartnerContact: one-to-many
- Person → PartnerContact: one-to-many
- NewsletterSubscriber: no foreign key relationships

---

## Notes

This data model is independent of frontend implementation details and
framework-specific concerns. It is designed to support reporting,
auditing, and future integrations without requiring structural changes.
