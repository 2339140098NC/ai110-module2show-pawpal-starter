# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

The `Scheduler` class goes beyond a simple priority sort with four additional features:

**Recurring task awareness** — every `Task` carries a `frequency` (`"daily"`, `"weekly"`, or `"once"`) and a `last_completed_date`. `is_due_today()` checks recurrence rules before the task is considered for scheduling, so weekly grooming only appears once every seven days and a one-off vet visit disappears after it is done.

**Preferred start times** — tasks can declare a `preferred_time` (minutes from 8:00 AM). The scheduler places those tasks at their requested slot first, then fills the remaining gaps with flexible tasks using a linear free-slot scan (`_find_free_slot`).

**Sort by time** — `sort_by_time()` returns the generated schedule in chronological order regardless of the order tasks were added, using `sorted()` with a lambda key on the start offset.

**Conflict detection** — `detect_conflicts()` compares every pair of scheduled tasks for overlapping time windows `[start, start+duration)`. It returns plain warning strings (no exceptions) and labels each conflict as `same pet` or `cross-pet` so the owner knows exactly what to resolve.

## Testing PawPal+

### Running the tests

```bash
python -m pytest pytest/test_pawpal.py -v
```

### What the tests cover

| Area | Tests | What is verified |
|---|---|---|
| **Sorting correctness** | 3 | `sort_by_time()` returns tasks in chronological order; ties at the same start minute preserve insertion order (stable sort); calling it before `generate_schedule()` returns an empty list without crashing |
| **Recurrence logic** | 7 | Daily tasks are not re-scheduled the same day but are due again the next; weekly tasks respect the exact 7-day boundary; `"once"` tasks disappear after completion; `generate_schedule()` marks tasks complete and sets `last_completed_date` so the next day's due-check works correctly |
| **Conflict detection** | 4 | Overlapping preferred times on the same pet produce a `"same pet"` warning; overlapping times across two pets produce a `"cross-pet"` warning; adjacent tasks (end == next start) are correctly treated as non-overlapping; identical start times are always flagged |
| **Core behaviour** | 2 | `mark_complete()` flips `completed` to `True`; adding a task increases the pet's task count |

### Confidence Level

**4 / 5 stars**

The 16-test suite covers all three required areas (sorting, recurrence, conflict detection) including boundary conditions (7-day weekly boundary, adjacent-but-not-overlapping tasks, stable sort on ties). The scheduler's core slot-filling and time-budget logic has light indirect coverage through the integration tests but does not yet have dedicated unit tests for `_find_free_slot` edge cases (fragmented gaps, zero time available). Expanding coverage there would push confidence to 5 stars.

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
