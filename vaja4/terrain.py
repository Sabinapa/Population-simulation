"""
terrain.py – generiranje štirih vrst terena in pomožnih funkcij.

Tipi terena:
  1 = reka    – vijugava reka z gozdnimi bregovi
  2 = jezero  – veliko jezero z obalnimi pasovi in satelitskim ribnikom
  3 = delta   – rečna delta z vejastimi rokavi in otoki
  4 = dolina  – gorska dolina s koncentričnimi pasovi in centralnim jezerom
"""

import random
import math
import numpy as np
import pygame

# Oznake celic
WATER    = 0
SAND     = 1
GRASS    = 2
FOREST   = 3
MOUNTAIN = 4
PEAK     = 5


class Terrain:
    """Drži 2D mrežo tipov celic in pygame Surface za risanje."""

    def __init__(self, cfg):
        self.cfg  = cfg
        self.rows = cfg.GRID_H
        self.cols = cfg.GRID_W
        self.cell = cfg.CELL

        self.grid    = np.zeros((self.rows, self.cols), dtype=np.int8)
        self.surface = pygame.Surface((cfg.MAP_W, cfg.MAP_H))

        self._generate(cfg.terrain_type)
        self._bake_surface()

    # ── generatorji ───────────────────────────────────────────────────────

    def _generate(self, terrain_type: int):
        t = terrain_type
        if   t == 1: self._gen_river()
        elif t == 2: self._gen_lake()
        elif t == 3: self._gen_delta()
        elif t == 4: self._gen_valley()
        else:        self._gen_river()

    def _gen_river(self):
        """Vijugava reka z gozdnimi bregovi in naplavnimi ravnicami."""
        g = self.grid
        rows, cols = self.rows, self.cols

        # Gozd na eni strani, trava na drugi
        g[:rows // 2, :] = FOREST
        g[rows // 2:, :] = GRASS

        river_w   = random.randint(5, 8)
        amplitude = rows // 5
        freq      = 2 * math.pi / cols * 1.8
        center    = rows // 2 + random.randint(-rows // 8, rows // 8)
        phase     = random.uniform(0, math.pi * 2)

        for c in range(cols):
            mid = int(center + amplitude * math.sin(freq * c + phase))

            # Travnati koridor ob reki
            for r in range(max(0, mid - river_w - 8), min(rows, mid + river_w + 9)):
                if g[r, c] == FOREST:
                    g[r, c] = GRASS

            # Peščene brežine
            for r in range(max(0, mid - river_w - 1), min(rows, mid + river_w + 2)):
                if g[r, c] != WATER:
                    g[r, c] = SAND

            # Voda reke
            for r in range(max(0, mid - river_w), min(rows, mid + river_w + 1)):
                g[r, c] = WATER

        # Gozdni otočki v travnatih pasovih
        for r in range(rows):
            for c in range(cols):
                if g[r, c] == GRASS and random.random() < 0.07:
                    g[r, c] = FOREST

    def _gen_lake(self):
        """Veliko jezero z organskim obrežjem, satelitskim ribnikom in gozdnimi pasovi."""
        g = self.grid
        rows, cols = self.rows, self.cols
        g[:] = FOREST

        # Glavno jezero (organsko oblikovano)
        cx  = int(cols * 0.44)
        cy  = rows // 2
        rx  = int(cols * 0.27)
        ry  = int(rows * 0.30)

        for r in range(rows):
            for c in range(cols):
                angle     = math.atan2(r - cy, c - cx)
                variation = (0.10 * math.sin(3 * angle)
                             + 0.07 * math.cos(5 * angle)
                             + 0.04 * math.sin(7 * angle - 1.1))
                d         = ((c - cx) / rx) ** 2 + ((r - cy) / ry) ** 2
                eff       = d + variation

                if   eff < 0.88:  g[r, c] = WATER
                elif eff < 1.05:  g[r, c] = SAND
                elif eff < 1.65:  g[r, c] = GRASS
                # ostalo ostane FOREST

        # Manjši satelitski ribnik (zgoraj desno)
        cx2, cy2 = int(cols * 0.80), int(rows * 0.22)
        rx2, ry2 = int(cols * 0.07), int(rows * 0.08)

        for r in range(rows):
            for c in range(cols):
                d2 = ((c - cx2) / rx2) ** 2 + ((r - cy2) / ry2) ** 2
                if   d2 < 1.0:                      g[r, c] = WATER
                elif d2 < 1.3 and g[r, c] != WATER: g[r, c] = SAND

        # Travnate jase v gozdu
        for r in range(rows):
            for c in range(cols):
                if g[r, c] == FOREST and random.random() < 0.10:
                    g[r, c] = GRASS

    def _gen_delta(self):
        """Rečna delta: reka se vejasto razlije v spodnji del karte."""
        g = self.grid
        rows, cols = self.rows, self.cols
        g[:] = GRASS

        num_channels = random.randint(4, 6)
        source_c     = cols // 2 + random.randint(-cols // 8, cols // 8)

        for ch in range(num_channels):
            spread = (ch - (num_channels - 1) / 2.0) / max(num_channels - 1, 1)

            prev_c = float(source_c)
            for r in range(rows):
                t        = r / rows
                target_c = source_c + spread * cols * 0.48 * t * t
                # Gladko sledenje
                c_center = int(0.65 * target_c + 0.35 * prev_c)
                prev_c   = float(c_center)

                width = int(2 + t * 5 + random.uniform(0, 1.0))
                for c in range(max(0, c_center - width), min(cols, c_center + width + 1)):
                    g[r, c] = WATER

        # Peščeni otočki ob vodnih kanalih
        sand_cands = []
        for r in range(rows):
            for c in range(cols):
                if g[r, c] == GRASS:
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1),
                                   (-1,-1), (-1,1), (1,-1), (1,1)):
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < rows and 0 <= nc < cols
                                and g[nr, nc] == WATER):
                            sand_cands.append((r, c))
                            break
        for r, c in sand_cands:
            g[r, c] = SAND

        # Gozdni pasovi v notranjosti
        for r in range(rows):
            for c in range(cols):
                if g[r, c] == GRASS and random.random() < 0.10:
                    g[r, c] = FOREST

    def _gen_valley(self):
        """
        Gorska dolina: koncentrični pasovi od roba (vrh/gora) proti
        središču (gozd → trava), z jezerom in potokom na dnu doline.
        """
        g = self.grid
        rows, cols = self.rows, self.cols

        cx     = cols / 2.0
        cy     = rows / 2.0
        max_d  = math.hypot(cx, cy)

        for r in range(rows):
            for c in range(cols):
                d     = math.hypot(c - cx, r - cy) / max_d
                angle = math.atan2(r - cy, c - cx)
                noise = (0.07 * math.sin(5 * angle + 1.2)
                         + 0.05 * math.cos(7 * angle - 0.8)
                         + 0.04 * math.sin(c * 0.08 + r * 0.06))
                dn = d + noise

                if   dn < 0.18:  g[r, c] = GRASS
                elif dn < 0.44:  g[r, c] = FOREST
                elif dn < 0.63:  g[r, c] = MOUNTAIN
                else:            g[r, c] = PEAK

        # Centralno jezero
        lake_r  = max_d * 0.10
        sand_r  = max_d * 0.14
        for r in range(rows):
            for c in range(cols):
                d_abs = math.hypot(c - cx, r - cy)
                if   d_abs < lake_r:  g[r, c] = WATER
                elif d_abs < sand_r and g[r, c] != WATER:
                    g[r, c] = SAND

        # Potok iz jezera v naključni smeri
        ang   = random.uniform(0, 2 * math.pi)
        sdx   = math.cos(ang)
        sdy   = math.sin(ang)
        sx_f  = cx
        sy_f  = cy
        sw    = 1
        for i in range(int(max_d * 0.36)):
            sx_f += sdx + 0.04 * math.sin(i * 0.35)
            sy_f += sdy + 0.04 * math.cos(i * 0.42)
            sc, sr = int(sx_f), int(sy_f)
            for dr in range(-sw, sw + 1):
                for dc in range(-sw, sw + 1):
                    nr, nc = sr + dr, sc + dc
                    if (0 <= nr < rows and 0 <= nc < cols
                            and g[nr, nc] not in (MOUNTAIN, PEAK)):
                        g[nr, nc] = WATER

        # Pesek ob potoku
        for r in range(rows):
            for c in range(cols):
                if g[r, c] in (GRASS, FOREST):
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < rows and 0 <= nc < cols
                                and g[nr, nc] == WATER):
                            g[r, c] = SAND
                            break

    # ── pomožne funkcije ──────────────────────────────────────────────────

    def _scatter_type(self, cell_type: int, density: float):
        g = self.grid
        for r in range(self.rows):
            for c in range(self.cols):
                if g[r, c] == GRASS and random.random() < density:
                    g[r, c] = cell_type

    def _bake_surface(self):
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
        for r in range(self.rows):
            for c in range(self.cols):
                color = color_map.get(int(self.grid[r, c]), cfg.COLOR_GRASS)
                pygame.draw.rect(surf, color, (c * cell, r * cell, cell, cell))

    def rebake(self):
        """Pokliči po spremembi terrain_type."""
        self._generate(self.cfg.terrain_type)
        self._bake_surface()

    # ── poizvedbe ─────────────────────────────────────────────────────────

    def is_water(self, px: float, py: float) -> bool:
        r, c = self._px_to_rc(px, py)
        return bool(self.grid[r, c] == WATER)

    def is_passable(self, px: float, py: float) -> bool:
        r, c = self._px_to_rc(px, py)
        return self.grid[r, c] != WATER

    def _px_to_rc(self, px: float, py: float):
        c = int(max(0, min(self.cols - 1, px // self.cell)))
        r = int(max(0, min(self.rows - 1, py // self.cell)))
        return r, c

    def land_cells(self) -> list[tuple[int, int]]:
        return [(r, c)
                for r in range(self.rows)
                for c in range(self.cols)
                if self.grid[r, c] != WATER]

    def nearest_water(self, px: float, py: float, max_dist: float = 200) -> tuple | None:
        cell     = self.cell
        r0, c0   = self._px_to_rc(px, py)
        search_r = int(max_dist / cell) + 1

        best_dist = max_dist
        best_pos  = None

        for dr in range(-search_r, search_r + 1):
            for dc in range(-search_r, search_r + 1):
                r = r0 + dr
                c = c0 + dc
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    if self.grid[r, c] == WATER:
                        wx = c * cell + cell // 2
                        wy = r * cell + cell // 2
                        d  = math.hypot(wx - px, wy - py)
                        if d < best_dist:
                            best_dist = d
                            best_pos  = (wx, wy)

        return best_pos
