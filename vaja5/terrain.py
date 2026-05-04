"""
terrain.py – štirje proceduralni generatorji terena in pomožne poizvedbe.

Vrste terena:
  1 = reka   – vijugasta reka z gozdnatimi bregovi
  2 = jezero – veliko jezero s pasovi plaže/trave/gozda + majhen ribnik
  3 = delta  – razvejajoči rečni kanali proti dnu mape
  4 = dolina – gorska dolina s conami, jezerom in potokom
"""

import random
import math
import numpy as np
import pygame

# Konstante tipa celice
WATER    = 0
SAND     = 1
GRASS    = 2
FOREST   = 3
MOUNTAIN = 4
PEAK     = 5


class Terrain:
    # Hrani 2D mrežo tipov celic in pripravljeno pygame površino za risanje.

    def __init__(self, cfg):
        self.cfg  = cfg
        self.rows = cfg.GRID_H
        self.cols = cfg.GRID_W
        self.cell = cfg.CELL

        self.grid    = np.zeros((self.rows, self.cols), dtype=np.int8)
        self.surface = pygame.Surface((cfg.MAP_W, cfg.MAP_H))

        self._generate(cfg.terrain_type)
        self._bake_surface()

    # Generatorji terena
    def _generate(self, terrain_type: int):
        t = terrain_type
        if   t == 1: self._gen_river()
        elif t == 2: self._gen_lake()
        elif t == 3: self._gen_delta()
        elif t == 4: self._gen_valley()
        else:        self._gen_river()

    # REKA
    def _gen_river(self):
        # Vijugasta reka čez mapo z gozdnatimi bregovi in peščenimi obalami.

        grid = self.grid
        rows, cols = self.rows, self.cols

        # Ena polovica gozd, druga trava
        grid[:rows // 2, :] = FOREST
        grid[rows // 2:, :] = GRASS

        # Parametri reke (vijugavost, širina, položaj) so delno naključni
        river_w   = random.randint(5, 8)
        amplitude = rows // 5
        freq      = 2 * math.pi / cols * 1.8
        center    = rows // 2 + random.randint(-rows // 8, rows // 8)
        phase     = random.uniform(0, math.pi * 2)

        # Za vsak stolpec izračunaj sredino reke in določi celice za vodo, pesek in gozd/travo.
        for c in range(cols):
            mid = int(center + amplitude * math.sin(freq * c + phase))

            # Travni koridor, ki čisti gozd vzdolž reke
            for r in range(max(0, mid - river_w - 8), min(rows, mid + river_w + 9)):
                if grid[r, c] == FOREST:
                    grid[r, c] = GRASS

            # Peščene obale na obeh bregovih
            for r in range(max(0, mid - river_w - 1), min(rows, mid + river_w + 2)):
                if grid[r, c] != WATER:
                    grid[r, c] = SAND

            # Voda reke
            for r in range(max(0, mid - river_w), min(rows, mid + river_w + 1)):
                grid[r, c] = WATER

        # Raztrosi gozdne lise po travnih conah
        for r in range(rows):
            for c in range(cols):
                if grid[r, c] == GRASS and random.random() < 0.07:
                    grid[r, c] = FOREST

    # JEZERO
    def _gen_lake(self):
        # Veliko organsko jezero s pasovi plaže/trave/gozda + majhen ribnik (zgoraj desno).
        grid = self.grid
        rows, cols = self.rows, self.cols

        # Osnovna plast je gozd
        grid[:] = FOREST

        # Središče glavnega jezera in njegove velikosti
        cx = int(cols * 0.44)
        cy = rows // 2
        rx = int(cols * 0.27)
        ry = int(rows * 0.30)

        # Za vsako celico izračunamo efektivno oddaljenost od središča jezera
        for r in range(rows):
            for c in range(cols):
                angle     = math.atan2(r - cy, c - cx)
                variation = (0.10 * math.sin(3 * angle)
                             + 0.07 * math.cos(5 * angle)
                             + 0.04 * math.sin(7 * angle - 1.1))
                d           = ((c - cx) / rx) ** 2 + ((r - cy) / ry) ** 2
                effective_r = d + variation

                if   effective_r < 0.88:  grid[r, c] = WATER
                elif effective_r < 1.05:  grid[r, c] = SAND
                elif effective_r < 1.65:  grid[r, c] = GRASS
                # ostalo ostane FOREST

        # Majhen ribnik (zgoraj desno)
        cx2, cy2 = int(cols * 0.80), int(rows * 0.22)
        rx2, ry2 = int(cols * 0.07), int(rows * 0.08)
        for r in range(rows):
            for c in range(cols):
                pond_dist = ((c - cx2) / rx2) ** 2 + ((r - cy2) / ry2) ** 2
                if   pond_dist < 1.0:                            grid[r, c] = WATER
                elif pond_dist < 1.3 and grid[r, c] != WATER:   grid[r, c] = SAND

        # Travne jase razpršene po gozdu
        for r in range(rows):
            for c in range(cols):
                if grid[r, c] == FOREST and random.random() < 0.10:
                    grid[r, c] = GRASS

    # DELTA
    def _gen_delta(self):
        # Rečna delta: več kanalov, ki se razprostirajo proti dnu mape.
        grid = self.grid
        rows, cols = self.rows, self.cols

        # Osnovna plast je trava
        grid[:] = GRASS

        # Število kanalov in izvorno mesto sta delno naključna
        num_channels = random.randint(4, 6)
        source_c     = cols // 2 + random.randint(-cols // 8, cols // 8)

        # Vsak kanal se širi in vijuga proti dnu, širina se povečuje s kvadratom razdalje od izvora.
        for ch in range(num_channels):
            spread = (ch - (num_channels - 1) / 2.0) / max(num_channels - 1, 1)

            prev_c = float(source_c)
            for r in range(rows):
                # Kanal se širi in razprostira ko se bliža dnu
                t        = r / rows
                target_c = source_c + spread * cols * 0.48 * t * t
                c_center = int(0.65 * target_c + 0.35 * prev_c)
                prev_c   = float(c_center)
                width = int(2 + t * 5 + random.uniform(0, 1.0))
                for c in range(max(0, c_center - width), min(cols, c_center + width + 1)):
                    grid[r, c] = WATER

        # Peščene obale ob vodi
        sand_cands = []
        for r in range(rows):
            for c in range(cols):
                if grid[r, c] == GRASS:
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1),
                                   (-1,-1), (-1,1), (1,-1), (1,1)):
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < rows and 0 <= nc < cols and grid[nr, nc] == WATER):
                            sand_cands.append((r, c))
                            break
        for r, c in sand_cands:
            grid[r, c] = SAND

        # Raztrosi gozdne lise v notranjosti
        for r in range(rows):
            for c in range(cols):
                if grid[r, c] == GRASS and random.random() < 0.10:
                    grid[r, c] = FOREST

    # DOLINA
    def _gen_valley(self):
        # Gorska dolina: pasovi terena, osrednje jezero in potok.
        grid = self.grid
        rows, cols = self.rows, self.cols

        cx    = cols / 2.0
        cy    = rows / 2.0
        max_d = math.hypot(cx, cy)

        # Pasovi terena so določeni z oddaljenostjo od središča + nekaj sinusnih motenj za bolj organski izgled.
        for r in range(rows):
            for c in range(cols):
                d     = math.hypot(c - cx, r - cy) / max_d
                angle = math.atan2(r - cy, c - cx)
                noise = (0.07 * math.sin(5 * angle + 1.2)
                         + 0.05 * math.cos(7 * angle - 0.8)
                         + 0.04 * math.sin(c * 0.08 + r * 0.06))
                noisy_d = d + noise

                if   noisy_d < 0.18:  grid[r, c] = GRASS
                elif noisy_d < 0.44:  grid[r, c] = FOREST
                elif noisy_d < 0.63:  grid[r, c] = MOUNTAIN
                else:                 grid[r, c] = PEAK

        # Osrednje jezero
        lake_r = max_d * 0.10
        sand_r = max_d * 0.14
        for r in range(rows):
            for c in range(cols):
                d_abs = math.hypot(c - cx, r - cy)
                if   d_abs < lake_r:  grid[r, c] = WATER
                elif d_abs < sand_r and grid[r, c] != WATER:
                    grid[r, c] = SAND

        # Potok teče iz jezera v naključni smeri
        ang  = random.uniform(0, 2 * math.pi)
        sdx  = math.cos(ang)
        sdy  = math.sin(ang)
        sx_f = cx
        sy_f = cy
        sw   = 1
        for i in range(int(max_d * 0.36)):
            sx_f += sdx + 0.04 * math.sin(i * 0.35)
            sy_f += sdy + 0.04 * math.cos(i * 0.42)
            sc, sr = int(sx_f), int(sy_f)
            for dr in range(-sw, sw + 1):
                for dc in range(-sw, sw + 1):
                    nr, nc = sr + dr, sc + dc
                    if (0 <= nr < rows and 0 <= nc < cols
                            and grid[nr, nc] not in (MOUNTAIN, PEAK)):
                        grid[nr, nc] = WATER

        # Peščene celice ob potoku
        for r in range(rows):
            for c in range(cols):
                if grid[r, c] in (GRASS, FOREST):
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < rows and 0 <= nc < cols
                                and grid[nr, nc] == WATER):
                            grid[r, c] = SAND
                            break

    # Priprava površine
    def _bake_surface(self):
        # Nariše vsako celico mreže kot obarvan pravokotnik na self.surface.
        cfg = self.cfg
        color_map = {
            WATER:    cfg.COLOR_WATER,
            SAND:     cfg.COLOR_SAND,
            GRASS:    cfg.COLOR_GRASS,
            FOREST:   cfg.COLOR_FOREST,
            MOUNTAIN: cfg.COLOR_MOUNTAIN,
            PEAK:     cfg.COLOR_PEAK,
        }
        surf = self.surface
        cell = self.cell

        # Za vsako celico v mreži narišemo pravokotnik z ustrezno barvo.
        for r in range(self.rows):
            for c in range(self.cols):
                color = color_map.get(int(self.grid[r, c]), cfg.COLOR_GRASS)
                pygame.draw.rect(surf, color, (c * cell, r * cell, cell, cell))

    # Znova generira in prevede teren po spremembi terrain_type.
    def rebake(self):
        self._generate(self.cfg.terrain_type)
        self._bake_surface()

    # Je celica na dani lokaciji voda?
    def is_water(self, px: float, py: float) -> bool:
        r, c = self._px_to_rc(px, py)
        return bool(self.grid[r, c] == WATER)

    # Vrne True če celica na položaju (px, py) ni voda.
    def is_passable(self, px: float, py: float) -> bool:
        r, c = self._px_to_rc(px, py)
        return self.grid[r, c] != WATER

    # PX -> RC (piksli v indeks celice)
    def _px_to_rc(self, px: float, py: float):
        c = int(max(0, min(self.cols - 1, px // self.cell)))
        r = int(max(0, min(self.rows - 1, py // self.cell)))
        return r, c

    # Vrne seznam (vrstica, stolpec) za vse kopne celice.
    def land_cells(self) -> list[tuple[int, int]]:
        return [(r, c)
                for r in range(self.rows)
                for c in range(self.cols)
                if self.grid[r, c] != WATER]

    # Poišče najbližjo vodo znotraj max_dist (v pikslih) od dane pozicije.
    def nearest_water(self, px: float, py: float, max_dist: float = 200) -> tuple | None:
        cell     = self.cell
        r0, c0   = self._px_to_rc(px, py)
        search_r = int(max_dist / cell) + 1

        best_dist = max_dist
        best_pos  = None

        # Preiščemo kvadrat okoli (r0, c0) z radijem search_r in poiščemo najbližjo celico z vodo.
        for dr in range(-search_r, search_r + 1):
            for dc in range(-search_r, search_r + 1):
                r = r0 + dr
                c = c0 + dc

                # Preverimo, ali je (r, c) znotraj meja mreže in ali je voda.
                if 0 <= r < self.rows and 0 <= c < self.cols:

                    # Če je celica voda, izračunamo njeno središče in oddaljenost od (px, py).
                    if self.grid[r, c] == WATER:
                        wx = c * cell + cell // 2
                        wy = r * cell + cell // 2
                        d  = math.hypot(wx - px, wy - py)
                        # Če je ta voda bližje od doslej najbližje, posodobimo best_dist in best_pos.
                        if d < best_dist:
                            best_dist = d
                            best_pos  = (wx, wy)

        return best_pos
