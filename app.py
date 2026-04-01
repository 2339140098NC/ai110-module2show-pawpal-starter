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

# Initialise session state objects
if "owner" not in st.session_state:
    st.session_state.owner = None
if "pet" not in st.session_state:
    st.session_state.pet = None
if "tasks" not in st.session_state:
    st.session_state.tasks = []

if st.button("Save owner & pet"):
    owner = Owner(name=owner_name, time_available=int(time_available), preferences=preferences)
    pet = Pet(name=pet_name, species=species, owner=owner)
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.pet = pet
    st.session_state.tasks = []
    st.success(f"Saved! Owner: {owner_name} | Pet: {pet_name} ({species})")

st.divider()

# --- Task management ---
st.subheader("Tasks")

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
        st.success(f"Added: {task_title}")

st.divider()

# --- Task list with filtering ---
st.subheader("All Tasks")

if st.session_state.tasks:
    filter_status = st.radio(
        "Filter by status",
        options=["all", "pending", "completed"],
        horizontal=True,
    )

    displayed = []
    if st.session_state.owner is not None:
        scheduler_preview = Scheduler(st.session_state.owner)
        completed_filter = None
        if filter_status == "pending":
            completed_filter = False
        elif filter_status == "completed":
            completed_filter = True

        for pet, task in scheduler_preview.filter_tasks(completed=completed_filter):
            due_label = "due today" if task.is_due_today() else "not due today"
            displayed.append({
                "pet": pet.name,
                "title": task.title,
                "duration (min)": task.duration_minutes,
                "priority": task.priority,
                "frequency": task.frequency,
                "recurrence": due_label,
                "status": "completed" if task.completed else "pending",
                "preferred start": f"min {task.preferred_time}" if task.preferred_time is not None else "flexible",
            })

    if displayed:
        st.table(displayed)
    else:
        st.info(f"No tasks match filter: {filter_status}.")
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

        # Sort by start time for display
        sorted_schedule = scheduler.sort_by_time()

        st.success("Schedule generated!")

        start_hour = 8 * 60  # 8:00 AM in minutes
        rows = []
        for task, offset in sorted_schedule:
            actual = start_hour + offset
            hour, minute = divmod(actual, 60)
            am_pm = "AM" if hour < 12 else "PM"
            display_hour = hour if hour <= 12 else hour - 12
            rows.append({
                "Time": f"{display_hour}:{minute:02d} {am_pm}",
                "Task": task.title,
                "Duration (min)": task.duration_minutes,
                "Priority": task.priority,
                "Frequency": task.frequency,
            })

        st.table(rows)

        # Conflict report
        conflicts = scheduler.detect_conflicts()
        if conflicts:
            st.error(f"**{len(conflicts)} conflict(s) detected:**")
            for t1, t2, s1, s2 in conflicts:
                base = 8 * 60

                def fmt(offset, dur):
                    s = base + offset
                    h, m = divmod(s, 60)
                    ap = "AM" if h < 12 else "PM"
                    dh = h if h <= 12 else h - 12
                    e = base + offset + dur
                    eh, em = divmod(e, 60)
                    eap = "AM" if eh < 12 else "PM"
                    edh = eh if eh <= 12 else eh - 12
                    return f"{dh}:{m:02d} {ap} – {edh}:{em:02d} {eap}"

                st.warning(
                    f"'{t1.title}' ({fmt(s1, t1.duration_minutes)}) overlaps "
                    f"'{t2.title}' ({fmt(s2, t2.duration_minutes)})"
                )
        else:
            st.success("No scheduling conflicts.")

        st.markdown("#### Reasoning")
        st.text(scheduler.explain_plan())
