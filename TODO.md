# Project To-Do

## General

- [ ] **Power Dial Stats webhook** — Create a new Kixie webhook that pulls dial count from Power Dial Stats, scoped per powerlist ID, for use in the overall campaign metrics dashboard
- [ ] **Kixie call dispositions setup**
  - [ ] Define and create all call dispositions that will be used in Kixie
  - [ ] Create a test Kixie powerlist to run through each disposition
  - [ ] Verify each disposition is captured correctly in the dashboard
- [ ] **Dashboard metrics reorganization**
  - [ ] Rename "Conversations" → "Pickups" (anyone who picks up and speaks)
  - [ ] Wire "Booked Meetings" card to the `meeting booked` disposition
  - [ ] Wire "Send Information" card to the `send information` disposition
  - [ ] Update KPI query filters in `core/views.py` dashboard view to match new dispositions
- [x] **Fix: Job title column not populating** — webhook payload is not mapping the title field correctly into the dashboard
- [x] **Fix: Tracking sheet cutting off at Notes** — table is not displaying all columns, everything after Notes is missing
- [ ] **Dashboard filtering** — add filter controls for date range, call outcome, and whether the Call Notes field has any text
- [ ] **Single-line columns** — force all columns except Call Notes to display on one line (no wrapping)
- [ ] **Card-style rows** — redesign each row as a two-row-height card that displays all call data in large text within the page width

---

## Right Now

- [ ] Smoke test Phase 1.5 on Render
  - [ ] Log in as staff → confirm redirect to `/manage/`
  - [ ] Create a new customer
  - [ ] Add a campaign (powerlist ID)
  - [ ] Create a user account for that customer
  - [ ] Log in as that user → confirm dashboard shows correct data
- [ ] Push Phase 1.5 code to Render

---

## Phase 2 — Collaboration Layer

- [ ] Commenting system — sidebar or expandable section per call record
- [ ] Internal status tags — client-side metadata layer (separate from call outcome)
- [ ] Lock "Call Outcome" field — read-only, cannot be edited by client
- [ ] Email notifications via SendGrid when a client leaves a comment

---

## Phase 3 — Optimization & UX

- [ ] Advanced filtering — date range picker, column search, multi-sort
- [ ] Charts — bar chart for Meetings Booked per week
- [ ] UI polish — typography, whitespace, premium feel
- [ ] Mobile responsiveness

---

## Backlog / Nice to Have

- [ ] Edit existing campaign name (rename powerlist) from `/manage/`
- [ ] "Last activity" column on customer list in `/manage/`
- [ ] Audit log — track who made changes in the admin
- [ ] Email invitation to new users (send login link instead of manual password)
- [ ] Bulk powerlist import from CSV
- [ ] Pagination on the dashboard call log table

---

## Notes

