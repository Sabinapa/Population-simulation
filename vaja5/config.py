
class Config:
    """
    Centralna konfiguracija simulacije ekosistema.
    UPPER_CASE = fiksne konstante (okno, teren, barve).
    snake_case = nastavljivi simulacijski parametri in spremenljivo stanje.
    """

    # Okno
    SCREEN_W    = 1500          # širina okna v pikslih
    SCREEN_H    = 900           # višina okna v pikslih
    FPS         = 60            # največje število sličic na sekundo

    # Teren
    CELL        = 8             # velikost ene celice mreže v pikslih
    GRID_W      = 120           # število celic po širini mape
    GRID_H      = 90            # število celic po višini mape

    # 1=reka, 2=jezero, 3=delta, 4=dolina
    terrain_type = 1            # tip generiranega terena

    # Barve terena
    COLOR_WATER    = (45,  105, 190)    # barva vode
    COLOR_SAND     = (205, 190, 130)    # barva peska ob vodi
    COLOR_GRASS    = (75,  155,  55)    # barva trave
    COLOR_FOREST   = (25,   90,  25)    # barva gozda
    COLOR_MOUNTAIN = (120, 112, 102)    # barva gore
    COLOR_PEAK     = (235, 238, 245)    # barva snežnega vrha

    # Začetne populacije
    initial_foxes   = 8         # število lisic ob zagonu
    initial_rabbits = 30        # število zajcev ob zagonu
    initial_clovers = 80        # število radičev ob zagonu

    max_foxes   = 120           # največje dovoljeno število lisic
    max_rabbits = 300           # največje dovoljeno število zajcev
    max_clovers = 600           # največje dovoljeno število radičev

    # Lastnosti plenilca (lisica)
    fox_speed        = 55.0     # osnovna hitrost gibanja v px/s
    fox_size         = 12       # polmer telesa v px
    fox_sense_radius = 90.0     # radij zaznavanja okolice v px
    fox_max_hunger   = 120.0    # sekunde do smrti od lakote
    fox_max_thirst   = 80.0     # sekunde do smrti od žeje
    fox_max_age      = 600.0    # največja starost v sekundah
    fox_repro_drive  = 0.65     # prag reprodukcijskega nagona (0–1)
    fox_variation    = 0.10     # naključno odstopanje lastnosti pri rojstvu (±10 %)

    # Lastnosti plena (zajec)
    rabbit_speed        = 45.0  # osnovna hitrost gibanja v px/s
    rabbit_size         = 8     # polmer telesa v px
    rabbit_sense_radius = 70.0  # radij zaznavanja okolice v px
    rabbit_max_hunger   = 90.0  # sekunde do smrti od lakote
    rabbit_max_thirst   = 60.0  # sekunde do smrti od žeje
    rabbit_max_age      = 480.0 # največja starost v sekundah
    rabbit_repro_drive  = 0.60  # prag reprodukcijskega nagona (0–1)
    rabbit_variation    = 0.10  # naključno odstopanje lastnosti pri rojstvu (±10 %)

    # Mutacija
    mutation_chance  = 0.10     # verjetnost mutacije pri rojstvu (10 %)
    mutation_amount  = 0.20     # največja sprememba vrednosti pri mutaciji (±20 %)

    # Hitrost simulacije
    sim_speed = 1.0             # množitelj hitrosti (1.0 = normalno)

    # Simulacijsko področje (levo zgoraj)
    VIEW_W  = 700               # širina simulacijske površine v px
    VIEW_H  = 494               # višina simulacijske površine v px

    # Kamera
    cam_x    = 0                # horizontalni odmik kamere v px
    cam_y    = 0                # vertikalni odmik kamere v px
    cam_speed = 300             # hitrost premikanja kamere v px/s

    # Izračun velikosti mape v piksljih na osnovi števila celic in velikosti celice širine in višine
    @property
    def MAP_W(self):
        return self.GRID_W * self.CELL

    @property
    def MAP_H(self):
        return self.GRID_H * self.CELL