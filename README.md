# Self-Playing Survival (MVP)

A tiny, automatically played 3D survival sandbox in Python 3. The agent walks toward food, wood, and coin sources, automatically collects them, explores generated terrain, and fights randomly placed enemies.

## Run it

Python 3.10+ is recommended. A desktop window and working OpenGL graphics drivers are required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 main.py
```

On Windows, activate the environment with `.venv\\Scripts\\activate`.

## MVP scope

- Third-person 3D scene and a self-playing character
- Procedurally generated terrain chunks with food, wood, coins, and trees
- Nearby chunks are created as the player explores; distant chunks are destroyed to bound memory use
- Enemies approach and deal damage; the agent automatically fights back
- HUD tracks health, food, wood, coins, and approximate world position
- No save system, assets, backend, or external services

## Design constraints

Keep the prototype intentionally small: one game loop, primitive geometry, deterministic chunk seeds, and a fixed chunk radius. World memory stays bounded by the active chunk window. The resource list only tracks active resources.

## Next sensible increments

1. Fix resource consumption and enemy spawn timing with explicit cooldowns.
2. Add an agent state machine (gather, flee, fight, heal).
3. Add a seed/config file and lightweight save data (JSON).
4. Add tests for chunk generation and agent decisions before adding more systems.
