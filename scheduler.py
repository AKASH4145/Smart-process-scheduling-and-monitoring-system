"""
=====================================================
  ELEVATOR FACTORY - JOB SHOP SCHEDULING ENGINE
  Uses Google OR-Tools to find the optimal schedule
=====================================================

KEY CONCEPTS (for beginners):
  - Each ORDER is a product (e.g., a cabin, a door panel)
  - Each ORDER has STEPS that must happen in a fixed sequence
  - Each STEP needs a specific MACHINE
  - Two orders CANNOT use the same machine at the same time
  - OR-Tools figures out the best timetable automatically
"""

from ortools.sat.python import cp_model
import pandas as pd


# ─────────────────────────────────────────────────
#  STEP 1 — Define Your Factory Data
# ─────────────────────────────────────────────────

# Machines in the elevator factory
MACHINES = {
    0: "Laser Cutter",
    1: "CNC Machine",
    2: "Press Brake (Bending)",
    3: "Welding Station",
    4: "Powder Coating",
    5: "Assembly Station",
}

# Orders — each order has:
#   "steps": list of (machine_id, duration_in_hours)
#   "deadline": how many hours from now it must be done
#   "priority": 1=High, 2=Medium, 3=Low
ORDERS = {
    "Order A - Cabin Structure": {
        "priority": 1,
        "deadline": 12,
        "steps": [
            (0, 2),   # Laser Cutter   → 2 hrs
            (1, 3),   # CNC Machine    → 3 hrs
            (3, 2),   # Welding        → 2 hrs
            (5, 2),   # Assembly       → 2 hrs
        ],
    },
    "Order B - Door Panel": {
        "priority": 2,
        "deadline": 10,
        "steps": [
            (0, 1),   # Laser Cutter   → 1 hr
            (2, 2),   # Bending        → 2 hrs
            (4, 3),   # Powder Coating → 3 hrs
        ],
    },
    "Order C - Guide Rails": {
        "priority": 1,
        "deadline": 8,
        "steps": [
            (1, 2),   # CNC Machine    → 2 hrs
            (3, 1),   # Welding        → 1 hr
        ],
    },
    "Order D - Motor Mount": {
        "priority": 3,
        "deadline": 14,
        "steps": [
            (0, 1),   # Laser Cutter   → 1 hr
            (1, 2),   # CNC Machine    → 2 hrs
            (3, 1),   # Welding        → 1 hr
            (4, 2),   # Powder Coating → 2 hrs
            (5, 3),   # Assembly       → 3 hrs
        ],
    },
    "Order E - Safety Bracket": {
        "priority": 2,
        "deadline": 9,
        "steps": [
            (2, 1),   # Bending        → 1 hr
            (3, 1),   # Welding        → 1 hr
            (4, 2),   # Powder Coating → 2 hrs
        ],
    },
}


# ─────────────────────────────────────────────────
#  STEP 2 — The Scheduling Engine (OR-Tools)
# ─────────────────────────────────────────────────

def run_scheduler(orders=ORDERS, machines=MACHINES):
    """
    This function takes the orders and machines,
    and figures out the BEST possible schedule.

    How it works (simple explanation):
    1. We create a "model" — like a blank timetable
    2. We tell it the rules:
       - Each step has a start time, end time, duration
       - Steps within one order must go in sequence
       - Two steps on the same machine cannot overlap
    3. We tell it the GOAL: finish everything as fast as possible
    4. OR-Tools tries millions of combinations and gives us the best one
    """

    model = cp_model.CpModel()

    # Calculate the maximum possible time (worst case = all jobs run one after another)
    horizon = sum(
        duration
        for order in orders.values()
        for (_, duration) in order["steps"]
    )

    # Dictionary to store all the "time variables" for each step
    all_tasks = {}
    # Dictionary to group tasks by machine (to prevent overlap)
    machine_to_tasks = {m: [] for m in machines}

    # ── Create time variables for every step of every order ──
    for order_name, order_data in orders.items():
        for step_index, (machine_id, duration) in enumerate(order_data["steps"]):

            # These are the "unknowns" OR-Tools will solve for
            start_var = model.NewIntVar(0, horizon, f"{order_name}_step{step_index}_start")
            end_var   = model.NewIntVar(0, horizon, f"{order_name}_step{step_index}_end")

            # An "interval" links start, duration, and end together
            interval_var = model.NewIntervalVar(
                start_var, duration, end_var,
                f"{order_name}_step{step_index}_interval"
            )

            all_tasks[(order_name, step_index)] = {
                "start":    start_var,
                "end":      end_var,
                "interval": interval_var,
                "machine":  machine_id,
                "duration": duration,
            }

            machine_to_tasks[machine_id].append(interval_var)

    # ── Rule 1: Steps within an order must go in sequence ──
    # (You can't weld before you cut!)
    for order_name, order_data in orders.items():
        for step_index in range(len(order_data["steps"]) - 1):
            # End of this step must be <= Start of next step
            model.Add(
                all_tasks[(order_name, step_index)]["end"]
                <= all_tasks[(order_name, step_index + 1)]["start"]
            )

    # ── Rule 2: No two jobs can use the same machine at the same time ──
    for machine_id, intervals in machine_to_tasks.items():
        if len(intervals) > 1:
            model.AddNoOverlap(intervals)

    # ── Goal: Minimize the total time to finish everything (makespan) ──
    makespan = model.NewIntVar(0, horizon, "makespan")
    model.AddMaxEquality(
        makespan,
        [all_tasks[(order_name, len(order_data["steps"]) - 1)]["end"]
         for order_name, order_data in orders.items()]
    )
    model.Minimize(makespan)

    # ── Solve! ──
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30  # Give it up to 30 seconds
    status = solver.Solve(model)

    # ── Extract Results ──
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        results = []
        for order_name, order_data in orders.items():
            for step_index, (machine_id, duration) in enumerate(order_data["steps"]):
                task = all_tasks[(order_name, step_index)]
                start = solver.Value(task["start"])
                end   = solver.Value(task["end"])
                results.append({
                    "Order":    order_name,
                    "Step":     step_index + 1,
                    "Machine":  machines[machine_id],
                    "Start_hr": start,
                    "End_hr":   end,
                    "Duration": duration,
                    "Priority": order_data["priority"],
                    "Deadline": order_data["deadline"],
                    "On_Time":  end <= order_data["deadline"],
                })

        df = pd.DataFrame(results).sort_values(["Machine", "Start_hr"])
        total_time = solver.ObjectiveValue()
        return df, total_time, True

    else:
        return pd.DataFrame(), 0, False


# ─────────────────────────────────────────────────
#  STEP 3 — Run it and print results
# ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🏭 Running Elevator Factory Scheduler...\n")
    df, total_time, success = run_scheduler()

    if success:
        print(f"✅ Optimal schedule found! Total time: {int(total_time)} hours\n")
        print(df.to_string(index=False))
    else:
        print("❌ Could not find a valid schedule. Check your inputs.")
