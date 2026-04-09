"""
config.py – vse nastavljive vrednosti simulacije na enem mestu.
UI lahko med izvajanjem spreminja vrednosti tega objekta.
"""

class Config:
    # ── okno ──────────────────────────────────────────────────────────────
    SCREEN_W    = 1500
    SCREEN_H    = 900
    FPS         = 60

    # ── teren ─────────────────────────────────────────────────────────────
    CELL        = 8          # velikost celice v pikslih
    GRID_W      = 120        # število celic po širini
    GRID_H      = 90         # število celic po višini

    # 1=reka, 2=jezero, 3=delta, 4=dolina
    terrain_type = 1

    # ── barve terena ──────────────────────────────────────────────────────
    COLOR_WATER    = (45,  105, 190)
    COLOR_SAND     = (205, 190, 130)
    COLOR_GRASS    = (75,  155,  55)
    COLOR_FOREST   = (25,   90,  25)
    COLOR_MOUNTAIN = (120, 112, 102)
    COLOR_PEAK     = (235, 238, 245)

    # ── začetne populacije ────────────────────────────────────────────────
    initial_foxes   = 8
    initial_rabbits = 30
    initial_clovers = 80

    max_foxes   = 120
    max_rabbits = 300
    max_clovers = 600

    # ── lastnosti plenilca (lisica) ───────────────────────────────────────
    fox_speed        = 55.0
    fox_size         = 12      # polmer v px
    fox_sense_radius = 90.0    # px
    fox_max_hunger   = 120.0   # sekunde do lakote
    fox_max_thirst   = 80.0    # sekunde do žeje
    fox_max_age      = 600.0
    fox_repro_drive  = 0.65
    fox_variation    = 0.10

    # ── lastnosti plena (zajec) ───────────────────────────────────────────
    rabbit_speed        = 45.0
    rabbit_size         = 8       # polmer v px
    rabbit_sense_radius = 70.0
    rabbit_max_hunger   = 90.0
    rabbit_max_thirst   = 60.0
    rabbit_max_age      = 480.0
    rabbit_repro_drive  = 0.60
    rabbit_variation    = 0.10

    # ── mutacija ──────────────────────────────────────────────────────────
    mutation_chance  = 0.10
    mutation_amount  = 0.20

    # ── hitrost simulacije ────────────────────────────────────────────────
    sim_speed = 1.0

    # ── simulacijsko področje (levo zgoraj) ───────────────────────────────
    VIEW_W  = 700   # širina simulacijske površine v px
    VIEW_H  = 494   # višina simulacijske površine v px

    # ── kamera ────────────────────────────────────────────────────────────
    cam_x   = 0
    cam_y   = 0
    cam_speed = 300

    @property
    def MAP_W(self):
        return self.GRID_W * self.CELL

    @property
    def MAP_H(self):
        return self.GRID_H * self.CELL
