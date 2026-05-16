"""
profiler.py – Dinamični pregled kode vaja6.

Poganja simulacijo brez zaslona (headless) in meri čas posameznih funkcij.
Zaženi: python profiler.py
"""

import os
import sys
import cProfile
import pstats
import io
import time

# Pygame brez okna (headless način)
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from config   import Config
from terrain  import Terrain
from entities import Fox, Rabbit, Clover
import random

# ── Nastavitve profiliranja ────────────────────────────────────────────────────
TICKS        = 500    # število simulacijskih korakov
SIM_SPEED    = 1.0    # hitrost simulacije
DT           = 1/60   # fiksen dt (60 fps)
PRINT_TOP_N  = 20     # koliko najpočasnejših funkcij izpišemo

# ── Zgradi simulacijo brez UI ─────────────────────────────────────────────────

def build_sim(terrain_type=1):
    cfg              = Config()
    cfg.sim_speed    = SIM_SPEED
    cfg.terrain_type = terrain_type

    terrain = Terrain(cfg)
    land    = terrain.land_cells()

    clovers = []
    chosen  = random.sample(land, min(cfg.initial_clovers, len(land)))
    for r, c in chosen:
        clovers.append(Clover(c * cfg.CELL + cfg.CELL // 2,
                               r * cfg.CELL + cfg.CELL // 2, cfg))

    rabbits = []
    spawn   = random.sample(land, min(cfg.initial_rabbits, len(land)))
    for i, (r, c) in enumerate(spawn):
        rb = Rabbit(c * cfg.CELL + cfg.CELL // 2,
                    r * cfg.CELL + cfg.CELL // 2,
                    "M" if i % 2 == 0 else "F", cfg)
        rb.newborn_timer = 0.0
        rabbits.append(rb)

    foxes = []
    spawn = random.sample(land, min(cfg.initial_foxes, len(land)))
    for i, (r, c) in enumerate(spawn):
        fx = Fox(c * cfg.CELL + cfg.CELL // 2,
                 r * cfg.CELL + cfg.CELL // 2,
                 "M" if i % 2 == 0 else "F", cfg)
        fx.newborn_timer = 0.0
        foxes.append(fx)

    return cfg, terrain, foxes, rabbits, clovers


def run_simulation(cfg, terrain, foxes, rabbits, clovers, ticks):
    # Jedro simulacije brez UI – enako kot Simulation._update_entities()
    for tick in range(ticks):
        for clover in clovers[:]:
            clover.update(DT, terrain, clovers)

        new_rabbits = []
        for rabbit in rabbits[:]:
            rabbit.update(DT, terrain, foxes, rabbits, clovers, new_rabbits)
            if rabbit.dead:
                rabbits.remove(rabbit)
        added = new_rabbits[:max(0, cfg.max_rabbits - len(rabbits))]
        rabbits.extend(added)

        new_foxes = []
        for fox in foxes[:]:
            fox.update(DT, terrain, foxes, rabbits, new_foxes)
            if fox.dead:
                foxes.remove(fox)
        added = new_foxes[:max(0, cfg.max_foxes - len(foxes))]
        foxes.extend(added)

        if not foxes and not rabbits:
            print(f"  [!] Vse živali so poginile pri koraku {tick}")
            break

    return foxes, rabbits, clovers


# ── Ročne meritve posameznih funkcij ──────────────────────────────────────────

def measure_nearest_water(terrain, rabbits, repetitions=1000):
    if not rabbits:
        return 0.0
    rabbit = rabbits[0]
    t0 = time.perf_counter()
    for _ in range(repetitions):
        terrain.nearest_water(rabbit.x, rabbit.y, 320)
    elapsed = time.perf_counter() - t0
    return elapsed / repetitions * 1000  # ms na klic

def measure_find_food(rabbits, clovers, repetitions=500):
    if not rabbits:
        return 0.0
    rabbit = rabbits[0]
    t0 = time.perf_counter()
    for _ in range(repetitions):
        rabbit._find_food(clovers)
    elapsed = time.perf_counter() - t0
    return elapsed / repetitions * 1000

def measure_find_partner(rabbits, repetitions=500):
    if not rabbits:
        return 0.0
    rabbit = rabbits[0]
    t0 = time.perf_counter()
    for _ in range(repetitions):
        rabbit._find_partner(rabbits)
    elapsed = time.perf_counter() - t0
    return elapsed / repetitions * 1000

def measure_find_best_prey(foxes, rabbits, repetitions=500):
    if not foxes:
        return 0.0
    fox = foxes[0]
    t0 = time.perf_counter()
    for _ in range(repetitions):
        fox._find_best_prey(rabbits)
    elapsed = time.perf_counter() - t0
    return elapsed / repetitions * 1000

def measure_flee(rabbits, foxes, terrain, repetitions=500):
    if not rabbits:
        return 0.0
    rabbit = rabbits[0]
    t0 = time.perf_counter()
    for _ in range(repetitions):
        rabbit._flee(foxes, DT, terrain)
    elapsed = time.perf_counter() - t0
    return elapsed / repetitions * 1000

def measure_bake_surface(cfg, repetitions=5):
    t0 = time.perf_counter()
    for _ in range(repetitions):
        t = Terrain(cfg)
    elapsed = time.perf_counter() - t0
    return elapsed / repetitions * 1000

def measure_list_remove(repetitions=200):
    # Simulira list.remove() na večjem seznamu
    times = []
    for _ in range(repetitions):
        lst = list(range(300))
        t0  = time.perf_counter()
        lst.remove(150)
        times.append(time.perf_counter() - t0)
    return sum(times) / len(times) * 1000

def measure_pop0(repetitions=1000):
    # Simulira list.pop(0) vs deque popleft
    from collections import deque

    lst = list(range(200))
    t0  = time.perf_counter()
    for _ in range(repetitions):
        if lst:
            lst.pop(0)
            lst.append(0)
    list_time = (time.perf_counter() - t0) / repetitions * 1000

    dq = deque(range(200), maxlen=200)
    t0 = time.perf_counter()
    for _ in range(repetitions):
        dq.popleft()
        dq.append(0)
    deque_time = (time.perf_counter() - t0) / repetitions * 1000

    return list_time, deque_time


# ── Glavna funkcija ───────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  DINAMIČNI PREGLED – Vaja 6")
    print(f"  Koraki: {TICKS}  |  DT: {DT:.4f}s  |  Sim speed: {SIM_SPEED}")
    print("=" * 60)

    # Zgradi simulacijo
    print("\n[1/3] Gradnja simulacije...")
    random.seed(42)
    cfg, terrain, foxes, rabbits, clovers = build_sim(terrain_type=1)
    print(f"  Lisice: {len(foxes)}, Zajci: {len(rabbits)}, Radič: {len(clovers)}")
    print(f"  Kopnih celic: {len(terrain.land_cells())}")

    # ── cProfile celotne simulacije ───────────────────────────────────────────
    print(f"\n[2/3] cProfile za {TICKS} korakov...")
    random.seed(42)
    cfg2, terrain2, foxes2, rabbits2, clovers2 = build_sim(terrain_type=1)

    profiler = cProfile.Profile()
    profiler.enable()
    run_simulation(cfg2, terrain2, foxes2, rabbits2, clovers2, TICKS)
    profiler.disable()

    # Izpis rezultatov cProfile
    stream = io.StringIO()
    stats  = pstats.Stats(profiler, stream=stream)
    stats.sort_stats('cumulative')
    stats.print_stats(PRINT_TOP_N)
    cprofile_output = stream.getvalue()

    print(cprofile_output)

    # ── Ročne meritve posameznih funkcij ──────────────────────────────────────
    print("[3/3] Ročne meritve posameznih funkcij...")
    random.seed(42)
    cfg3, terrain3, foxes3, rabbits3, clovers3 = build_sim(terrain_type=1)
    # Poženi par korakov da dobimo realno stanje
    run_simulation(cfg3, terrain3, foxes3, rabbits3, clovers3, 50)

    results = {}

    print("  Merim nearest_water()...")
    results['nearest_water']  = measure_nearest_water(terrain3, rabbits3)

    print("  Merim _find_food()...")
    results['_find_food']     = measure_find_food(rabbits3, clovers3)

    print("  Merim _find_partner() (zajec)...")
    results['_find_partner']  = measure_find_partner(rabbits3)

    print("  Merim _find_best_prey()...")
    results['_find_best_prey']= measure_find_best_prey(foxes3, rabbits3)

    print("  Merim _flee()...")
    results['_flee']          = measure_flee(rabbits3, foxes3, terrain3)

    print("  Merim _bake_surface() (generacija terena)...")
    results['_bake_surface']  = measure_bake_surface(cfg3)

    print("  Merim list.remove()...")
    results['list_remove']    = measure_list_remove()

    list_pop, deque_pop = measure_pop0()
    results['list_pop0']      = list_pop
    results['deque_popleft']  = deque_pop

    # ── Izpis rezultatov ──────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  REZULTATI ROČNIH MERITEV (ms na klic)")
    print("=" * 60)
    print(f"  {'Funkcija':<30} {'ms/klic':>10}  {'Opomba'}")
    print("-" * 60)

    annotations = {
        'nearest_water':   'dvojna zanka O(search_r^2)',
        '_find_food':      'O(n) po vseh radičih',
        '_find_partner':   'O(n) po vseh zajcih/lisicah',
        '_find_best_prey': 'O(n) po vseh zajcih',
        '_flee':           'O(n) comprehension + any()',
        '_bake_surface':   'samo ob inicializaciji!',
        'list_remove':     'O(n) – primerja za deque',
        'list_pop0':       'O(n) – list.pop(0)',
        'deque_popleft':   'O(1) – deque alternativa',
    }

    sorted_results = sorted(
        [(k, v) for k, v in results.items()
         if k not in ('deque_popleft',)],
        key=lambda x: x[1], reverse=True
    )

    for name, ms in sorted_results:
        note = annotations.get(name, '')
        print(f"  {name:<30} {ms:>8.4f} ms   {note}")

    print(f"\n  deque_popleft (primerjava):    {results['deque_popleft']:.6f} ms")
    print(f"  list_pop0:                      {results['list_pop0']:.6f} ms")
    if results['deque_popleft'] > 0:
        ratio = results['list_pop0'] / results['deque_popleft']
        print(f"  → list.pop(0) je {ratio:.1f}× počasnejši od deque.popleft()")

    # ── Kontekst – koliko klicev na frame ─────────────────────────────────────
    print("\n" + "=" * 60)
    print("  OCENA OBREMENITVE NA FRAME (pri polni populaciji)")
    print("=" * 60)
    n_rabbits = len(rabbits3) or 30
    n_foxes   = len(foxes3)   or 8
    n_clovers = len(clovers3) or 80

    nw_calls = n_rabbits + n_foxes  # žejne živali
    nw_ms    = nw_calls * results['nearest_water']
    ff_calls = n_rabbits
    ff_ms    = ff_calls * results['_find_food']
    fp_calls = n_rabbits + n_foxes
    fp_ms    = fp_calls * results['_find_partner']
    pr_calls = n_foxes
    pr_ms    = pr_calls * results['_find_best_prey']

    print(f"  Populacija: {n_rabbits} zajcev, {n_foxes} lisic, {n_clovers} radičev")
    print(f"  nearest_water: ~{nw_calls} klicev/frame → ~{nw_ms:.2f} ms/frame")
    print(f"  _find_food:    ~{ff_calls} klicev/frame → ~{ff_ms:.2f} ms/frame")
    print(f"  _find_partner: ~{fp_calls} klicev/frame → ~{fp_ms:.2f} ms/frame")
    print(f"  _find_best_prey: ~{pr_calls} klicev/frame → ~{pr_ms:.2f} ms/frame")
    total = nw_ms + ff_ms + fp_ms + pr_ms
    print(f"  SKUPAJ (ocena): ~{total:.2f} ms/frame")
    budget = 1000/60
    print(f"  Frame budget pri 60fps: {budget:.1f} ms")
    print(f"  Obremenitev: {total/budget*100:.1f}% frame budgeta")

    # ── Shrani rezultate v datoteko ───────────────────────────────────────────
    out_path = "profiler_rezultati.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("DINAMIČNI PREGLED – Vaja 6\n")
        f.write(f"Koraki: {TICKS} | DT: {DT:.4f}s | Sim speed: {SIM_SPEED}\n")
        f.write(f"Populacija: {n_rabbits} zajcev, {n_foxes} lisic, {n_clovers} radičev\n\n")
        f.write("=== cPROFILE REZULTATI ===\n")
        f.write(cprofile_output)
        f.write("\n=== ROČNE MERITVE (ms/klic) ===\n")
        for name, ms in sorted_results:
            note = annotations.get(name, '')
            f.write(f"{name:<30} {ms:>8.4f} ms   {note}\n")
        f.write(f"\ndeque_popleft: {results['deque_popleft']:.6f} ms\n")
        f.write(f"list_pop0:     {results['list_pop0']:.6f} ms\n")
        f.write(f"\n=== OCENA OBREMENITVE NA FRAME ===\n")
        f.write(f"nearest_water: ~{nw_ms:.2f} ms/frame\n")
        f.write(f"_find_food:    ~{ff_ms:.2f} ms/frame\n")
        f.write(f"_find_partner: ~{fp_ms:.2f} ms/frame\n")
        f.write(f"_find_best_prey: ~{pr_ms:.2f} ms/frame\n")
        f.write(f"SKUPAJ: ~{total:.2f} ms/frame od {budget:.1f} ms budgeta\n")

    print(f"\n  Rezultati shranjeni v: {out_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
