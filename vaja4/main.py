"""
Ekosistem simulacija: Lisica (plenilec) – Zajec (plen) – Detelja (hrana)
Zagon:  cd vaja4 && python main.py
"""

import pygame
import sys
import random

from config   import Config
from terrain  import Terrain
from entities import Fox, Rabbit, Clover
from ui       import UI


# ══════════════════════════════════════════════════════════════════════════════
def main():
    pygame.init()
    pygame.display.set_caption("Ekosistem Simulacija")

    cfg = Config()
    ui  = UI(cfg)
    sim = Simulation(cfg, ui)

    clock = pygame.time.Clock()
    while True:
        dt = clock.tick(cfg.FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            ui.handle_event(event, sim)

        if sim.running and not sim.paused:
            sim.update(dt)

        ui.draw(sim)
        pygame.display.flip()


# ══════════════════════════════════════════════════════════════════════════════
class Simulation:
    """Jedro simulacije – drži teren, seznam bitij in časovnik."""

    def __init__(self, cfg: "Config", ui: "UI"):
        self.cfg         = cfg
        self.ui          = ui
        self.running     = False
        self.paused      = False
        self.show_visual = True    # ko False: simulacija teče, vizualizacija izklopljena
        self.tick        = 0
        self.elapsed     = 0.0

        self.terrain : Terrain       = None
        self.foxes   : list[Fox]     = []
        self.rabbits : list[Rabbit]  = []
        self.clovers : list[Clover]  = []

        self.history_fox    = []
        self.history_rabbit = []
        self.history_clover = []

    # ── zagon ─────────────────────────────────────────────────────────────
    def start(self):
        cfg = self.cfg
        self.terrain = Terrain(cfg)
        cfg.cam_x    = 0
        cfg.cam_y    = 0

        self.foxes   = []
        self.rabbits = []
        self.clovers = []

        land = self.terrain.land_cells()

        # Detelje
        chosen = random.sample(land, min(cfg.initial_clovers, len(land)))
        for r, c in chosen:
            self.clovers.append(Clover(
                c * cfg.CELL + cfg.CELL // 2,
                r * cfg.CELL + cfg.CELL // 2,
                cfg))

        # Zajci
        spawn = random.sample(land, min(cfg.initial_rabbits, len(land)))
        for i, (r, c) in enumerate(spawn):
            self.rabbits.append(Rabbit(
                c * cfg.CELL + cfg.CELL // 2,
                r * cfg.CELL + cfg.CELL // 2,
                "M" if i % 2 == 0 else "F",
                cfg))

        # Lisice
        spawn = random.sample(land, min(cfg.initial_foxes, len(land)))
        for i, (r, c) in enumerate(spawn):
            self.foxes.append(Fox(
                c * cfg.CELL + cfg.CELL // 2,
                r * cfg.CELL + cfg.CELL // 2,
                "M" if i % 2 == 0 else "F",
                cfg))

        self.tick    = 0
        self.elapsed = 0.0
        self.running = True
        self.paused  = False

        self.history_fox    = [len(self.foxes)]
        self.history_rabbit = [len(self.rabbits)]
        self.history_clover = [len(self.clovers)]

    # ── posodabljanje ─────────────────────────────────────────────────────
    def update(self, dt: float):
        self.elapsed += dt * self.cfg.sim_speed
        self.tick    += 1

        terrain = self.terrain
        cfg     = self.cfg

        # Detelje
        for cl in self.clovers[:]:
            cl.update(dt, terrain, self.clovers)

        # Zajci
        new_rabbits = []
        for rb in self.rabbits[:]:
            rb.update(dt, terrain, self.foxes, self.rabbits, self.clovers, new_rabbits)
            if rb.dead:
                self.rabbits.remove(rb)
        self.rabbits.extend(new_rabbits[:max(0, cfg.max_rabbits - len(self.rabbits))])

        # Lisice
        new_foxes = []
        for fx in self.foxes[:]:
            fx.update(dt, terrain, self.foxes, self.rabbits, new_foxes)
            if fx.dead:
                self.foxes.remove(fx)
        self.foxes.extend(new_foxes[:max(0, cfg.max_foxes - len(self.foxes))])

        # Statistike (vsake 30 korakov)
        if self.tick % 30 == 0:
            self.history_fox.append(len(self.foxes))
            self.history_rabbit.append(len(self.rabbits))
            self.history_clover.append(len(self.clovers))
            for lst in (self.history_fox, self.history_rabbit, self.history_clover):
                if len(lst) > 200:
                    lst.pop(0)

        # Dodajanje detelje
        if self.tick % 60 == 0 and len(self.clovers) < cfg.max_clovers:
            lnd = terrain.land_cells()
            if lnd:
                r, c = random.choice(lnd)
                self.clovers.append(Clover(
                    c * cfg.CELL + cfg.CELL // 2,
                    r * cfg.CELL + cfg.CELL // 2,
                    cfg))


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    main()
