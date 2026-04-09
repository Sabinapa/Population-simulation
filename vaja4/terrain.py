"""
terrain.py – generiranje štirih vrst terena in pomožnih funkcij.

Tipi terena:
  1 = reka (horizontalna/diagonalna)
  2 = jezero (eno veliko)
  3 = več manjših jezer
  4 = Perlinov šum (višinski pasovi)
"""

import random
import math
import numpy as np
import pygame

try:
    import noise as pnoise
    HAS_NOISE = True
except ImportError:
    HAS_NOISE = False


# Oznake celic
WATER  = 0
SAND   = 1
GRASS  = 2
FOREST = 3
MOUNTAIN = 4
PEAK   = 5


class Terrain:
    """
    Drži 2D mrežo tipov celic in pygame Surface za risanje.
    """

    def __init__(self, cfg):
        self.cfg  = cfg
        self.rows = cfg.GRID_H
        self.cols = cfg.GRID_W
        self.cell = cfg.CELL

        # 2D numpy polje tipov celic
        self.grid = np.zeros((self.rows, self.cols), dtype=np.int8)

        # Predpripravljena površina za risanje (ne rišemo vsake sličice znova)
        self.surface = pygame.Surface((cfg.MAP_W, cfg.MAP_H))

        self._generate(cfg.terrain_type)
        self._bake_surface()

    # ── generatorji ───────────────────────────────────────────────────────

    def _generate(self, terrain_type: int):
        t = terrain_type
        if   t == 1: self._gen_river()
        elif t == 2: self._gen_lake()
        elif t == 3: self._gen_multi_lake()
        elif t == 4: self._gen_perlin()
        else:        self._gen_river()

    def _gen_river(self):
        """Reka – sinusoidna pot čez celo karto."""
        g = self.grid
        g[:] = GRASS  # Začnemo z travo

        # Osnovna os reke (z-desno)
        rows, cols = self.rows, self.cols
        amplitude  = rows // 5
        frequency  = 2 * math.pi / cols * 1.5  # 1.5 periode

        center_row = rows // 2 + random.randint(-rows // 6, rows // 6)
        river_width = random.randint(3, 6)

        for c in range(cols):
            mid = int(center_row + amplitude * math.sin(frequency * c))
            for r in range(max(0, mid - river_width), min(rows, mid + river_width + 1)):
                g[r, c] = WATER
            # Pas peska ob reki
            for r in (mid - river_width - 1, mid + river_width + 1):
                if 0 <= r < rows:
                    g[r, c] = SAND

        # Dodamo gozd v notranjosti (naključni otočki)
        self._scatter_type(FOREST, density=0.08)

    def _gen_lake(self):
        """Eno veliko jezero v sredini."""
        g = self.grid
        g[:] = GRASS

        cx, cy = self.cols // 2, self.rows // 2
        rx = self.cols // 5
        ry = self.rows // 4

        for r in range(self.rows):
            for c in range(self.cols):
                # Elipsa
                if ((c - cx) / rx) ** 2 + ((r - cy) / ry) ** 2 < 1.0:
                    g[r, c] = WATER
                elif ((c - cx) / (rx + 1.5)) ** 2 + ((r - cy) / (ry + 1.5)) ** 2 < 1.0:
                    g[r, c] = SAND

        self._scatter_type(FOREST, density=0.07)

    def _gen_multi_lake(self):
        """Več manjših jezer."""
        g = self.grid
        g[:] = GRASS

        num_lakes = random.randint(4, 7)
        for _ in range(num_lakes):
            cx = random.randint(10, self.cols - 10)
            cy = random.randint(8,  self.rows - 8)
            rx = random.randint(4, 12)
            ry = random.randint(4, 10)

            for r in range(self.rows):
                for c in range(self.cols):
                    d = ((c - cx) / rx) ** 2 + ((r - cy) / ry) ** 2
                    if d < 1.0:
                        g[r, c] = WATER
                    elif d < 1.4 and g[r, c] != WATER:
                        g[r, c] = SAND

        self._scatter_type(FOREST, density=0.09)

    def _gen_perlin(self):
        """
        Perlinov šum → višinski pasovi.
        Padne nazaj na naključni terrain_type 1-3 če knjižnica ni nameščena.
        """
        if not HAS_NOISE:
            print("[Terrain] noise ni nameščen, padnem na reko.")
            self._gen_river()
            return

        cfg  = self.cfg
        seed = cfg.perlin_seed
        scale = cfg.perlin_scale
        octaves = cfg.perlin_octaves

        height_map = np.zeros((self.rows, self.cols))

        for r in range(self.rows):
            for c in range(self.cols):
                # pnoise.pnoise2 vrne vrednosti [-1, 1]
                val = pnoise.pnoise2(
                    (c + seed) / (self.cols / scale),
                    (r + seed) / (self.rows / scale),
                    octaves=octaves,
                    persistence=0.5,
                    lacunarity=2.0,
                    repeatx=10000,
                    repeaty=10000,
                    base=seed
                )
                height_map[r, c] = val

        # Normalizacija na [0, 1]
        hmin, hmax = height_map.min(), height_map.max()
        height_map = (height_map - hmin) / (hmax - hmin)

        # Dodelitev pasov
        g = self.grid
        for r in range(self.rows):
            for c in range(self.cols):
                h = height_map[r, c]
                if   h < cfg.HEIGHT_WATER:    g[r, c] = WATER
                elif h < cfg.HEIGHT_SAND:     g[r, c] = SAND
                elif h < cfg.HEIGHT_GRASS:    g[r, c] = GRASS
                elif h < cfg.HEIGHT_FOREST:   g[r, c] = FOREST
                elif h < cfg.HEIGHT_MOUNTAIN: g[r, c] = MOUNTAIN
                else:                          g[r, c] = PEAK

    # ── pomožne funkcije ──────────────────────────────────────────────────

    def _scatter_type(self, cell_type: int, density: float):
        """Naključno poseje celice tipa cell_type na kopno."""
        g = self.grid
        for r in range(self.rows):
            for c in range(self.cols):
                if g[r, c] == GRASS and random.random() < density:
                    g[r, c] = cell_type

    def _bake_surface(self):
        """Nariše celotno mrežo enkrat v Surface."""
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
        """Ali so koordinate (px, py) v vodi?"""
        r, c = self._px_to_rc(px, py)
        return bool(self.grid[r, c] == WATER)

    def is_passable(self, px: float, py: float) -> bool:
        """Ali je celica prehodna (= ni voda)?"""
        r, c = self._px_to_rc(px, py)
        t = self.grid[r, c]
        return t != WATER

    def _px_to_rc(self, px: float, py: float):
        c = int(max(0, min(self.cols - 1, px // self.cell)))
        r = int(max(0, min(self.rows - 1, py // self.cell)))
        return r, c

    def land_cells(self) -> list[tuple[int, int]]:
        """Vrne seznam vseh (r, c) celic, ki so prehodne."""
        return [(r, c)
                for r in range(self.rows)
                for c in range(self.cols)
                if self.grid[r, c] != WATER]

    def nearest_water(self, px: float, py: float, max_dist: float = 200) -> tuple | None:
        """
        Vrne (wx, wy) najbližje vodne celice znotraj max_dist,
        ali None če ni nobene.
        """
        cell = self.cell
        r0, c0 = self._px_to_rc(px, py)
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
