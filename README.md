# Tiny Kingdom — Autonomous RTS

A small Python 3 settlement simulation inspired by classic real-time strategy games. The agent behaves like a villager: it walks to a resource, works there for a short time, carries one unit back to the Town Center, and deposits it. It automatically builds a small settlement and defends itself from raids.

## Run it

Python 3.10+ is recommended. A desktop window and working OpenGL graphics drivers are required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 main.py
```

On Windows, activate the environment with `.venv\\Scripts\\activate`.

## Gameplay

- Autonomous worker gathers wood from trees, food from berry bushes, and gold from ore deposits.
- The worker spends time working at each node, carries resources, and returns to the Town Center to deposit them.
- Stored resources are automatically spent on houses and a defensive tower.
- Enemy raiders arrive over time; the worker fights back, food heals damage, and a tower provides extra defense.
- The world generates deterministic terrain chunks around the worker; distant chunks are removed to keep memory bounded.
- Low-poly characters, trees, resource nodes, houses, a Town Center, and a tower are assembled from Ursina primitives. No external art assets are required.

## Controls

The simulation is autonomous. Press `Esc` to quit.

## Design constraints

The prototype intentionally uses one game loop, one dependency, deterministic chunk seeds, primitive 3D geometry, and a fixed active chunk radius. It does not yet include manual unit selection, multiple workers, save/load, or imported character animations.
