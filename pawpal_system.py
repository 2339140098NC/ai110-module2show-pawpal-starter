from dataclasses import dataclass
from typing import List


@dataclass
class Owner:
    name: str
    time_available: int
    preferences: str


@dataclass
class Pet:
    name: str
    species: str
    owner: Owner


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str


class Scheduler:
    def __init__(self, pet: Pet, tasks: List[Task]):
        self.pet = pet
        self.tasks: List[Task] = tasks
        self.total_time: int = 0
        self.reasoning: str = ""

    def generate_schedule(self) -> List[Task]:
        pass

    def explain_plan(self) -> str:
        pass
