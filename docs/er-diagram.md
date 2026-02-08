# Entity–Relationship Diagram (ERD)

## Overview

This document describes the core data model for the backend system.
The model supports event management, volunteer coordination, donations,
partner relationships, contact inquiries, and newsletter subscriptions.

The design emphasizes:
- normalized data
- support for anonymous interactions
- clear separation of roles (person vs organization)
- secure handling of financial data (no payment details stored)

---

## Entity Relationship Diagram

See the accompanying diagram file:

**`er-diagram.png`**

This diagram illustrates entities, their relationships, and cardinality.

---

## Design Principles

- Persons are centralized to avoid duplicate records across donors,
  volunteers, and partner contacts.
- Anonymous interactions are supported (donations and contact messages
  do not require a person record).
- Payment data is never stored; only third-party payment processor
  identifiers are persisted.
- Low-commitment engagement (newsletter subscriptions) is intentionally
  isolated from identity records.
- Organizations are modeled separately from individuals.

---

## Entities and Relationships

### Person

Represents a known individual who has meaningfully interacted with the
organization.

A person may:
- make one or more donations
- submit one or more contact messages
- have one volunteer profile
- serve as a contact for one or more partner organizations

A person may not exist for anonymous actions.

---

### Donation

Represents a single donation attempt or completed transaction.

- A donation may be associated with one person (anonymous donations allowed).
- A donation may be associated with one event.
- A donation always references an external payment processor
  (e.g., Stripe) via stored identifiers.

No card or banking data is stored.

---

### Event

Represents a real-world or virtual activity organized by the nonprofit.

An event:
- may receive multiple donations
- may involve multiple volunteers
- exists independently of donations or volunteers

---

### VolunteerProfile

Represents volunteer-specific information for a person.

- A volunteer profile belongs to exactly one person.
- A person may or may not have a volunteer profile.
- Volunteers may participate in one or more events.

This entity isolates volunteer-specific data from general identity data.

---

### ContactMessage

Represents a message submitted through the contact form.

- A contact message may be associated with one person.
- Contact messages may be anonymous.
- A person may submit multiple contact messages.

Contact messages serve as a communication audit trail.

---

### PartnerOrganization

Represents an external organization (business, nonprofit, or institution).

- Partner organizations exist independently of individuals.
- An organization may have multiple partner contacts.

---

### PartnerContact

Represents a person’s role within a partner organization.

- A partner contact belongs to one person.
- A partner contact belongs to one partner organization.
- A person may serve as a contact for multiple organizations.

This entity acts as a meaningful bridge between people and organizations.

---

### NewsletterSubscriber

Represents a low-commitment email subscription.

- Stores email only
- No person record required
- No relationship to other entities
- Supports easy opt-in and opt-out compliance

Newsletter subscribers are intentionally modeled separately from people.

---

## Relationship Summary (Cardinality)

- Person → Donation: 0..1 to many
- Event → Donation: 1 to many
- Person → ContactMessage: 0..1 to many
- Person → VolunteerProfile: 1 to 0..1
- VolunteerProfile ↔ Event: many to many
- PartnerOrganization → PartnerContact: 1 to many
- Person → PartnerContact: 1 to many
- NewsletterSubscriber: no foreign key relationships

---

## Notes

This ER diagram reflects the intended backend data structure and is
independent of frontend implementation details.

The model is designed to support reporting, auditing, and future
integrations without requiring structural changes.
