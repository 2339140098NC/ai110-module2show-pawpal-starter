# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
    1. Enter Owner & Pet information - provide owner name, pet name, and species
    2. Add/Manage pet care tasks with a name, duration(minutes), and priority (low/midium/high)
    3. Generaet a Daily Schedule - Produce an optimized daily plan that selects and orders tasks based on constraints, and explains the reasoning
- What classes did you include, and what responsibilities did you assign to each?
Classes to have:
- Owner
    - Name
    - Time available(minutes/day)
    - Preference

- Pet
    - Name
    - species
    - owner
- Tasks:
    - title
    - duration-minutes
    - priority
- Scheduler
    - pet
    - tasks
    - total_time
    - reasoning
    Methods:
    - generate_schedule()
    - explain_plan()

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
1. Scheduler has no connection to Owner, even though Owner.time_available is the key constraint for scheduling. Right now the only path is Scheduler -> pet -> owner. Which means generate-schedule() would have to self.pet.owner.time_available to get he time budget, which works but indirect. Scheduler.__init__ should also accept the owner directly or derive total time from pet.owner.time_available during init
2. Priority is a plain string. It takes any string right now. Using fixed set of values python literal["low","medium", "high"] type hintor an Enum would prevent invalid priorities from silently breaking the scheduing logic 
3. Generate_schedule() return type doesn't carry timing`
---
 
## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
