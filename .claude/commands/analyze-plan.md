---
name: analyze-plan
description: Analyze an implementation plan document for completeness, risks, missing steps, and readiness. Use when the user wants feedback on a phase plan, asks "is this plan ready?", "review this plan", or "analyze the implementation plan".
---

Read the implementation plan the user is referring to (check `docs/` for phase-*.md files if not specified). Then analyze it across these dimensions and report findings:

## 1. Completeness Check

- Does every feature listed in the corresponding phase of `docs/Kixie Dashboard Project Plan.md` have a concrete implementation step?
- Are there any steps in the delivery sequence that reference files or functions not defined elsewhere in the plan?
- Is there a smoke test or verification step at the end?

## 2. Dependency & Order Check

- Are there hidden dependencies between steps that would break if done out of order?
- Does any step assume a model, URL, or piece of config that hasn't been created yet in a prior step?
- Flag any step that touches a file also touched by a different step — those need to be sequenced carefully.

## 3. Risk Flags

- Any step that deletes or overwrites existing data (migrations, model changes, teardown scripts)?
- Any step that could affect the production Render deployment if pushed without testing?
- Any form or view that handles user input without validation?
- Any authentication or access-control gap (e.g., a staff-only view missing the `staff_required` check)?

## 4. Missing Details

- Steps listed without enough detail to actually implement (e.g., "build X" with no field names, URL patterns, or logic described)?
- Any template mentioned but never laid out (columns, form fields, error states)?
- Any edge case the plan doesn't address (e.g., what happens if the form is submitted with duplicate data)?

## 5. Scope Creep Check

- Does the plan include anything that belongs to a later phase? Call it out — it should be moved to "Out of Scope."
- Is the "Out of Scope" section present and does it correctly defer things to future phases?

## Output Format

Report findings as a short structured list under each dimension. Use:
- **Good** — nothing to flag
- **Warning** — something to watch but not blocking
- **Gap** — missing detail that needs to be added before implementation starts
- **Risk** — something that could cause data loss, security issues, or a broken production deploy

For every Warning, Gap, or Risk, include the delivery sequence step number it applies to in parentheses — e.g., **(Step 3)**. If the issue spans multiple steps or applies to the plan structure rather than a specific step, use **(Plan-level)**. "Good" items do not need a step number.

End with a one-line **Verdict**: Ready to implement / Needs minor fixes / Needs major revision.
