import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.divider()

# --- Owner & Pet setup ---
st.subheader("Owner & Pet Information")

col_a, col_b = st.columns(2)
with col_a:
    owner_name = st.text_input("Owner name", value="Jordan")
    time_available = st.number_input("Time available today (minutes)", min_value=10, max_value=480, value=90)
    preferences = st.text_input("Preferences", value="morning routines")
with col_b:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])

# Initialise session state
for key, default in [
    ("owner", None),
    ("pet", None),
    ("tasks", []),
    ("schedule_rows", None),
    ("schedule_conflicts", None),
    ("schedule_reasoning", None),
    ("schedule_metrics", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

if st.button("Save owner & pet"):
    owner = Owner(name=owner_name, time_available=int(time_available), preferences=preferences)
    pet = Pet(name=pet_name, species=species, owner=owner)
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.pet = pet
    st.session_state.tasks = []
    # Clear any previously generated schedule
    st.session_state.schedule_rows = None
    st.session_state.schedule_conflicts = None
    st.session_state.schedule_reasoning = None
    st.session_state.schedule_metrics = None
    st.success(f"Saved! Owner: {owner_name} | Pet: {pet_name} ({species})")

st.divider()

# --- Task management ---
st.subheader("Add a Task")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
with col5:
    preferred_time = st.number_input(
        "Preferred start (min, optional)",
        min_value=-1, max_value=480, value=-1,
        help="Minutes from 8:00 AM. Set to -1 to leave flexible.",
    )

if st.button("Add task"):
    if st.session_state.pet is None:
        st.warning("Save an owner & pet first before adding tasks.")
    else:
        pref = int(preferred_time) if preferred_time >= 0 else None
        task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            frequency=frequency,
            preferred_time=pref,
        )
        st.session_state.pet.add_task(task)
        st.session_state.tasks.append({
            "title": task_title,
            "duration (min)": int(duration),
            "priority": priority,
            "frequency": frequency,
            "preferred start": f"min {pref}" if pref is not None else "flexible",
        })
        # Invalidate any cached schedule so stale results aren't shown
        st.session_state.schedule_rows = None
        st.session_state.schedule_conflicts = None
        st.session_state.schedule_reasoning = None
        st.session_state.schedule_metrics = None
        st.success(f"Added: {task_title}")

st.divider()

# --- Task list with filtering ---
st.subheader("All Tasks")

PRIORITY_ICON = {"high": "🔴", "medium": "🟡", "low": "🟢"}

if st.session_state.tasks:
    filter_col, _ = st.columns([2, 3])
    with filter_col:
        filter_status = st.radio(
            "Filter by status",
            options=["all", "pending", "completed"],
            horizontal=True,
        )

    displayed = []
    if st.session_state.owner is not None:
        completed_filter = {"pending": False, "completed": True}.get(filter_status)
        for pet, task in Scheduler(st.session_state.owner).filter_tasks(completed=completed_filter):
            due_label = "✅ due today" if task.is_due_today() else "⏭ not due today"
            displayed.append({
                "Pet": pet.name,
                "Task": task.title,
                "Priority": f"{PRIORITY_ICON.get(task.priority, '')} {task.priority}",
                "Duration (min)": task.duration_minutes,
                "Frequency": task.frequency,
                "Recurrence": due_label,
                "Status": "✔ completed" if task.completed else "⏳ pending",
                "Preferred start": f"min {task.preferred_time}" if task.preferred_time is not None else "flexible",
            })

    if displayed:
        st.dataframe(displayed, use_container_width=True, hide_index=True)
    else:
        st.info(f"No tasks match filter: **{filter_status}**.")
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# --- Schedule generation ---
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if st.session_state.owner is None:
        st.warning("Save an owner & pet first.")
    elif not st.session_state.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(st.session_state.owner)
        scheduler.generate_schedule()
        sorted_schedule = scheduler.sort_by_time()

        # Build display rows
        rows = []
        base = 8 * 60  # 8:00 AM offset
        for task, offset in sorted_schedule:
            total = base + offset
            h, m = divmod(total, 60)
            ap = "AM" if h < 12 else "PM"
            dh = h if h <= 12 else h - 12
            rows.append({
                "Time": f"{dh}:{m:02d} {ap}",
                "Task": task.title,
                "Priority": f"{PRIORITY_ICON.get(task.priority, '')} {task.priority}",
                "Duration (min)": task.duration_minutes,
                "Frequency": task.frequency,
            })

        time_used = sum(task.duration_minutes for task, _ in sorted_schedule)
        conflicts = scheduler.detect_conflicts()

        # Persist results so Streamlit reruns don't re-run the scheduler
        st.session_state.schedule_rows = rows
        st.session_state.schedule_conflicts = conflicts
        st.session_state.schedule_reasoning = scheduler.explain_plan()
        st.session_state.schedule_metrics = {
            "scheduled": len(rows),
            "time_used": time_used,
            "time_available": st.session_state.owner.time_available,
            "conflicts": len(conflicts),
        }

# Display stored schedule results (survives reruns)
if st.session_state.schedule_rows is not None:
    rows = st.session_state.schedule_rows
    metrics = st.session_state.schedule_metrics
    conflicts = st.session_state.schedule_conflicts

    # Summary metrics bar
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tasks scheduled", metrics["scheduled"])
    m2.metric("Time used (min)", metrics["time_used"])
    m3.metric("Time available (min)", metrics["time_available"])
    m4.metric("Conflicts", metrics["conflicts"])

    if rows:
        st.success("Schedule generated — sorted by start time.")
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.warning("No tasks were due today or none fit within the available time.")

    # Conflict warnings
    if conflicts:
        st.error(f"**{len(conflicts)} scheduling conflict(s) detected — review before finalising:**")
        for warning in conflicts:
            st.warning(warning)
    else:
        st.success("No scheduling conflicts detected.")

    # Reasoning expander
    with st.expander("Show scheduling reasoning"):
        st.text(st.session_state.schedule_reasoning)
