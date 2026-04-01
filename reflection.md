# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
    1. Enter Owner & Pet information - provide owner name, pet name, and species
    2. Add/Manage pet care tasks with a name, duration(minutes), and priority (low/midium/high)
    3. Generaet a Daily Schedule - Produce an optimized daily plan that selects and orders tasks based on constraints, and explains the reasoning
- What classes did you include, and what responsibilities did you assign to each?
Classes to have:
- Owner
    - Name
    - Time available(minutes/day)
    - Preference

- Pet
    - Name
    - species
    - owner
- Tasks:
    - title
    - duration-minutes
    - priority
- Scheduler
    - pet
    - tasks
    - total_time
    - reasoning
    Methods:
    - generate_schedule()
    - explain_plan()

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
1. Scheduler has no connection to Owner, even though Owner.time_available is the key constraint for scheduling. Right now the only path is Scheduler -> pet -> owner. Which means generate-schedule() would have to self.pet.owner.time_available to get he time budget, which works but indirect. Scheduler.__init__ should also accept the owner directly or derive total time from pet.owner.time_available during init
2. Priority is a plain string. It takes any string right now. Using fixed set of values python literal["low","medium", "high"] type hintor an Enum would prevent invalid priorities from silently breaking the scheduing logic 
3. Generate_schedule() return type doesn't carry timing`
---
 
## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

Preferred-time tasks are placed at their exact requested minute even when they overlap another task. The scheduler detects and warns about the conflict but does not move the task to the nearest free slot. This keeps the logic simple and gives the owner full control — for a pet care app, the owner usually has a hard reason for a specific time (e.g., medication must be given at 9 AM), so silently relocating the task would be worse than surfacing a warning and letting them decide.

---

## 3. AI Collaboration

**a. How you used AI**

I used VS Code Copilot and Claude Code across every phase of the project, but with a clear division of labor:

- **Design phase** — I used Copilot Chat with `#codebase` to brainstorm the UML skeleton. Asking "what responsibilities belong on Scheduler vs. Pet?" helped me identify early that `Scheduler` should own `Owner` directly rather than reaching through `Pet.owner`.
- **Implementation** — Copilot's inline autocomplete was most useful for boilerplate-heavy code: the `dataclass` field declarations, `__init__` signatures, and the repetitive structure of `filter_tasks()`. It saved time on code I already knew how to write.
- **Debugging** — When `detect_conflicts()` was returning strings but `app.py` was trying to unpack them as tuples, I asked Claude Code to explain the mismatch. Seeing the type signature spelled out (`List[str]`, not `List[Tuple]`) made the bug immediately obvious.
- **Testing** — Prompting with "what are the most important edge cases for a scheduler with sorting and recurring tasks?" produced a structured list I then converted into concrete `pytest` functions. The AI identified the 7-day boundary condition for weekly tasks, which I would likely have missed.
- **Most effective prompt style** — Specific, context-grounded questions worked best: *"Given this `is_due_today()` implementation, what boundary condition is most likely to fail?"* Generic prompts like *"write tests for my scheduler"* produced shallow results. Feeding the actual code in `#codebase` context made suggestions accurate rather than generic.

**b. Judgment and verification**

During the `generate_schedule()` implementation, Copilot suggested placing flexible tasks by simply appending them in priority order without any slot-collision checking. The suggestion was syntactically correct and would have "worked" — tasks would appear in the schedule — but it ignored the time budget entirely, meaning a 4-hour task would be scheduled even if only 30 minutes remained.

I rejected it because the core constraint of the scheduler is `owner.time_available`. A schedule that silently exceeds the time budget is worse than one that skips a task and explains why. I kept the `_find_free_slot()` approach that checks the occupied interval list before committing a task to the schedule, and added the "skipped — no free slot" reasoning line so the owner always knows what was left out and why.

The verification step was straightforward: I traced through a manual example with two tasks whose combined duration exceeded `time_available` and confirmed only the first task appeared in the output, with the second appearing in `explain_plan()` as skipped.

---

**c. VS Code Copilot — Specific Experience**

**Most effective Copilot features:**

1. **Inline autocomplete for method stubs** — After writing the docstring for `_find_free_slot()`, Copilot completed the full O(n log n) scan algorithm correctly on the first suggestion. For algorithmic code where the intent is clearly described, this was the single biggest time-saver.
2. **Copilot Chat with `#codebase`** — Asking *"which classes currently depend on each other and how?"* produced an accurate dependency graph without me having to trace imports manually. This was essential for validating the UML before finalizing it.
3. **Inline explain (`/explain`)** — Used this on the half-open interval overlap test (`s1 < s2 + d2 and s2 < s1 + d1`) to confirm it handled edge cases correctly before writing the adjacent-task test.

**One suggestion I rejected:**

Copilot suggested adding a `pet_name` attribute directly to `Task` to make filtering easier — so `filter_tasks()` could just check `task.pet_name` without traversing the `Pet → Task` relationship. I rejected this because it would have duplicated data that already exists in the object graph and introduced a consistency risk: if a task were moved to a different pet, `pet_name` could become stale. The cleaner solution was the `_task_pet` dict inside `Scheduler` that maps `id(task) → Pet` at schedule-generation time — no duplication, no stale state.

**How separate chat sessions helped:**

Keeping design, implementation, testing, and UI in separate sessions prevented context bleed. When I was writing tests, the chat had no memory of the implementation debates, which forced me to re-read the actual code before writing each test rather than relying on what I thought the code did. This caught at least one case where my mental model of `is_due_today()` was wrong about the `"once"` frequency behavior.

**Being the "lead architect" with AI tools:**

The clearest lesson was that AI tools are excellent at *execution* and weak at *judgment about system goals*. Copilot could write any individual method I described, but it had no opinion on whether the overall design was coherent — that required me to hold the full picture. Every time I accepted a suggestion without checking it against the design constraints (time budget, recurrence rules, the half-open interval invariant), I introduced a bug or inconsistency. The AI accelerated the work by roughly 2–3x, but the acceleration was entirely in typing speed and boilerplate. Every structural decision — what goes on which class, what a method's contract is, what the scheduler does when it can't fit a task — required my judgment, not the AI's. The lead architect role means setting those contracts clearly enough that the AI's execution suggestions are actually useful.

---

## 4. Testing and Verification

**a. What you tested**

- **Sorting correctness** — `sort_by_time()` returns tasks in chronological order including stable tie-breaking, and returns `[]` safely before `generate_schedule()` is called
- **Recurrence logic** — all three frequency modes (`daily`, `weekly`, `once`) including the exact 7-day boundary for weekly tasks and the full round-trip: generate → mark complete → due again tomorrow
- **Conflict detection** — same-pet overlaps, cross-pet overlaps, adjacent (non-overlapping) tasks, and identical start times
- **Core behavior** — `mark_complete()` state change, `add_task()` count increment

These tests mattered because recurrence and conflict detection are the features most likely to have off-by-one errors. The 7-day weekly boundary (`>= 7` vs `> 7`) and the half-open interval overlap check (`<` vs `<=`) are exactly the kind of logic that looks correct on inspection but fails at the boundary.

**b. Confidence**

**4 / 5.** All 16 tests pass, covering the three required areas including boundary conditions. The gap is `_find_free_slot()` — it is tested indirectly through `generate_schedule()` integration tests, but it does not yet have unit tests for fragmented gap scenarios (multiple occupied intervals with a valid gap in the middle) or the zero-time-available edge case. Those would push confidence to 5.

---

## 5. Reflection

**a. What went well**

The separation between `Task.is_due_today()` and `Scheduler.generate_schedule()` worked cleanly. Putting all recurrence logic inside `Task` meant the scheduler only had to call one method per task — it had no knowledge of what "daily" or "weekly" meant. This made testing recurrence logic in isolation straightforward and kept `Scheduler` focused on slot-filling rather than date arithmetic.

**b. What you would improve**

The preferred-time placement does not resolve conflicts — it detects them after the fact. In a next iteration I would add a "nearest free slot" fallback: if the preferred time is occupied, find the closest open slot within a configurable tolerance window (e.g., ±15 minutes) before falling back to the fully flexible algorithm. This would reduce the number of conflict warnings an owner sees on a typical day.

I would also change `priority` from a plain `str` to a `Literal["low", "medium", "high"]` or `Enum`, so invalid priority values raise an error at task creation rather than silently producing wrong sort order later.

**c. Key takeaway**

Designing a system well means making every class responsible for exactly one thing and making each responsibility testable in isolation. The moment `Scheduler` had to know about date arithmetic, the design became harder to test and reason about. Moving `is_due_today()` onto `Task` — where the recurrence data lives — was the single most clarifying structural decision in the project. AI tools helped write the code faster, but they could not have made that design call. That is the irreplaceable part of being the architect.
