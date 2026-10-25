import html
import pandas as pd
import streamlit as st
from simulation import LANES, compare_controllers, shortest_route, run_simulation

st.set_page_config(page_title="IATO | Incident-Aware Traffic Optimizer", page_icon="🚦", layout="wide")
st.markdown("""
<style>
.stApp { background:#0b1020; color:#e5e7eb; }
h1,h2,h3 { color:#c4b5fd !important; }
div[data-testid="stMetric"] { background:#151d33; border:1px solid #334155; padding:14px; border-radius:12px; }
section[data-testid="stSidebar"] { background:#171a27; }
.small-note { color:#9ca3af; font-size:.9rem; }
</style>
""", unsafe_allow_html=True)

st.title("🚦 IATO — Incident-Aware Traffic Optimizer")
st.caption("Educational prototype • Synthetic traffic only • No live-road integration")

SCENARIOS = ["Normal traffic", "North congestion", "Accident near East", "East road closure", "Emergency vehicle at West"]
with st.sidebar:
    st.header("Simulation controls")
    steps = st.slider("Simulation steps", 20, 200, 80, 20)
    arrival_rate = st.slider("Max random arrivals per approach / step", 1, 12, 5)
    repetitions = st.slider("Repeated runs per controller", 3, 30, 10)
    scenario = st.selectbox("Traffic scenario", SCENARIOS)
    emergency_priority = st.checkbox("Enable emergency priority rule", value=True)
    run = st.button("▶ Run experiment", type="primary", use_container_width=True)

key = (steps, arrival_rate, repetitions, scenario, emergency_priority)
if run or st.session_state.get("experiment_key") != key:
    df, examples = compare_controllers(steps, arrival_rate, scenario, repetitions, emergency_priority)
    st.session_state["experiment_df"] = df
    st.session_state["examples"] = examples
    st.session_state["experiment_key"] = key

df = st.session_state["experiment_df"]
examples = st.session_state["examples"]
means = df.groupby("Controller").mean(numeric_only=True)
fixed, adaptive = means.loc["Fixed-time"], means.loc["Adaptive"]
queue_improvement = fixed["Average queue"] - adaptive["Average queue"]

m1,m2,m3,m4 = st.columns(4)
m1.metric("Adaptive mean queue", f"{adaptive['Average queue']:.1f}")
m2.metric("Adaptive vehicles served", f"{adaptive['Vehicles served']:.1f}")
m3.metric("Approx. wait (steps)", f"{adaptive['Approx. wait (steps)']:.1f}")
m4.metric("Queue difference vs fixed", f"{queue_improvement:+.1f}", help="Positive means lower average queue for Adaptive in this synthetic experiment.")

experiment_tab, network_tab, incident_tab, notes_tab = st.tabs(["📊 Experiment", "🗺️ Interactive network", "🚨 Incident & animation", "ℹ️ Model notes"])
with experiment_tab:
    st.subheader("Average queue across repeated runs")
    st.bar_chart(df.groupby("Controller")["Average queue"].mean(), horizontal=True)
    st.subheader("Controller summary")
    st.dataframe(means.reset_index().round(2), hide_index=True, use_container_width=True)
    st.subheader("Run-to-run variation")
    st.dataframe(df.round(2), hide_index=True, use_container_width=True)
    st.download_button("⬇ Download experiment CSV", df.to_csv(index=False).encode("utf-8"), "iato_experiment_results.csv", "text/csv")

with network_tab:
    st.subheader("Interactive four-junction network")
    st.caption("Choose a route and road closure. Junction positions are conceptual, not geographic.")
    left, right = st.columns([1, 1])
    with left:
        start = st.selectbox("Route origin", LANES, index=0, key="route_start")
        goal = st.selectbox("Route destination", LANES, index=2, key="route_goal")
        closure = st.selectbox("Road segment status", ["None", "North ↔ East", "East ↔ South", "North ↔ West", "South ↔ West"], key="route_closure")
    closure_map = {"None": set(), "North ↔ East": {("North","East")}, "East ↔ South": {("East","South")}, "North ↔ West": {("North","West")}, "South ↔ West": {("South","West")}}
    route = shortest_route(start, goal, closure_map[closure])
    sample = examples["Adaptive"]["data"].iloc[-1]
    q = {lane: int(sample[f"{lane} queue"]) for lane in LANES}
    active = str(sample["Active signal"])
    positions = {"North":(250,65), "East":(425,190), "South":(250,315), "West":(75,190)}
    links = [("North","East"),("East","South"),("South","West"),("West","North"),("North","South"),("East","West")]
    svg = ['<svg viewBox="0 0 500 380" width="100%" style="background:#0f172a;border-radius:14px;border:1px solid #334155">']
    for a,b in links:
        x1,y1=positions[a]; x2,y2=positions[b]
        closed = (a,b) in closure_map[closure] or (b,a) in closure_map[closure]
        in_route = bool(route and a in route and b in route and abs(route.index(a)-route.index(b))==1)
        color = '#f87171' if closed else ('#34d399' if in_route else '#64748b')
        dash = ' stroke-dasharray="7 6"' if closed else ''
        svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{5 if in_route else 2}"{dash}/>')
    for lane,(x,y) in positions.items():
        fill = '#34d399' if lane==active else '#293548'
        svg.append(f'<circle cx="{x}" cy="{y}" r="35" fill="{fill}" stroke="#c4b5fd" stroke-width="2"/>')
        svg.append(f'<text x="{x}" y="{y-3}" fill="white" text-anchor="middle" font-size="13" font-weight="bold">{lane}</text>')
        svg.append(f'<text x="{x}" y="{y+15}" fill="white" text-anchor="middle" font-size="12">Q: {q[lane]}</text>')
    svg.append('</svg>')
    with right:
        st.markdown(''.join(svg), unsafe_allow_html=True)
        if route:
            st.success("Suggested route: " + " → ".join(route))
        else:
            st.error("No route available for this closure.")
        st.markdown("**Legend:** 🟢 active signal / 🟩 suggested route / 🔴 closed road")
    st.info("Route selection uses Dijkstra's shortest-path algorithm on a small illustrative graph; it is not connected to a real map.")

with incident_tab:
    st.subheader("Incident scenario and step-by-step traffic animation")
    incident = st.selectbox("Choose incident to inspect", SCENARIOS, index=SCENARIOS.index(scenario), key="incident_scenario")
    incident_result = run_simulation(steps, arrival_rate, "Adaptive", incident, seed=100, emergency_priority=emergency_priority)
    trace = incident_result["data"]
    step_num = st.slider("Simulation frame / step", 1, len(trace), min( min(steps, 40), len(trace)), key="animation_step")
    frame = trace.iloc[step_num-1]
    cols = st.columns(4)
    for col, lane in zip(cols, LANES):
        col.metric(f"{lane} queue", int(frame[f"{lane} queue"]))
    st.markdown(f"**Step {step_num}/{len(trace)}** · Active signal: **{frame['Active signal']}** · Green time (model units): **{frame['Green time (model units)']}**")
    st.line_chart(trace.set_index("Step")[["North queue", "East queue", "South queue", "West queue"]].iloc[:step_num])
    st.dataframe(trace.iloc[max(0,step_num-8):step_num], hide_index=True, use_container_width=True)
    if incident == "Accident near East":
        st.warning("Simulated incident: extra arrivals are added to East. This is a scenario rule, not accident detection.")
    elif incident == "East road closure":
        st.warning("Simulated road closure: East approach does not receive new arrivals and is excluded from signal selection.")
    elif incident == "Emergency vehicle at West":
        st.warning("Simulated emergency: West receives priority when the priority rule is enabled.")
    elif incident == "North congestion":
        st.warning("Simulated congestion: North receives additional arrivals each step.")
    else:
        st.info("Normal synthetic arrival pattern.")
    st.success("Vehicle conservation check passed for this run." if incident_result["conservation_ok"] else "Vehicle conservation check failed.")

with notes_tab:
    st.subheader("Model notes and limitations")
    st.markdown("""
- Traffic arrivals are synthetic and reproducible for a given seed.
- Fixed-time and adaptive controllers are compared using the same set of seeds.
- Each arriving vehicle is either served/exited or remains queued; the app checks this conservation invariant.
- The adaptive controller serves the longest eligible queue; fixed-time cycles through eligible approaches.
- Incident and emergency modes are simulated rules, not real-time detection or dispatch.
- The network drawing and route costs are illustrative, not a geographic map or live navigation.
- This prototype does not model vehicles physically moving between junctions and does not integrate SUMO, live traffic feeds, trained AI, or quantum hardware.
- Results are educational outputs from this simplified model and should not be interpreted as real-world performance claims.
""")
