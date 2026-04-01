from dataclasses import dataclass, field
from datetime import date
from typing import List, Literal, Optional, Tuple


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Literal["low", "medium", "high"]
    frequency: str              # "daily", "weekly", "once"
    completed: bool = False
    preferred_time: Optional[int] = None    # minutes from day-start (0 = 8:00 AM)
    last_completed_date: Optional[str] = None  # ISO date "YYYY-MM-DD"

    def mark_complete(self) -> None:
        """Mark the task as completed and record today's date."""
        self.completed = True
        self.last_completed_date = date.today().isoformat()

    def is_due_today(self, today: Optional[date] = None) -> bool:
        """Determine whether this task is due to be performed today.

        Applies recurrence rules based on ``frequency``:
        - ``"once"``: due if the task has never been completed.
        - ``"daily"``: due if it was not already completed today
          (compares ``last_completed_date`` to ``today``).
        - ``"weekly"``: due if it has never been completed, or if at least
          7 days have passed since ``last_completed_date``.
        - Any other value: treated as always due.

        Args:
            today: The reference date to check against.  Defaults to the
                real calendar date (``date.today()``) when omitted, but can
                be passed explicitly in tests to avoid time-sensitive failures.

        Returns:
            ``True`` if the task should be included in today's schedule,
            ``False`` if it has already been handled and should be skipped.
        """
        if today is None:
            today = date.today()
        if self.frequency == "once":
            return not self.completed
        if self.frequency == "daily":
            if self.last_completed_date is None:
                return True
            return self.last_completed_date != today.isoformat()
        if self.frequency == "weekly":
            if self.last_completed_date is None:
                return True
            last = date.fromisoformat(self.last_completed_date)
            return (today - last).days >= 7
        return True  # unknown frequency: always treat as due


@dataclass
class Owner:
    name: str
    time_available: int     # total minutes available in the day
    preferences: str
    pets: List["Pet"] = field(default_factory=list)

    def add_pet(self, pet: "Pet") -> None:
        """Add a pet to the owner's list of pets."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks from all pets owned by this owner."""
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks


@dataclass
class Pet:
    name: str
    species: str
    owner: Owner
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to the pet's list of tasks."""
        self.tasks.append(task)

    def get_pending_tasks(self) -> List[Task]:
        """Get all pending (not completed) tasks for this pet."""
        return [t for t in self.tasks if not t.completed]


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class Scheduler:
    def __init__(self, owner: Owner):
        """Initialise the scheduler for a given owner.

        Collects all tasks from every pet registered under ``owner`` and
        sets up the internal state that ``generate_schedule`` will populate.

        Args:
            owner: The ``Owner`` whose pets' tasks will be scheduled.
                   ``owner.time_available`` defines the total minute budget
                   for the day.
        """
        self.owner = owner
        self.total_time: int = owner.time_available
        self.tasks: List[Task] = owner.get_all_tasks()
        self.reasoning: str = ""
        self._schedule: List[Tuple[Task, int]] = []
        # Maps each Task object → its Pet, built during generate_schedule()
        self._task_pet: dict = {}

    # ------------------------------------------------------------------
    # Core schedule generation
    # ------------------------------------------------------------------

    def generate_schedule(self, today: Optional[date] = None) -> List[Tuple[Task, int]]:
        """
        Build today's schedule.

        - Only includes tasks that are due today (respects recurrence rules).
        - Tasks with ``preferred_time`` are placed at their requested start minute
          if it fits within the available window.
        - Remaining tasks are sorted by priority (high first) then duration, and
          slotted into the first free gap.
        - Detects and reports any time-window overlaps in the reasoning text.
        """
        # Build task → pet lookup keyed by id() — Task is a mutable dataclass
        # and therefore not hashable, so we use the object's memory address as key.
        self._task_pet = {
            id(task): pet
            for pet in self.owner.pets
            for task in pet.tasks
        }

        pending = [t for t in self.tasks if t.is_due_today(today)]

        preferred = [t for t in pending if t.preferred_time is not None]
        flexible = sorted(
            [t for t in pending if t.preferred_time is None],
            key=lambda t: (PRIORITY_ORDER[t.priority], t.duration_minutes),
        )

        scheduled: List[Tuple[Task, int]] = []
        reasons: List[str] = []

        # --- Place preferred-time tasks first ---
        for task in preferred:
            start = task.preferred_time
            if start + task.duration_minutes <= self.total_time:
                scheduled.append((task, start))
                task.mark_complete()
                reasons.append(
                    f"- '{task.title}' ({task.priority}, {task.frequency}, "
                    f"{task.duration_minutes} min) placed at preferred time minute {start}."
                )
            else:
                reasons.append(
                    f"- '{task.title}' skipped — preferred start ({start} min) + "
                    f"duration ({task.duration_minutes} min) exceeds available window "
                    f"({self.total_time} min)."
                )

        # --- Place flexible tasks in first available free slot ---
        occupied = [(s, s + t.duration_minutes) for t, s in scheduled]

        for task in flexible:
            slot = self._find_free_slot(occupied, task.duration_minutes)
            if slot is not None:
                scheduled.append((task, slot))
                occupied.append((slot, slot + task.duration_minutes))
                task.mark_complete()
                reasons.append(
                    f"- '{task.title}' ({task.priority}, {task.frequency}, "
                    f"{task.duration_minutes} min) starts at minute {slot}."
                )
            else:
                reasons.append(
                    f"- '{task.title}' skipped — no free slot available "
                    f"(needs {task.duration_minutes} min, {self.total_time} min window)."
                )

        self._schedule = scheduled

        # --- Conflict report (preferred-time tasks can overlap each other) ---
        conflict_lines = self.detect_conflicts()

        time_used = sum(t.duration_minutes for t, _ in scheduled)
        pet_names = ", ".join(p.name for p in self.owner.pets)
        self.reasoning = (
            f"Schedule for {self.owner.name}'s pet(s): {pet_names} "
            f"({self.total_time} min available).\n"
            + "\n".join(reasons)
            + (("\n" + "\n".join(conflict_lines)) if conflict_lines else "")
            + f"\nTotal time used: {time_used}/{self.total_time} min."
        )
        return self._schedule

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def sort_by_time(self) -> List[Tuple[Task, int]]:
        """Return the current schedule sorted chronologically by start time.

        Uses the integer start offset (minutes from day-start) stored in each
        ``(Task, int)`` tuple as the sort key, so tasks scheduled at the same
        minute retain their original relative order (stable sort).

        Returns:
            A new list of ``(Task, start_offset)`` tuples ordered from the
            earliest start time to the latest.  The internal ``_schedule``
            list is not modified.

        Note:
            Call ``generate_schedule()`` before this method; an empty list is
            returned if no schedule has been generated yet.
        """
        return sorted(self._schedule, key=lambda item: item[1])

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[Tuple["Pet", Task]]:
        """
        Filter all tasks across all pets.

        Args:
            pet_name: If given, only include tasks belonging to this pet (case-insensitive).
            completed: If given, only include tasks matching this completion status.

        Returns:
            List of (Pet, Task) pairs.
        """
        results = []
        for pet in self.owner.pets:
            if pet_name is not None and pet.name.lower() != pet_name.lower():
                continue
            for task in pet.tasks:
                if completed is not None and task.completed != completed:
                    continue
                results.append((pet, task))
        return results

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self) -> List[str]:
        """
        Lightweight conflict detection: compare every pair of scheduled tasks and
        check whether their time windows overlap.  Returns a list of human-readable
        warning strings so the caller can print them without crashing.

        Two tasks conflict when their intervals [start, start+duration) intersect:
            s1 < s2 + d2  AND  s2 < s1 + d1

        Each warning identifies whether the conflict is within the same pet or
        across different pets, e.g.:
            WARNING (same pet  – Mochi): 'Feeding' 8:00-8:10 overlaps 'Morning walk' 8:05-8:35
            WARNING (cross-pet – Mochi / Luna): 'Morning walk' 8:20-8:50 overlaps 'Playtime' 8:30-8:45
        """
        BASE = 8 * 60  # display times relative to 8:00 AM

        def fmt(start_offset: int, duration: int) -> str:
            """Format a time window as 'H:MM AM – H:MM AM'."""
            def clock(minutes: int) -> str:
                h, m = divmod(BASE + minutes, 60)
                ap = "AM" if h < 12 else "PM"
                dh = h if h <= 12 else h - 12
                return f"{dh}:{m:02d} {ap}"
            return f"{clock(start_offset)}-{clock(start_offset + duration)}"

        warnings = []
        for i in range(len(self._schedule)):
            t1, s1 = self._schedule[i]
            for j in range(i + 1, len(self._schedule)):
                t2, s2 = self._schedule[j]
                # Overlap test: intervals [s1, s1+d1) and [s2, s2+d2) intersect
                if s1 < s2 + t2.duration_minutes and s2 < s1 + t1.duration_minutes:
                    pet1 = self._task_pet.get(id(t1))
                    pet2 = self._task_pet.get(id(t2))
                    p1 = pet1.name if pet1 else "?"
                    p2 = pet2.name if pet2 else "?"
                    if p1 == p2:
                        scope = f"same pet  – {p1}"
                    else:
                        scope = f"cross-pet – {p1} / {p2}"
                    warnings.append(
                        f"WARNING ({scope}): "
                        f"'{t1.title}' {fmt(s1, t1.duration_minutes)} overlaps "
                        f"'{t2.title}' {fmt(s2, t2.duration_minutes)}"
                    )
        return warnings

    # ------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------

    def explain_plan(self) -> str:
        """Return a human-readable summary of the last generated schedule.

        The summary includes, for each task: whether it was placed or skipped
        and why, any detected time-window conflicts, and the total minutes used
        versus the available budget.

        Returns:
            A multi-line string with one bullet per task decision plus a
            totals line.  If ``generate_schedule()`` has not been called yet,
            returns an explanatory prompt instead.
        """
        if not self.reasoning:
            return "No schedule generated yet. Call generate_schedule() first."
        return self.reasoning

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_free_slot(
        self, occupied: List[Tuple[int, int]], duration: int
    ) -> Optional[int]:
        """Find the earliest free time slot that can hold a task of ``duration`` minutes.

        Sorts the occupied intervals once, then performs a single left-to-right scan.
        The candidate start begins at 0 and advances past each blocking interval until
        a gap large enough for ``duration`` is found, or the available window is exhausted.

        Algorithm (O(n log n)):
            1. Sort ``occupied`` by interval start.
            2. For each interval ``[occ_start, occ_end)``:
               - If ``candidate + duration <= occ_start``, the gap before this
                 block is sufficient — stop scanning.
               - If the interval overlaps the candidate window, advance
                 ``candidate`` to ``occ_end`` (jump past the block).
            3. Return ``candidate`` if it still fits within ``total_time``,
               otherwise return ``None``.

        Args:
            occupied: List of ``(start, end)`` tuples representing time windows
                      that are already taken.  May be unsorted.
            duration: The number of consecutive minutes required.

        Returns:
            The earliest valid start minute, or ``None`` if no slot is available
            within ``self.total_time``.
        """
        candidate = 0
        for occ_start, occ_end in sorted(occupied):
            if candidate + duration <= occ_start:
                break                   # gap before this block is large enough
            if candidate < occ_end:
                candidate = occ_end     # jump past the blocking slot
        return candidate if candidate + duration <= self.total_time else None
