# Project Blueprint: Client Call Metrics Portal

## 1. Executive Summary

A modern, sophisticated reporting platform for a cold-call lead generation business. The portal bridges the gap between raw **Kixie webhook data** (hosted on Render) and client-facing transparency. The design focuses on high-level KPI visibility for business owners and granular conversation auditing for sales leaders.

---

## 2. Development Roadmap

### Phase 1: Foundation & Mapping ✅ COMPLETE

**Goal:** Establish secure access and core data visualization.

- ✅ **Client-Campaign Mapping:** Create a relational table/logic linking **Customer ID** to specific **Kixie Powerlist IDs**.
  - This ensures the dashboard only queries data relevant to the logged-in user.
- ✅ **Secure Authentication:** Implement a login system where user sessions are tied to their assigned Powerlist IDs.
- ✅ **Executive KPI Header:** Display "All Time" summary cards: Total Dials, Conversations, Meetings Booked, and Information Requests.
- ✅ **The Conversation Log:** A primary data table defaulting to status = 'conversation'.
  - Include an "Expand to All Dials" toggle for transparency.
- ✅ **Audio Integration:** Embed functional HTML5 audio players directly in rows using the Kixie recording URLs.
- ✅ **Campaign Selector:** A dropdown menu to switch the view from "All Time" to specific campaign Powerlists.

---

### Phase 1.5: Customer Setup & Administration

**Goal:** Enable self-service customer onboarding and ongoing account management without requiring developer intervention.

- **Customer Creation Flow:** Build an admin-facing screen to create new customers, set their name and website, and assign Powerlist IDs with campaign names.
- **Powerlist Management:** Allow adding, editing, and removing `CustomerPowerlist` entries per customer from a dedicated UI (not just Django admin).
- **User Account Management:** Screen to create and manage user accounts tied to a customer, including password reset and role assignment.
- **Customer Overview Screen:** A list view of all customers showing their assigned powerlists, user count, and last activity.
- **Onboarding Checklist:** Guided setup flow that ensures a new customer has at least one powerlist and one user account before going live.

---

### Phase 2: Collaboration Layer

**Goal:** Enable feedback loops while maintaining data integrity.

- **Commenting System:** Add a sidebar or expandable section for specific call records where clients can discuss next steps.
- **Read-Only Outcomes:** The "Call Outcome" property remains locked to the webhook data. It cannot be changed by the client, preserving the "Source of Truth."
- **Internal Tagging:** Allow clients to add a "Status Tag" (e.g., "Review Quality" or "Lead Contacted") that exists as a separate metadata layer.
- **Notification Engine:** Integrate an email service (e.g., SendGrid) to fire an automated alert to the admin whenever a client leaves a comment.

### Phase 3: Optimization & UX

**Goal:** Polishing for scale and high-end brand perception.

- **Advanced Filtering:** Add column-header search, date-range pickers, and multi-sort functionality.
- **Visual Analytics:** Introduce clean, modern trend charts (e.g., bar charts for "Meetings Booked" per week).
- **Modern UI Refinement:** Focus on premium typography, white-space optimization, and a "sophisticated but simple" aesthetic.
- **Mobile Responsiveness:** Ensure stakeholders can audit calls and check metrics via mobile browsers.

---

## 3. Data Architecture (Logic)

| Table | Key Purpose |
|-------|-------------|
| Users | Stores login credentials and unique Client_ID. |
| Mapping | Links Client_ID to one or many Kixie_Powerlist_IDs. |
| Call_Logs | Raw data from Render DB (Read-Only). |
| Comments | Stores client feedback linked to a Call_Log_ID. |

---

## 4. User Journey Summary

1. **Entry:** Client logs in and is greeted by the **All Time** success metrics.
2. **Audit:** Client filters for "Conversations" and listens to a specific call recording.
3. **Action:** Client leaves a comment on a lead that requested information.
4. **Loop:** You receive an email notification, check the portal, and reply or take action.

---

## 5. Success Metrics

- **Reduced Manual Reporting:** Minimal client requests for manual Excel/CSV exports.
- **Client Retention:** Increased "stickiness" of your service through the transparency portal.
- **Platform Engagement:** Clients actively using the comment feature to communicate next steps.
