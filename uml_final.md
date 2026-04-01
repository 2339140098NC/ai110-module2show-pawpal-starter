classDiagram

    %% ── Classes ────────────────────────────────────────────────────────────

    class Task {
        <<dataclass>>
        +str title
        +int duration_minutes
        +str priority
        +str frequency
        +bool completed
        +Optional~int~ preferred_time
        +Optional~str~ last_completed_date
        +mark_complete() None
        +is_due_today(today: date) bool
    }

    class Owner {
        <<dataclass>>
        +str name
        +int time_available
        +str preferences
        +List~Pet~ pets
        +add_pet(pet: Pet) None
        +get_all_tasks() List~Task~
    }

    class Pet {
        <<dataclass>>
        +str name
        +str species
        +Owner owner
        +List~Task~ tasks
        +add_task(task: Task) None
        +get_pending_tasks() List~Task~
    }

    class Scheduler {
        +Owner owner
        +int total_time
        +List~Task~ tasks
        +str reasoning
        -List~Tuple~ _schedule
        -dict _task_pet
        +generate_schedule(today: date) List~Tuple~
        +sort_by_time() List~Tuple~
        +filter_tasks(pet_name, completed) List~Tuple~
        +detect_conflicts() List~str~
        +explain_plan() str
        -_find_free_slot(occupied, duration) int
    }

    class PRIORITY_ORDER {
        <<module constant>>
        +dict value
        high = 0
        medium = 1
        low = 2
    }

    %% ── Relationships ───────────────────────────────────────────────────────

    Owner "1" *-- "0..*" Pet       : owns
    Pet   "1" *-- "0..*" Task      : has tasks
    Pet    --> Owner                : owner (back-ref)
    Scheduler ..> Owner            : <<uses>>
    Scheduler ..> Task             : <<schedules>>
    Scheduler ..> Pet              : <<filters>>
    Scheduler ..> PRIORITY_ORDER   : <<uses>>