from pawpal_system import Owner, Pet, Task, Scheduler

# Create owner with 90 minutes available today
owner = Owner(name="Jordan", time_available=90, preferences="morning routines")

# Create two pets
mochi = Pet(name="Mochi", species="dog", owner=owner)
luna = Pet(name="Luna", species="cat", owner=owner)

# Tasks added OUT OF ORDER intentionally — Grooming (late in the day) is added first,
# Feeding (early) is added last, so the raw list order does NOT match clock order.
mochi.add_task(Task(title="Grooming",     duration_minutes=20, priority="medium", frequency="weekly"))
mochi.add_task(Task(title="Morning walk", duration_minutes=30, priority="high",   frequency="daily"))
mochi.add_task(Task(title="Feeding",      duration_minutes=10, priority="high",   frequency="daily"))

# SAME-PET CONFLICT: both Mochi tasks request minute 0 — they will overlap.
mochi.add_task(Task(title="Brush teeth",  duration_minutes=5,  priority="low",    frequency="daily",
                    preferred_time=0))

# Luna: Vet medicine (preferred minute 55) added before Playtime (preferred minute 50)
# so preferred-time tasks also arrive out of clock order.
luna.add_task(Task(title="Vet medicine",     duration_minutes=10, priority="high",   frequency="once",
                   preferred_time=55))
luna.add_task(Task(title="Litter box clean", duration_minutes=10, priority="high",   frequency="daily"))
# CROSS-PET CONFLICT: Playtime (Luna) at minute 0 overlaps Brush teeth (Mochi) at minute 0.
luna.add_task(Task(title="Playtime",         duration_minutes=15, priority="medium", frequency="daily",
                   preferred_time=0))

# Register pets under the owner
owner.add_pet(mochi)
owner.add_pet(luna)

# ── Generate schedule ────────────────────────────────────────────────
scheduler = Scheduler(owner)
schedule = scheduler.generate_schedule()

# ── RAW order (insertion order, NOT sorted) ──────────────────────────
print("=" * 56)
print("  RAW ORDER  (tasks as added — unsorted)")
print("=" * 56)
start_hour = 8 * 60
for task, start_offset in schedule:
    actual_start = start_hour + start_offset
    hour, minute = divmod(actual_start, 60)
    am_pm = "AM" if hour < 12 else "PM"
    display_hour = hour if hour <= 12 else hour - 12
    print(f"  {display_hour}:{minute:02d} {am_pm}  |  {task.title} "
          f"({task.duration_minutes} min) [{task.priority}]")

# ── SORTED order (sort_by_time) ───────────────────────────────────────
print("=" * 56)
print("  SORTED BY TIME  (sort_by_time)")
print("=" * 56)
for task, start_offset in scheduler.sort_by_time():
    actual_start = start_hour + start_offset
    hour, minute = divmod(actual_start, 60)
    am_pm = "AM" if hour < 12 else "PM"
    display_hour = hour if hour <= 12 else hour - 12
    print(f"  {display_hour}:{minute:02d} {am_pm}  |  {task.title} "
          f"({task.duration_minutes} min) [{task.priority}]")

# ── Conflict detection ───────────────────────────────────────────────
print("=" * 56)
warnings = scheduler.detect_conflicts()
if warnings:
    print(f"  {len(warnings)} CONFLICT(S) DETECTED:")
    for msg in warnings:
        print(f"    {msg}")
else:
    print("  No conflicts detected.")

# ── Filter by pet ────────────────────────────────────────────────────
print("=" * 56)
print("  FILTER: Mochi's tasks only")
for pet, task in scheduler.filter_tasks(pet_name="Mochi"):
    status = "done" if task.completed else "pending"
    print(f"    [{status}] {task.title} ({task.frequency})")

# ── Filter by status ─────────────────────────────────────────────────
print("=" * 56)
print("  FILTER: all pending tasks (not yet scheduled/completed)")
pending_tasks = scheduler.filter_tasks(completed=False)
if pending_tasks:
    for pet, task in pending_tasks:
        print(f"    {pet.name}: {task.title} ({task.frequency})")
else:
    print("    All tasks are complete for today.")

# ── Reasoning ────────────────────────────────────────────────────────
print("=" * 56)
print(scheduler.explain_plan())
print("=" * 56)
