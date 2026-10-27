# Tiny Kingdom — MVP

A tiny autonomous 3D settlement simulation inspired by classic RTS games. One worker gathers wood, food, and gold, returns resources to the Town Center, builds houses automatically, and survives periodic raids. The simulation runs without player input.

## Run

Python 3.10+ and a desktop graphics environment are required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Press Esc to quit. No external art assets are needed; the scene uses built-in Ursina primitives.
