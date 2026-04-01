from pawpal_system import Owner, Pet, Task, Scheduler

# Create owner with 90 minutes available today
owner = Owner(name="Jordan", time_available=90, preferences="morning routines")

# Create two pets
mochi = Pet(name="Mochi", species="dog", owner=owner)
luna = Pet(name="Luna", species="cat", owner=owner)

# Add tasks to Mochi
mochi.add_task(Task(title="Morning walk",   duration_minutes=30, priority="high",   frequency="daily"))
mochi.add_task(Task(title="Feeding",        duration_minutes=10, priority="high",   frequency="daily"))
mochi.add_task(Task(title="Grooming",       duration_minutes=20, priority="medium", frequency="weekly"))

# Add tasks to Luna
luna.add_task(Task(title="Litter box clean", duration_minutes=10, priority="high",  frequency="daily"))
luna.add_task(Task(title="Playtime",         duration_minutes=15, priority="medium", frequency="daily"))

# Register pets under the owner
owner.add_pet(mochi)
owner.add_pet(luna)

# Build and print the schedule
scheduler = Scheduler(owner)
schedule = scheduler.generate_schedule()

print("=" * 40)
print("       TODAY'S SCHEDULE")
print("=" * 40)

start_hour = 8 * 60  # start at 8:00 AM in minutes
for task, start_offset in schedule:
    actual_start = start_hour + start_offset
    hour, minute = divmod(actual_start, 60)
    am_pm = "AM" if hour < 12 else "PM"
    display_hour = hour if hour <= 12 else hour - 12
    print(f"  {display_hour}:{minute:02d} {am_pm}  |  {task.title} ({task.duration_minutes} min) [{task.priority}]")

print("=" * 40)
print(scheduler.explain_plan())
