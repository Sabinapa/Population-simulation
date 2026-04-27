
# Ekosistem simulacija: Lisica (plenilec) – Zajec (plen) – Radič (hrana)
import pygame
import sys
import random

from config   import Config
from terrain  import Terrain
from entities import Fox, Rabbit, Clover
from ui       import UI

# ── Poimenovane konstante ─────────────────────────────────────────────────────
HISTORY_SAMPLE_INTERVAL = 30    # zabeleži populacijo vsakih N korakov
HISTORY_MAX_POINTS      = 200   # največja dolžina zgodovine v pomnilniku


def main():
    pygame.init()
    pygame.display.set_caption("Ekosistem Simulacija")

    cfg = Config()
    ui  = UI(cfg)
    sim = Simulation(cfg, ui)
    sim.preview_terrain()   # prikaži teren takoj preden uporabnik pritisne Start

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


class Simulation:
    # Jedro simulacije – upravlja teren, sezname entitet in uro.
    def __init__(self, cfg: "Config", ui: "UI"):
        self.cfg         = cfg
        self.ui          = ui
        self.running     = False
        self.paused      = False
        self.show_visual = True    # ko je False: simulacija teče brez risanja entitet
        self.tick        = 0
        self.elapsed     = 0.0    # skupni simulirani čas v sekundah

        self.terrain : Terrain       = None
        self.foxes   : list[Fox]     = []
        self.rabbits : list[Rabbit]  = []
        self.clovers : list[Clover]  = []

        self.history_fox    = []
        self.history_rabbit = []
        self.history_clover = []

        self.births_fox    = 0
        self.births_rabbit = 0

    # ── Zagon / ponastavitev ───────────────────────────────────────────────────
    def start(self):
        # Zgradi svež teren in namesti začetne populacije.
        cfg = self.cfg
        self.terrain = Terrain(cfg)
        cfg.cam_x    = 0
        cfg.cam_y    = 0

        self.foxes   = []
        self.rabbits = []
        self.clovers = []

        land = self.terrain.land_cells()

        # Naključno raztrosi radič po kopnih celicah
        chosen = random.sample(land, min(cfg.initial_clovers, len(land)))
        for r, c in chosen:
            self.clovers.append(Clover(
                c * cfg.CELL + cfg.CELL // 2,
                r * cfg.CELL + cfg.CELL // 2,
                cfg))

        # Namesti zajce – izmenično M/Ž
        spawn = random.sample(land, min(cfg.initial_rabbits, len(land)))
        for i, (r, c) in enumerate(spawn):
            rb = Rabbit(
                c * cfg.CELL + cfg.CELL // 2,
                r * cfg.CELL + cfg.CELL // 2,
                "M" if i % 2 == 0 else "F",
                cfg)
            rb.newborn_timer = 0.0   # začetne živali niso novorojenčki
            self.rabbits.append(rb)

        # Namesti lisice – izmenično M/Ž
        spawn = random.sample(land, min(cfg.initial_foxes, len(land)))
        for i, (r, c) in enumerate(spawn):
            fx = Fox(
                c * cfg.CELL + cfg.CELL // 2,
                r * cfg.CELL + cfg.CELL // 2,
                "M" if i % 2 == 0 else "F",
                cfg)
            fx.newborn_timer = 0.0   # začetne živali niso novorojenčki
            self.foxes.append(fx)

        self.tick    = 0
        self.elapsed = 0.0
        self.running = True
        self.paused  = False

        self.history_fox    = [len(self.foxes)]
        self.history_rabbit = [len(self.rabbits)]
        self.history_clover = [len(self.clovers)]

        self.births_fox    = 0
        self.births_rabbit = 0

    def preview_terrain(self):
        # Generira in prikazuje teren preden se simulacija začne.
        self.terrain   = Terrain(self.cfg)
        self.cfg.cam_x = 0
        self.cfg.cam_y = 0

    # ── Glavno posodabljanje ───────────────────────────────────────────────────
    def update(self, dt: float):
        self.elapsed += dt * self.cfg.sim_speed
        self.tick    += 1

        self._update_entities(dt)

        if self.tick % HISTORY_SAMPLE_INTERVAL == 0:
            self._record_history()

        self._check_auto_pause()

    def _update_entities(self, dt: float):
        # Posodobi vse entitete za en korak; zbere in doda novorojenčke.
        terrain = self.terrain
        cfg     = self.cfg

        # Radič: posodobitev je prazna operacija (rezervirano za bodoče ponovne rasti)
        for clover in self.clovers[:]:
            clover.update(dt, terrain, self.clovers)

        # Zajci – novorojenčke zbiramo v ločen seznam da ne iteriramo čez njih
        new_rabbits = []
        for rabbit in self.rabbits[:]:
            rabbit.update(dt, terrain, self.foxes, self.rabbits, self.clovers, new_rabbits)
            if rabbit.dead:
                self.rabbits.remove(rabbit)
        added_rabbits = new_rabbits[:max(0, cfg.max_rabbits - len(self.rabbits))]
        self.rabbits.extend(added_rabbits)
        self.births_rabbit += len(added_rabbits)

        # Lisice – enak vzorec kot pri zajcih
        new_foxes = []
        for fox in self.foxes[:]:
            fox.update(dt, terrain, self.foxes, self.rabbits, new_foxes)
            if fox.dead:
                self.foxes.remove(fox)
        added_foxes = new_foxes[:max(0, cfg.max_foxes - len(self.foxes))]
        self.foxes.extend(added_foxes)
        self.births_fox += len(added_foxes)

    def _record_history(self):
        # Vzorči trenutno število populacij v zgodovinske sezname.
        self.history_fox.append(len(self.foxes))
        self.history_rabbit.append(len(self.rabbits))
        active_clovers = sum(1 for c in self.clovers if not c.eaten)
        self.history_clover.append(active_clovers)

        # Omeji zgodovino da prepreči neomejeno rast pomnilnika
        for lst in (self.history_fox, self.history_rabbit, self.history_clover):
            if len(lst) > HISTORY_MAX_POINTS:
                lst.pop(0)

    def _check_auto_pause(self):
        # Avtomatsko zaustavi ko vse živali poginejo.
        if len(self.foxes) == 0 and len(self.rabbits) == 0:
            self.paused = True


if __name__ == "__main__":
    main()
