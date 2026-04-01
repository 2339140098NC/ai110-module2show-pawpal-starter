import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler


def make_owner_with_pet(time_available=240):
    owner = Owner(name="Jordan", time_available=time_available, preferences="none")
    pet = Pet(name="Mochi", species="dog", owner=owner)
    owner.add_pet(pet)
    return owner, pet


# ---------------------------------------------------------------------------
# Existing tests
# ---------------------------------------------------------------------------

def test_mark_complete_changes_task_status():
    task = Task(title="Morning walk", duration_minutes=20, priority="high", frequency="daily")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    owner = Owner(name="Jordan", time_available=60, preferences="none")
    pet = Pet(name="Mochi", species="dog", owner=owner)
    assert len(pet.tasks) == 0
    pet.add_task(Task(title="Feeding", duration_minutes=10, priority="high", frequency="daily"))
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """Tasks should be returned earliest-start-first after sort_by_time()."""
    owner, pet = make_owner_with_pet()
    # Preferred times deliberately out of order: 60, 0, 30
    pet.add_task(Task(title="Lunch",     duration_minutes=10, priority="low",    frequency="daily", preferred_time=60))
    pet.add_task(Task(title="Breakfast", duration_minutes=10, priority="medium", frequency="daily", preferred_time=0))
    pet.add_task(Task(title="Mid",       duration_minutes=10, priority="high",   frequency="daily", preferred_time=30))

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()
    sorted_schedule = scheduler.sort_by_time()

    start_times = [start for _, start in sorted_schedule]
    assert start_times == sorted(start_times), "sort_by_time() did not return tasks in chronological order"


def test_sort_by_time_same_start_minute_is_stable():
    """Two tasks at the same preferred_time must keep their original relative order."""
    owner, pet = make_owner_with_pet()
    t1 = Task(title="First",  duration_minutes=5, priority="high", frequency="daily", preferred_time=0)
    t2 = Task(title="Second", duration_minutes=5, priority="high", frequency="daily", preferred_time=0)
    pet.add_task(t1)
    pet.add_task(t2)

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()
    sorted_schedule = scheduler.sort_by_time()

    titles = [task.title for task, _ in sorted_schedule]
    assert titles.index("First") < titles.index("Second"), "Stable sort order violated for equal start times"


def test_sort_by_time_before_generate_returns_empty():
    """sort_by_time() called before generate_schedule() should return an empty list."""
    owner, _ = make_owner_with_pet()
    scheduler = Scheduler(owner)
    assert scheduler.sort_by_time() == []


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_daily_task_not_due_after_completion_same_day():
    """A daily task completed today must not appear as due again today."""
    task = Task(title="Walk", duration_minutes=20, priority="high", frequency="daily")
    today = date(2026, 4, 1)
    task.last_completed_date = today.isoformat()
    assert task.is_due_today(today) is False


def test_daily_task_due_again_next_day():
    """A daily task completed yesterday must be due today (next calendar day)."""
    task = Task(title="Walk", duration_minutes=20, priority="high", frequency="daily")
    yesterday = date(2026, 3, 31)
    today = date(2026, 4, 1)
    task.last_completed_date = yesterday.isoformat()
    assert task.is_due_today(today) is True


def test_weekly_task_not_due_before_7_days():
    """A weekly task completed 6 days ago must not be due yet."""
    task = Task(title="Bath", duration_minutes=30, priority="medium", frequency="weekly")
    six_days_ago = date(2026, 3, 26)
    today = date(2026, 4, 1)
    task.last_completed_date = six_days_ago.isoformat()
    assert task.is_due_today(today) is False


def test_weekly_task_due_exactly_at_7_days():
    """A weekly task completed exactly 7 days ago must be due today (boundary)."""
    task = Task(title="Bath", duration_minutes=30, priority="medium", frequency="weekly")
    seven_days_ago = date(2026, 3, 25)
    today = date(2026, 4, 1)
    task.last_completed_date = seven_days_ago.isoformat()
    assert task.is_due_today(today) is True


def test_once_task_not_due_after_completion():
    """A 'once' task that has been completed must never be due again."""
    task = Task(title="Vet visit", duration_minutes=60, priority="high", frequency="once")
    task.mark_complete()
    assert task.is_due_today(date(2026, 4, 1)) is False


def test_once_task_due_when_not_completed():
    """A 'once' task that has never been completed must be due."""
    task = Task(title="Vet visit", duration_minutes=60, priority="high", frequency="once")
    assert task.is_due_today(date(2026, 4, 1)) is True


def test_generate_schedule_marks_daily_task_complete():
    """
    Generating a schedule for a daily task should mark it complete,
    so a scheduler built the same day no longer includes it.
    """
    owner, pet = make_owner_with_pet()
    task = Task(title="Walk", duration_minutes=20, priority="high", frequency="daily")
    pet.add_task(task)

    today = date(2026, 4, 1)
    scheduler = Scheduler(owner)
    scheduler.generate_schedule(today=today)

    # Task was scheduled → completed today
    assert task.completed is True
    assert task.last_completed_date == today.isoformat()

    # Tomorrow the task must be due again
    tomorrow = today + timedelta(days=1)
    assert task.is_due_today(tomorrow) is True


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_same_pet_overlap():
    """Two tasks for the same pet at overlapping preferred times trigger a warning."""
    owner, pet = make_owner_with_pet()
    pet.add_task(Task(title="Feeding",      duration_minutes=10, priority="high", frequency="daily", preferred_time=0))
    pet.add_task(Task(title="Morning walk", duration_minutes=30, priority="high", frequency="daily", preferred_time=5))

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()
    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) >= 1
    assert any("same pet" in c for c in conflicts)


def test_detect_conflicts_cross_pet_overlap():
    """Two tasks for different pets at overlapping times trigger a cross-pet warning."""
    owner = Owner(name="Jordan", time_available=240, preferences="none")
    pet1 = Pet(name="Mochi", species="dog", owner=owner)
    pet2 = Pet(name="Luna",  species="cat", owner=owner)
    owner.add_pet(pet1)
    owner.add_pet(pet2)

    pet1.add_task(Task(title="Walk",     duration_minutes=30, priority="high", frequency="daily", preferred_time=0))
    pet2.add_task(Task(title="Playtime", duration_minutes=20, priority="high", frequency="daily", preferred_time=10))

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()
    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) >= 1
    assert any("cross-pet" in c for c in conflicts)


def test_detect_no_conflict_for_adjacent_tasks():
    """Tasks that touch (one ends exactly when the next begins) must NOT conflict."""
    owner, pet = make_owner_with_pet()
    pet.add_task(Task(title="Feeding", duration_minutes=10, priority="high", frequency="daily", preferred_time=0))
    pet.add_task(Task(title="Walk",    duration_minutes=20, priority="high", frequency="daily", preferred_time=10))

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()
    conflicts = scheduler.detect_conflicts()

    assert conflicts == [], f"Unexpected conflicts for adjacent tasks: {conflicts}"


def test_detect_conflicts_same_start_time():
    """Two tasks with identical preferred_time (same minute) must be flagged."""
    owner, pet = make_owner_with_pet()
    pet.add_task(Task(title="Task A", duration_minutes=15, priority="high",   frequency="daily", preferred_time=0))
    pet.add_task(Task(title="Task B", duration_minutes=15, priority="medium", frequency="daily", preferred_time=0))

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()
    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) >= 1
