# IATO — Incident-Aware Traffic Optimizer

An educational traffic optimization prototype with adaptive signal control, incident scenarios, route planning, and simulation analytics.

## Features
- Adaptive and fixed-time traffic controller comparison
- Four-junction traffic network visualization
- Incident scenarios and alternative route planning
- Simulation metrics and CSV export
- Automated tests for core simulation logic

## Installation

```bash
python -m pip install -r requirements.txt
```

## Run the application

```bash
python -m streamlit run app.py
```

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Model limitations

IATO uses a simplified educational queue model. It checks vehicle conservation but does not model vehicles physically moving between junctions or use live traffic feeds, SUMO, trained AI, or quantum hardware. Approximate waiting time is a queue-area estimate, not measured journey time.

Results are illustrative and should not be interpreted as verified real-world traffic improvements.
