import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Owner, Pet, Task


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
