# IATO Flow Upgrade

This update separates the traffic model (`simulation.py`) from the Streamlit interface (`app.py`).

## Run
```bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Tests
```bat
python -m unittest discover -s tests -v
```

## Model boundaries
This is a simplified educational queue model. It checks vehicle conservation but does not model vehicles moving between junctions or use live traffic feeds, SUMO, trained AI, or quantum hardware. Approximate wait is a queue-area estimate, not measured journey time.
