"""
=====================================================
  NAIVE SCHEDULER — Simulates manual/unoptimized scheduling
  Jobs are assigned sequentially in the order they appear,
  with no optimization. This is the "before" state.
=====================================================
"""

import pandas as pd


def run_naive_scheduler(orders, machines):
    """
    Simulates a basic first-come-first-served schedule.
    Each order's steps are assigned as early as possible
    on each machine, but orders are processed one at a time
    in the order they appear — no intelligent interleaving.

    This mimics what happens when a factory manager
    manually fills in an Excel sheet sequentially.
    """

    # Track when each machine becomes free
    machine_free_at = {m: 0 for m in machines}

    results = []

    for order_name, order_data in orders.items():
        current_time = 0  # Each order starts after the previous one finishes

        for step_index, (machine_id, duration) in enumerate(order_data["steps"]):
            # Step can only start when:
            # 1. The previous step in this order is done (current_time)
            # 2. The machine is free (machine_free_at[machine_id])
            start = max(current_time, machine_free_at[machine_id])
            end = start + duration

            # Update machine availability
            machine_free_at[machine_id] = end
            current_time = end

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
    total_time = df["End_hr"].max()
    return df, total_time
