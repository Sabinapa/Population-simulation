# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a university course repository (Magisterij – Kvaliteta) containing four independent simulation exercises, each in its own folder. All simulations are written in Python and focus on population dynamics, game theory, and evolutionary biology.

## Running Each Exercise

Each `vaja` (exercise) is a standalone script:

```bash
# Vaja 1 – Population growth simulation (tkinter)
python vaja1/main.py

# Vaja 2 – Game theory: peaceful vs. aggressive creatures (tkinter)
python vaja2/vaja2.py

# Vaja 3 – Evolutionary lab: creatures with speed/size/perception traits (customtkinter + matplotlib)
python vaja3/vaja3.py

# Vaja 4 – Ecosystem simulation: Fox–Rabbit–Clover on a terrain (pygame)
cd vaja4 && python main.py
```

## Dependencies

- **Vaja 1 & 2**: stdlib only (`tkinter`, `random`, `math`)
- **Vaja 3**: `customtkinter`, `matplotlib`
- **Vaja 4**: `pygame`, `numpy`, and optionally `noise` (for Perlin terrain)

```bash
pip install -r vaja4/requirements.txt   # pygame>=2.5.0, noise>=1.2.2, numpy>=1.24.0
pip install customtkinter matplotlib    # for vaja3
```

Vaja 1 has a `.venv` in `vaja1/.venv/`. Activate it before running vaja1 if needed:
```bash
source vaja1/.venv/Scripts/activate  # Windows bash
```

## Architecture per Exercise

### Vaja 1 – Population Growth (`vaja1/main.py`)
Single-file tkinter app. `Creature` holds position and population parameters (R, S, K). `SimulationApp` manages the UI: a live canvas showing moving dots and a real-time analytics graph. Population dynamics follow `Δ = (R − S − K·N)·N` per cycle. Three populations run simultaneously with configurable parameters.

### Vaja 2 – Game Theory (`vaja2/vaja2.py`)
Single-file tkinter app. `Creature` is either `"Miroljubno"` (peaceful) or `"Agresivno"` (aggressive). Each generation: creatures are shuffled and assigned in pairs to food spots; payoff rules determine next-generation composition (M+M both survive, A+A both die, M+A: aggressor survives with 50% to reproduce, peaceful has 50% survival). Step-by-step with animated movement; generational history shown on a graph.

### Vaja 3 – Evolutionary Lab (`vaja3/vaja3.py`)
Single-file customtkinter app. `Creature` has continuous traits: `speed`, `size`, `perception`, `energy`. Movement priority: flee predators → seek plant food → hunt smaller prey → return home or wander. Energy is depleted each tick by `cost = (size³ × speed² + perception) × 0.0001`. Survivors reproduce with ±20% mutation. Evolution tracked across generations via matplotlib.

### Vaja 4 – Ecosystem Simulation (`vaja4/`)
Multi-file pygame app:
- `config.py` – all tunable constants (single `Config` instance shared across modules)
- `terrain.py` – generates tile grids (River, Lake, Multi-lake, Perlin noise)
- `entities.py` – `Fox`, `Rabbit`, `Clover` with thirst/hunger/age/reproduction logic
- `ui.py` – pygame panel, sliders, population graph, camera controls
- `main.py` – `Simulation` class (game loop, entity update order, history recording) and `main()` entry point

Entity update order in `Simulation.update()`: Clovers → Rabbits (new births buffered) → Foxes (new births buffered). Population caps enforced via `cfg.max_rabbits` / `cfg.max_foxes`. History sampled every 30 ticks, capped at 200 points.

## Language Note

Code comments and UI text are written in Slovenian (the course language). Variable and function names are in English.