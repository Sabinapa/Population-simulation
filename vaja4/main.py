
# Ekosistem simulacija: Lisica (plenilec) – Zajec (plen) – Radič (hrana)

import pygame
import sys
import random

from config   import Config
from terrain  import Terrain
from entities import Fox, Rabbit, Clover
from ui       import UI


def main():
    pygame.init()
    pygame.display.set_caption("Ekosistem Simulacija")

    cfg = Config()
    ui  = UI(cfg)
    sim = Simulation(cfg, ui)
    sim.preview_terrain()   # pokaži teren takoj ob zagonu, še preden uporabnik pritisne Start

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
    """Jedro simulacije – drži teren, seznam bitij in časovnik."""

    def __init__(self, cfg: "Config", ui: "UI"):
        self.cfg         = cfg
        self.ui          = ui
        self.running     = False
        self.paused      = False
        self.show_visual = True    # ko False: simulacija teče brez risanja bitij
        self.tick        = 0
        self.elapsed     = 0.0    # skupni pretečeni čas v sekundah

        self.terrain : Terrain       = None
        self.foxes   : list[Fox]     = []
        self.rabbits : list[Rabbit]  = []
        self.clovers : list[Clover]  = []

        self.history_fox    = []
        self.history_rabbit = []
        self.history_clover = []

        self.births_fox    = 0
        self.births_rabbit = 0

    # Zagon
    def start(self):
        cfg = self.cfg
        self.terrain = Terrain(cfg)
        cfg.cam_x    = 0
        cfg.cam_y    = 0

        self.foxes   = []
        self.rabbits = []
        self.clovers = []

        land = self.terrain.land_cells()

        # Razporedi radič naključno po kopnih celicah
        chosen = random.sample(land, min(cfg.initial_clovers, len(land)))
        for r, c in chosen:
            self.clovers.append(Clover(
                c * cfg.CELL + cfg.CELL // 2,
                r * cfg.CELL + cfg.CELL // 2,
                cfg))

        # Razporedi zajce – enakomerno M/F
        spawn = random.sample(land, min(cfg.initial_rabbits, len(land)))
        for i, (r, c) in enumerate(spawn):
            rb = Rabbit(
                c * cfg.CELL + cfg.CELL // 2,
                r * cfg.CELL + cfg.CELL // 2,
                "M" if i % 2 == 0 else "F",
                cfg)
            rb.newborn_timer = 0.0   # začetne živali niso novorojene
            self.rabbits.append(rb)

        # Razporedi lisice – enakomerno M/F
        spawn = random.sample(land, min(cfg.initial_foxes, len(land)))
        for i, (r, c) in enumerate(spawn):
            fx = Fox(
                c * cfg.CELL + cfg.CELL // 2,
                r * cfg.CELL + cfg.CELL // 2,
                "M" if i % 2 == 0 else "F",
                cfg)
            fx.newborn_timer = 0.0   # začetne živali niso novorojene
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

    # Predogled terena (pred zagonom)
    def preview_terrain(self):
        self.terrain   = Terrain(self.cfg)
        self.cfg.cam_x = 0
        self.cfg.cam_y = 0

    # Posodabljanje
    def update(self, dt: float):
        self.elapsed += dt * self.cfg.sim_speed
        self.tick    += 1

        terrain = self.terrain
        cfg     = self.cfg

        # Radič se ne premika, update je prazen (rezervirano za morebitno rast)
        for cl in self.clovers[:]:
            cl.update(dt, terrain, self.clovers)

        # Zajci – zbiramo novorojene v ločen seznam, da ne iteriramo čez nove
        new_rabbits = []
        for rb in self.rabbits[:]:
            rb.update(dt, terrain, self.foxes, self.rabbits, self.clovers, new_rabbits)
            if rb.dead:
                self.rabbits.remove(rb)
        # Dodaj novorojene, a ne prekoračuj populacijskega limita
        added_rabbits = new_rabbits[:max(0, cfg.max_rabbits - len(self.rabbits))]
        self.rabbits.extend(added_rabbits)
        self.births_rabbit += len(added_rabbits)

        # Lisice – enaka logika kot zajci
        new_foxes = []
        for fx in self.foxes[:]:
            fx.update(dt, terrain, self.foxes, self.rabbits, new_foxes)
            if fx.dead:
                self.foxes.remove(fx)
        added_foxes = new_foxes[:max(0, cfg.max_foxes - len(self.foxes))]
        self.foxes.extend(added_foxes)
        self.births_fox += len(added_foxes)

        # Vzorčenje zgodovine vsake 30 korakov; radič štejemo samo aktivne (nepojede)
        if self.tick % 30 == 0:
            self.history_fox.append(len(self.foxes))
            self.history_rabbit.append(len(self.rabbits))
            active_clovers = sum(1 for c in self.clovers if not c.eaten)
            self.history_clover.append(active_clovers)
            # Omejimo historiko na 200 točk, da ne zasedamo pomnilnika
            for lst in (self.history_fox, self.history_rabbit, self.history_clover):
                if len(lst) > 200:
                    lst.pop(0)

        # Samodejni premor, ko izumrejo vse živali
        if len(self.foxes) == 0 and len(self.rabbits) == 0:
            self.paused = True


if __name__ == "__main__":
    main()
