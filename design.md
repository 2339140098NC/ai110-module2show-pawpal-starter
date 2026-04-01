classDiagram
    class Owner {
        +String name
        +int time_available
        +String preferences
    }

    class Pet {
        +String name
        +String species
        +Owner owner
    }

    class Task {
        +String title
        +int duration_minutes
        +String priority
    }

    class Scheduler {
        +Pet pet
        +list tasks
        +int total_time
        +String reasoning
        +generate_schedule()
        +explain_plan()
    }

    Pet --> Owner : owned by
    Scheduler --> Pet : schedules for
    Scheduler --> Task : selects from
s