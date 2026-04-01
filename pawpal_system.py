from dataclasses import dataclass, field
from typing import List, Literal, Tuple


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Literal["low", "medium", "high"]
    frequency: str          # e.g. "daily", "weekly", "once"
    completed: bool = False


@dataclass
class Owner:
    name: str
    time_available: int     # total minutes available in the day
    preferences: str
    pets: List["Pet"] = field(default_factory=list)

    def add_pet(self, pet: "Pet") -> None:
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
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
        self.tasks.append(task)

    def get_pending_tasks(self) -> List[Task]:
        return [t for t in self.tasks if not t.completed]


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.total_time: int = owner.time_available
        self.tasks: List[Task] = owner.get_all_tasks()
        self.reasoning: str = ""
        self._schedule: List[Tuple[Task, int]] = []

    def generate_schedule(self) -> List[Tuple[Task, int]]:
        pending = [t for t in self.tasks if not t.completed]

        # Sort by priority (high first), then shorter duration as tiebreak
        sorted_tasks = sorted(
            pending,
            key=lambda t: (PRIORITY_ORDER[t.priority], t.duration_minutes),
        )

        scheduled = []
        reasons = []
        time_used = 0

        for task in sorted_tasks:
            if time_used + task.duration_minutes <= self.total_time:
                start = time_used
                scheduled.append((task, start))
                task.completed = True
                reasons.append(
                    f"- '{task.title}' ({task.priority} priority, {task.frequency}, "
                    f"{task.duration_minutes} min) starts at minute {start}."
                )
                time_used += task.duration_minutes
            else:
                reasons.append(
                    f"- '{task.title}' skipped — not enough time remaining "
                    f"({self.total_time - time_used} min left, needs {task.duration_minutes} min)."
                )

        self._schedule = scheduled
        pet_names = ", ".join(p.name for p in self.owner.pets)
        self.reasoning = (
            f"Schedule for {self.owner.name}'s pet(s): {pet_names} "
            f"({self.total_time} min available).\n"
            + "\n".join(reasons)
            + f"\nTotal time used: {time_used}/{self.total_time} min."
        )
        return self._schedule

    def explain_plan(self) -> str:
        if not self.reasoning:
            return "No schedule generated yet. Call generate_schedule() first."
        return self.reasoning
