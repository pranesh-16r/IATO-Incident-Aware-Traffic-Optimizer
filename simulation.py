from collections import defaultdict
import heapq
import random
import pandas as pd

LANES = ["North", "East", "South", "West"]

# Small illustrative graph for route planning (not a geographic road map).
EDGES = {
    "North": [("South", 2), ("East", 1), ("West", 1)],
    "East": [("West", 2), ("North", 1), ("South", 1)],
    "South": [("North", 2), ("East", 1), ("West", 1)],
    "West": [("East", 2), ("North", 1), ("South", 1)],
}

def shortest_route(start, goal, closed_roads=None):
    closed_roads = closed_roads or set()
    if start not in LANES or goal not in LANES:
        raise ValueError("Origin and destination must be valid junction names.")
    if start == goal:
        return [start]

    graph = defaultdict(list)
    for src, edges in EDGES.items():
        for dst, cost in edges:
            if (src, dst) not in closed_roads and (dst, src) not in closed_roads:
                graph[src].append((dst, cost))

    heap = [(0, start, [start])]
    visited = set()
    while heap:
        cost, node, path = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        if node == goal:
            return path
        for nxt, weight in graph[node]:
            if nxt not in visited:
                heapq.heappush(heap, (cost + weight, nxt, path + [nxt]))
    return None

def run_simulation(steps, arrival_rate, controller, scenario="Normal traffic",
                   seed=42, emergency_priority=True):
    """Deterministic queue model. Each vehicle is either queued or served/exited."""
    if steps < 1:
        raise ValueError("steps must be >= 1")
    if arrival_rate < 0:
        raise ValueError("arrival_rate must be >= 0")
    if controller not in {"Fixed-time", "Adaptive"}:
        raise ValueError("controller must be Fixed-time or Adaptive")

    rng = random.Random(seed)
    queues = {lane: 0 for lane in LANES}
    rows = []
    total_arrivals = 0
    total_served = 0
    queue_vehicle_steps = 0
    closed_lane = "East" if scenario == "East road closure" else None

    for step in range(steps):
        arrivals = {lane: rng.randint(0, arrival_rate) for lane in LANES}
        if scenario == "North congestion":
            arrivals["North"] += arrival_rate
        elif scenario == "Accident near East":
            arrivals["East"] += max(1, arrival_rate // 2)
        elif scenario == "East road closure":
            arrivals["East"] = 0
        elif scenario == "Emergency vehicle at West":
            # This scenario uses the same traffic arrivals; priority affects service selection.
            pass

        for lane in LANES:
            queues[lane] += arrivals[lane]
        total_arrivals += sum(arrivals.values())

        eligible = [lane for lane in LANES if lane != closed_lane]
        if controller == "Fixed-time":
            active = eligible[step % len(eligible)]
            green_units = 5
        else:
            # Stable tie-breaking makes runs reproducible.
            active = max(eligible, key=lambda lane: (queues[lane], -LANES.index(lane)))
            green_units = min(10, max(3, 2 + queues[active] // 2))

        if emergency_priority and scenario == "Emergency vehicle at West" and "West" in eligible:
            active = "West"
            green_units = max(green_units, 6)

        capacity = green_units * 2
        served = min(queues[active], capacity)
        queues[active] -= served
        total_served += served

        queue_now = sum(queues.values())
        queue_vehicle_steps += queue_now
        rows.append({
            "Step": step + 1,
            "North queue": queues["North"],
            "East queue": queues["East"],
            "South queue": queues["South"],
            "West queue": queues["West"],
            "Total queue": queue_now,
            "Active signal": active,
            "Green time (model units)": green_units,
            "Arrivals this step": sum(arrivals.values()),
            "Vehicles served this step": served,
            "Cumulative arrivals": total_arrivals,
            "Cumulative served": total_served,
            "Conservation check": total_arrivals == total_served + queue_now,
        })

    final_queue = sum(queues.values())
    assert total_arrivals == total_served + final_queue, "Vehicle conservation invariant failed."
    data = pd.DataFrame(rows)
    avg_queue = float(data["Total queue"].mean())
    # Approximate average wait in steps: area under queue curve / number of arrivals.
    approx_wait = queue_vehicle_steps / total_arrivals if total_arrivals else 0.0
    return {
        "data": data,
        "avg_queue": avg_queue,
        "vehicles_served": total_served,
        "total_arrivals": total_arrivals,
        "remaining_queue": final_queue,
        "queue_vehicle_steps": queue_vehicle_steps,
        "approx_wait_steps": approx_wait,
        "conservation_ok": total_arrivals == total_served + final_queue,
    }

def compare_controllers(steps, arrival_rate, scenario, repetitions, emergency_priority=True):
    records = []
    example_runs = {}
    for controller in ["Fixed-time", "Adaptive"]:
        runs = []
        for seed in range(100, 100 + repetitions):
            result = run_simulation(
                steps, arrival_rate, controller, scenario, seed, emergency_priority
            )
            runs.append(result)
            records.append({
                "Controller": controller,
                "Run": seed - 99,
                "Average queue": result["avg_queue"],
                "Approx. wait (steps)": result["approx_wait_steps"],
                "Vehicles arrived": result["total_arrivals"],
                "Vehicles served": result["vehicles_served"],
                "Remaining queue": result["remaining_queue"],
                "Conservation valid": result["conservation_ok"],
            })
        example_runs[controller] = runs[0]
    return pd.DataFrame(records), example_runs
