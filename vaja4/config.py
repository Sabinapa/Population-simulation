"""
config.py – vse nastavljive vrednosti simulacije na enem mestu.
UI lahko med izvajanjem spreminja vrednosti tega objekta.
"""

class Config:
    # ── okno ──────────────────────────────────────────────────────────────
    SCREEN_W    = 1280
    SCREEN_H    = 780
    FPS         = 60

    # ── teren ─────────────────────────────────────────────────────────────
    CELL        = 8          # velikost celice v pikslih
    GRID_W      = 120        # število celic po širini
    GRID_H      = 90         # število celic po višini

    terrain_type = 1         # 1=reka, 2=jezero, 3=več jezer, 4=Perlin

    # Perlin nastavitve (samo za terrain_type == 4)
    perlin_scale  = 4.0
    perlin_octaves = 6
    perlin_seed   = 42

    # višinski pasovi (Perlin) – meje od 0.0 do 1.0
    # voda 40 %, pesek 2.5 %, trava 35 %, gozd 15 %, gora 5 %, vrh 2.5 %
    HEIGHT_WATER  = 0.40
    HEIGHT_SAND   = 0.425
    HEIGHT_GRASS  = 0.775
    HEIGHT_FOREST = 0.925
    HEIGHT_MOUNTAIN = 0.975
    # vrh gore: > 0.975

    # ── barve terena ──────────────────────────────────────────────────────
    COLOR_WATER    = (55,  120, 200)
    COLOR_SAND     = (210, 195, 140)
    COLOR_GRASS    = (80,  160,  60)
    COLOR_FOREST   = (30,  100,  30)
    COLOR_MOUNTAIN = (130, 120, 110)
    COLOR_PEAK     = (240, 240, 245)

    # ── začetne populacije ────────────────────────────────────────────────
    initial_foxes   = 8
    initial_rabbits = 30
    initial_clovers = 80

    max_foxes   = 60
    max_rabbits = 200
    max_clovers = 300

    # ── lastnosti plenilca (lisica) ───────────────────────────────────────
    fox_speed        = 55.0   # px/s
    fox_size         = 8      # polmer v px
    fox_sense_radius = 90     # px
    fox_max_hunger   = 120.0  # sekunde do lakote
    fox_max_thirst   = 80.0   # sekunde do žeje
    fox_max_age      = 600.0  # sekunde življenja
    fox_repro_drive  = 0.65   # prag [0..1] ko začne iskati partnerja
    fox_variation    = 0.10   # ± faktor naključne variacije

    # ── lastnosti plena (zajec) ───────────────────────────────────────────
    rabbit_speed        = 45.0
    rabbit_size         = 5
    rabbit_sense_radius = 70
    rabbit_max_hunger   = 90.0
    rabbit_max_thirst   = 60.0
    rabbit_max_age      = 480.0
    rabbit_repro_drive  = 0.60
    rabbit_variation    = 0.10

    # ── mutacija ──────────────────────────────────────────────────────────
    mutation_chance  = 0.10   # verjetnost mutacije posamezne lastnosti
    mutation_amount  = 0.20   # ± faktor mutacije

    # ── hitrost simulacije ────────────────────────────────────────────────
    sim_speed = 1.0           # množitelj časa (1.0 = normalno)

    # ── pomikanje prikaza ─────────────────────────────────────────────────
    VIEW_W  = 960   # širina vidnega področja simulacije
    VIEW_H  = 720   # višina vidnega področja simulacije
    cam_x   = 0     # odmik kamere v px
    cam_y   = 0
    cam_speed = 300  # px/s

    @property
    def MAP_W(self):
        return self.GRID_W * self.CELL

    @property
    def MAP_H(self):
        return self.GRID_H * self.CELL
