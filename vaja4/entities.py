
# entities.py – razredi za vse entitete v simulaciji: lisice, zajci, radič

import math
import random
import pygame


# Razdalje med dvema točkama (Pitagorov izrek)
def _dist(ax, ay, bx, by):
    return math.hypot(bx - ax, by - ay)

# Vektor vzam skrajša na dolžino 1 (ohrani smer, normalizira dolžino)
def _normalize(dx, dy):
    d = math.hypot(dx, dy)
    if d < 1e-9:
        return 0.0, 0.0
    return dx / d, dy / d

# Variacija - Rojstvo nakljucno odstopanje +- 10 odstopanje od bazne vrednosti
def _vary(base: float, variation: float) -> float:
    return base * (1.0 + random.uniform(-variation, variation))

# z 10% verjetnostjo spremeni vrednost
def _mutate(value: float, cfg) -> float:
    """Z verjetnostjo mutation_chance spremeni vrednost za ±mutation_amount."""
    if random.random() < cfg.mutation_chance:
        value *= 1.0 + random.uniform(-cfg.mutation_amount, cfg.mutation_amount)
    return value

# Potomec podejuje povprečje lasnosti obeh staršev, nato aplicira variacijo in mutacijo
def _inherit(v_a: float, v_b: float, cfg) -> float:
    base = (v_a + v_b) / 2.0
    base = _vary(base, cfg.fox_variation)
    base = _mutate(base, cfg)
    return base


# Bazni razred za vse entitete
class Entity:
    def __init__(self, x: float, y: float, cfg):
        self.x    = x
        self.y    = y
        self.cfg  = cfg
        self.dead = False

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int):
        pass


# Radic (hrana za zajce)
class Clover(Entity):
    REGEN_TIME  = 20.0
    COLOR       = (155, 75, 210)   # vijolična
    COLOR_EATEN = ( 80, 38, 118)   # temnejša vijolična – pojeden radič

    def __init__(self, x, y, cfg):
        super().__init__(x, y, cfg)
        self.eaten       = False
        self.regen_timer = 0.0

    def update(self, dt, terrain, clover_list):
        pass   # radič se ne obnavlja – zaloga samo upada

    def eat(self):
        self.eaten = True

    def draw(self, surface, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        if self.eaten:
            pygame.draw.circle(surface, self.COLOR_EATEN, (sx, sy), 3)
        else:
            pygame.draw.circle(surface, self.COLOR, (sx, sy), 4)


# Osnovna žival – skupna logika za lisico in zajca
class Animal(Entity):
    """
    Prioritetna vrsta potreb (od najpomembnejše):
        Zajec:  beg → razmnoževanje → žeja → lakota → tavanje
        Lisica: razmnoževanje → žeja → lov → tavanje
    """

    def __init__(self, x, y, gender: str, cfg,
                 speed_base, size_base, sense_base,
                 max_hunger, max_thirst, max_age,
                 repro_drive, variation):
        super().__init__(x, y, cfg)

        self.gender = gender
        self.age    = 0.0
        self.dead   = False

        # Lastnosti z variacijo ±variation od bazne vrednosti
        self.speed        = _vary(speed_base,  variation)
        self.size         = max(3, int(_vary(size_base, variation)))
        self.sense_radius = _vary(sense_base,  variation)
        self.max_hunger   = _vary(max_hunger,  variation)
        self.max_thirst   = _vary(max_thirst,  variation)
        self.max_age      = _vary(max_age,     variation)
        self.repro_drive  = repro_drive

        self.hunger  = 0.0   # 0.0 = sito, 1.0 = smrt
        self.thirst  = 0.0   # 0.0 = napito, 1.0 = smrt
        self.repro   = 0.0   # 0.0 = brez želje, repro_drive = prag za iskanje partnerja

        self.repro_cooldown = random.uniform(20.0, 40.0)   # čakalna doba med paritvama
        self.newborn_timer  = 4.0   # sekunde rožnate barve ob rojstvu

        # Naključna začetna smer tavanja (normaliziran vektor)
        self._dir_x = random.choice([-1, 1]) * 1.0
        self._dir_y = random.choice([-1, 1]) * 1.0
        self._wander_timer = 0.0

        # Hitrost porabe:
        # žeje narašča z večjo hitrostjo;
        # lakota z večjo velikostjo
        self._thirst_rate = 1.0 / self.max_thirst * (1.0 + 0.3 * (self.speed / speed_base - 1))
        self._hunger_rate = 1.0 / self.max_hunger * (1.0 + 0.3 * (self.size  / size_base  - 1))

    # Splošna posodobitev (kliče se na začetku vsake update())
    def _base_update(self, dt, terrain):
        self.age          += dt
        self.newborn_timer = max(0.0, self.newborn_timer - dt * self.cfg.sim_speed)

        # Ko je bitje lačno, se poveča potreba po vodi
        thirst_mult  = 1.0 + 0.5 * (self.hunger / self.max_hunger) # do 50% hitreje, ko je lačno
        self.thirst += dt * self._thirst_rate * self.cfg.sim_speed * thirst_mult

        self.repro_cooldown = max(0.0, self.repro_cooldown - dt * self.cfg.sim_speed) # zmanjša cooldown
        self.hunger += dt * self._hunger_rate * self.cfg.sim_speed # lakota narašča s časom, hitreje za večje živali

        # Povečaj željo po razmnoževanju, če ni v cooldownu in ni kritično žejen/lakota
        if self.repro_cooldown <= 0:
            self.repro = min(1.0, self.repro + dt * 0.008 * self.cfg.sim_speed)

        # Smrt: če je žeja ali lakota kritična, ali če je presegla maksimalno starost
        if self.thirst >= 1.0 or self.hunger >= 1.0 or self.age >= self.max_age:
            self.dead = True

    def _drink(self, terrain):
        """Pije vodo, ko je bitje dovolj blizu vodne celice."""
        nearest = terrain.nearest_water(self.x, self.y, max_dist=self.cfg.CELL * 4)
        if nearest:
            wx, wy = nearest
            if _dist(self.x, self.y, wx, wy) < self.cfg.CELL * 3:
                self.thirst = max(0.0, self.thirst - 0.8 * self.cfg.sim_speed * 0.016)

    def _move_towards(self, tx, ty, dt, terrain):
        """
        Premakni se proti cilju s podporo za drsenje ob ovirah.
        Ko je neposredna pot blokirana, poskusi pravokotne smeri.
        """
        dx, dy = tx - self.x, ty - self.y
        if math.hypot(dx, dy) < 1.0:
            return

        nx, ny = _normalize(dx, dy)
        step   = self.speed * dt * self.cfg.sim_speed

        new_x = self.x + nx * step
        new_y = self.y + ny * step

        if terrain.is_passable(new_x, new_y):
            self.x, self.y = new_x, new_y
        else:
            moved = False
            if terrain.is_passable(new_x, self.y):
                self.x = new_x
                moved  = True
            if terrain.is_passable(self.x, new_y):
                self.y = new_y
                moved  = True

            if not moved:
                # Drsenje: poskusi 90° zarotiran vektor (v obe smeri)
                for perp_nx, perp_ny in ((-ny, nx), (ny, -nx)):
                    px = self.x + perp_nx * step * 0.8
                    py = self.y + perp_ny * step * 0.8
                    if terrain.is_passable(px, py):
                        self.x, self.y = px, py
                        break

        self._clamp(terrain)

    def _wander(self, dt, terrain):
        """Naključno tavanje – vsake 1.5–4 s izbere novo smer."""
        self._wander_timer -= dt
        if self._wander_timer <= 0: # čas za novo smer
            angle          = random.uniform(0, 2 * math.pi)
            self._dir_x    = math.cos(angle)
            self._dir_y    = math.sin(angle)
            self._wander_timer = random.uniform(1.5, 4.0)

        step  = self.speed * 0.4 * dt * self.cfg.sim_speed
        new_x = self.x + self._dir_x * step
        new_y = self.y + self._dir_y * step

        if terrain.is_passable(new_x, new_y): # neposredna pot prosta
            self.x, self.y = new_x, new_y
        elif terrain.is_passable(new_x, self.y): # poskusi premik samo v x smeri
            self.x         = new_x
            self._dir_y    = random.choice([-1, 1]) * abs(self._dir_y)
        elif terrain.is_passable(self.x, new_y): # poskusi premik samo v y smeri
            self.y         = new_y
            self._dir_x    = random.choice([-1, 1]) * abs(self._dir_x)
        else:
            # Popolnoma blokirano – takoj izberi novo smer
            angle          = random.uniform(0, 2 * math.pi)
            self._dir_x    = math.cos(angle)
            self._dir_y    = math.sin(angle)
            self._wander_timer = 0.2

        self._clamp(terrain)

    # Zagotovi, da bitje ostane znotraj meja
    def _clamp(self, terrain):
        cfg    = self.cfg
        self.x = max(0, min(cfg.MAP_W - 1, self.x))
        self.y = max(0, min(cfg.MAP_H - 1, self.y))

    # Risanje bitja: telo + obroč zaznavanja + statusni trakovi žeje/lakote
    def _draw_base(self, surface, cam_x, cam_y, color, outline, sense_ring_color):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        # Obroč zaznavanja
        pygame.draw.circle(surface, sense_ring_color, (sx, sy), int(self.sense_radius), 1)

        # Novorojene živali so rožnate – barva se postopno vrne na normalno
        if self.newborn_timer > 0:
            t = self.newborn_timer / 4.0   # 1.0 ob rojstvu → 0.0 po 4s
            color   = (
                int(color[0] * (1 - t) + 255 * t),
                int(color[1] * (1 - t) + 105 * t),
                int(color[2] * (1 - t) + 180 * t),
            )
            outline = (220, 80, 150)

        # Telo bitja
        pygame.draw.circle(surface, color,   (sx, sy), self.size)
        pygame.draw.circle(surface, outline, (sx, sy), self.size, 1)

        # Statusni trakovi nad bitjem: modra = žeja, rdeča = lakota
        bar_w = self.size * 2
        bar_h = 3
        bx    = sx - self.size
        by    = sy - self.size - 6

        pygame.draw.rect(surface, (25, 70, 190),
                         (bx, by, bar_w, bar_h))
        pygame.draw.rect(surface, (90, 175, 255),
                         (bx, by, int(bar_w * (1 - self.thirst)), bar_h))

        pygame.draw.rect(surface, (175, 25, 25),
                         (bx, by + bar_h + 1, bar_w, bar_h))
        pygame.draw.rect(surface, (255, 115, 75),
                         (bx, by + bar_h + 1, int(bar_w * (1 - self.hunger)), bar_h))


# Zajec (plen)
class Rabbit(Animal):
    COLOR        = (220, 220, 200)
    OUTLINE      = (140, 130, 110)
    SENSE_RING   = (200, 200, 155)

    def __init__(self, x, y, gender, cfg,
                 speed=None, size=None, sense=None,
                 max_hunger=None, max_thirst=None, max_age=None):
        c = cfg
        super().__init__(
            x, y, gender, cfg,
            speed_base  = speed       or c.rabbit_speed,
            size_base   = size        or c.rabbit_size,
            sense_base  = sense       or c.rabbit_sense_radius,
            max_hunger  = max_hunger  or c.rabbit_max_hunger,
            max_thirst  = max_thirst  or c.rabbit_max_thirst,
            max_age     = max_age     or c.rabbit_max_age,
            repro_drive = c.rabbit_repro_drive,
            variation   = c.rabbit_variation,
        )

    def update(self, dt, terrain, foxes, rabbits, clovers, new_rabbits: list):
        self._base_update(dt, terrain)
        if self.dead:
            return

        # Beg pred lisicami je absolutna prioriteta
        if self._flee(foxes, dt, terrain):
            return

        # Prioriteta 1: razmnoževanje – blokira se samo pri kritični žeji/lakoti
        if (self.repro >= self.repro_drive
                and self.repro_cooldown <= 0
                and self.thirst < 0.85
                and self.hunger < 0.90):
            partner = self._find_partner(rabbits) # poišče najboljšega partnerja glede na bližino in velikost
            if partner: # če najde partnerja, se premakne proti njemu; če je dovolj blizu, se razmnoži
                if _dist(self.x, self.y, partner.x, partner.y) < 14:
                    self._reproduce(partner, rabbits, new_rabbits)
                    self.repro          = 0.0
                    self.repro_cooldown = random.uniform(30.0, 60.0)
                    return
                self._move_towards(partner.x, partner.y, dt, terrain)
                return

        # Prioriteta 2: žeja
        if self.thirst > 0.45:
            water = terrain.nearest_water(self.x, self.y, 320) # išče v bližini
            if water: # če najde vodo, se premakne proti njej; če je dovolj blizu, pije
                self._move_towards(water[0], water[1], dt, terrain)
                self._drink(terrain)
                return

        # Prioriteta 3: lakota – išče najbližji nepojedeni radič
        if self.hunger > 0.40:
            target = self._find_food(clovers)
            if target:
                if _dist(self.x, self.y, target.x, target.y) < self.size + 6: # če je dovolj blizu, poje radič
                    target.eat()
                    self.hunger = max(0.0, self.hunger - 0.4)
                else: # če ni dovolj blizu, se premakne proti radiču
                    self._move_towards(target.x, target.y, dt, terrain)
                return

        self._wander(dt, terrain) # ce ni nobene potrebe, tava naokoli

    # Poišče najbližji nepojedeni radič znotraj zaznavnega območja
    def _find_food(self, clovers):
        best, bd = None, self.sense_radius
        for cl in clovers: # preveri vsak radič
            if cl.eaten:
                continue
            d = _dist(self.x, self.y, cl.x, cl.y) # izračuna razdaljo do radiča
            if d < bd: # če je bližje od dosedanjega najboljšega, ga nastavi kot novega najboljšega
                bd, best = d, cl
        return best

    # Poišče najboljšega partnerja: prednost večjemu in bližjemu.
    def _find_partner(self, rabbits):
        """Poišče najboljšega partnerja: prednost večjemu in bližjemu."""
        best, bd = None, self.sense_radius
        for rb in rabbits: # preveri vsakega zajca
            # izključi sebe, enak spol, tiste v cooldownu in mrtve
            if rb is self or rb.gender == self.gender or rb.repro_cooldown > 0 or rb.dead:
                continue
            d     = _dist(self.x, self.y, rb.x, rb.y)
            score = d / (rb.size + 1)   # manjši score = bliže in večji = boljši
            if score < bd: # če je boljši od dosedanjega najboljšega, ga nastavi kot novega najboljšega
                bd, best = score, rb
        return best

    # Ustvari novega zajca z lastnostmi, podedovanimi od obeh staršev, z variacijo in mutacijo
    def _reproduce(self, partner, rabbits, new_rabbits):
        cfg = self.cfg
        if len(rabbits) + len(new_rabbits) >= cfg.max_rabbits: # preveri, da ne preseže maksimalnega števila zajcev
            return

        # Ustvari 1-3 mladiče z naključnimi lastnostmi
        for _ in range(random.randint(1, 3)):
            gender = random.choice(["M", "F"])
            ox = self.x + random.uniform(-15, 15)
            oy = self.y + random.uniform(-15, 15)
            new_rabbits.append(Rabbit(
                ox, oy, gender, cfg,
                speed      = _mutate(_inherit(self.speed,        partner.speed,        cfg), cfg),
                size       = _mutate(_inherit(self.size,         partner.size,         cfg), cfg),
                sense      = _mutate(_inherit(self.sense_radius, partner.sense_radius, cfg), cfg),
                max_hunger = _mutate(_inherit(self.max_hunger,   partner.max_hunger,   cfg), cfg),
                max_thirst = _mutate(_inherit(self.max_thirst,   partner.max_thirst,   cfg), cfg),
                max_age    = _mutate(_inherit(self.max_age,      partner.max_age,      cfg), cfg),
            ))

    # Beži stran od vseh bližnjih lisic. Preveri, da ne beži k drugi lisici.
    def _flee(self, foxes, dt, terrain) -> bool:
        # preveri vsako lisico in zbere tiste, ki so znotraj zaznavnega območja
        nearby = [fx for fx in foxes
                  if _dist(self.x, self.y, fx.x, fx.y) < self.sense_radius]
        if not nearby:
            return False

        # Izračunaj povprečni vektor stran od vseh bližnjih lisic
        avg_dx = sum(self.x - fx.x for fx in nearby)
        avg_dy = sum(self.y - fx.y for fx in nearby)
        ndx, ndy = _normalize(avg_dx, avg_dy)

        # Preveri, da beg ne pelje naravnost k drugi oddaljenejši lisici
        tx, ty = self.x + ndx * 50, self.y + ndy * 50
        if any(_dist(tx, ty, fx.x, fx.y) < 30 for fx in foxes if fx not in nearby):
            ndx, ndy = -ndy, ndx   # zarotira smer za 90°

        step  = self.speed * 1.15 * dt * self.cfg.sim_speed
        new_x = self.x + ndx * step
        new_y = self.y + ndy * step

        if terrain.is_passable(new_x, new_y): # če je pot prosta, se premakne tja
            self.x, self.y = new_x, new_y
        else: #
            moved = False
            if terrain.is_passable(new_x, self.y): # poskusi premik samo v x smeri
                self.x = new_x
                moved  = True
            if terrain.is_passable(self.x, new_y): # poskusi premik samo v y smeri
                self.y = new_y
                moved  = True
            if not moved: # Drsenje: poskusi 90° zarotiran vektor (v obe smeri)
                for perp_nx, perp_ny in ((-ndy, ndx), (ndy, -ndx)):
                    px = self.x + perp_nx * step * 0.8
                    py = self.y + perp_ny * step * 0.8
                    if terrain.is_passable(px, py):
                        self.x, self.y = px, py
                        break

        self._clamp(terrain) # zagotovi, da zajec ostane znotraj meja
        return True

    # RISANJE
    def draw(self, surface, cam_x, cam_y):
        self._draw_base(surface, cam_x, cam_y, self.COLOR, self.OUTLINE, self.SENSE_RING)


# Lisica (plenilec)
class Fox(Animal):
    COLOR      = (220, 100, 30)
    OUTLINE    = (140,  60, 10)
    SENSE_RING = (255, 150, 55)

    def __init__(self, x, y, gender, cfg,
                 speed=None, size=None, sense=None,
                 max_hunger=None, max_thirst=None, max_age=None):
        c = cfg
        super().__init__(
            x, y, gender, cfg,
            speed_base  = speed       or c.fox_speed,
            size_base   = size        or c.fox_size,
            sense_base  = sense       or c.fox_sense_radius,
            max_hunger  = max_hunger  or c.fox_max_hunger,
            max_thirst  = max_thirst  or c.fox_max_thirst,
            max_age     = max_age     or c.fox_max_age,
            repro_drive = c.fox_repro_drive,
            variation   = c.fox_variation,
        )

    def update(self, dt, terrain, foxes, rabbits, new_foxes: list):
        self._base_update(dt, terrain)
        if self.dead:
            return

        # Prioriteta 1: razmnoževanje – blokira se samo pri kritični žeji/lakoti
        if (self.repro >= self.repro_drive
                and self.repro_cooldown <= 0
                and self.thirst < 0.85
                and self.hunger < 0.90):
            partner = self._find_partner(foxes) # poišče najboljšega partnerja glede na bližino in velikost
            if partner:
                if _dist(self.x, self.y, partner.x, partner.y) < 16: # če je dovolj blizu, se razmnoži
                    self._reproduce(partner, foxes, new_foxes)
                    self.repro          = 0.0
                    self.repro_cooldown = random.uniform(40.0, 80.0)
                    return
                self._move_towards(partner.x, partner.y, dt, terrain) # če ni dovolj blizu, se premakne proti partnerju
                return

        # Prioriteta 2: žeja
        if self.thirst > 0.45:
            water = terrain.nearest_water(self.x, self.y, 380) # išče v bližini
            if water: # če najde vodo, se premakne proti njej; če je dovolj blizu, pije
                self._move_towards(water[0], water[1], dt, terrain)
                self._drink(terrain)
                return

        # Prioriteta 3: lov
        if self.hunger > 0.30:
            prey = self._find_best_prey(rabbits) # poišče najboljši plen glede na bližino, velikost in hitrost
            if prey:
                # če je dovolj blizu, poje zajca (lakota se zmanjša, zajec umre)
                if _dist(self.x, self.y, prey.x, prey.y) < self.size + prey.size + 2:
                    prey.dead    = True
                    self.hunger  = max(0.0, self.hunger - 0.5)
                else: # če ni dovolj blizu, se premakne proti zajcu
                    self._move_towards(prey.x, prey.y, dt, terrain)
                return

        self._wander(dt, terrain) # ce ni nobene potrebe, tava naokoli

    # Poišče najboljši plen glede na bližino, velikost in hitrost
    def _find_best_prey(self, rabbits):
        best, best_score = None, float("inf")
        for rb in rabbits: # preveri vsakega zajca
            if rb.dead: # izključi mrtve zajce
                continue
            d = _dist(self.x, self.y, rb.x, rb.y)
            if d > self.sense_radius: # izključi zajce zunaj zaznavnega območja
                continue
            speed_factor = self.speed / max(rb.speed, 1.0)   # hitrejši plen je težje ujeti, zato zmanjša score
            score        = d / (rb.size * speed_factor + 1e-9)  # manjši score = bliže, večji in počasnejši = boljši
            if score < best_score: # če je boljši od dosedanjega najboljšega, ga nastavi kot novega najboljšega
                best_score, best = score, rb
        return best

    # Poišče najboljšega partnerja: prednost večjemu in bližjemu.
    def _find_partner(self, foxes):
        best, bd = None, self.sense_radius
        for fx in foxes: # preveri vsako lisico
            #  izključi sebe, enak spol, tiste v cooldownu in mrtve
            if fx is self or fx.gender == self.gender or fx.repro_cooldown > 0 or fx.dead:
                continue
            d     = _dist(self.x, self.y, fx.x, fx.y)
            score = d / (fx.size + 1)   # manjši score = bliže in večji = boljši
            if score < bd: # če je boljši od dosedanjega najboljšega, ga nastavi kot novega najboljšega
                bd, best = score, fx
        return best

    # Ustvari novega lisico z lastnostmi, podedovanimi od obeh staršev, z variacijo in mutacijo
    def _reproduce(self, partner, foxes, new_foxes):
        cfg = self.cfg
        if len(foxes) + len(new_foxes) >= cfg.max_foxes: # preveri, da ne preseže maksimalnega števila lisic
            return

        # Ustvari 1-2 mladiča z naključnimi lastnostmi
        for _ in range(random.randint(1, 2)):
            gender = random.choice(["M", "F"])
            ox = self.x + random.uniform(-15, 15)
            oy = self.y + random.uniform(-15, 15)
            new_foxes.append(Fox(
                ox, oy, gender, cfg,
                speed      = _mutate(_inherit(self.speed,        partner.speed,        cfg), cfg),
                size       = _mutate(_inherit(self.size,         partner.size,         cfg), cfg),
                sense      = _mutate(_inherit(self.sense_radius, partner.sense_radius, cfg), cfg),
                max_hunger = _mutate(_inherit(self.max_hunger,   partner.max_hunger,   cfg), cfg),
                max_thirst = _mutate(_inherit(self.max_thirst,   partner.max_thirst,   cfg), cfg),
                max_age    = _mutate(_inherit(self.max_age,      partner.max_age,      cfg), cfg),
            ))

    # RISANJE
    def draw(self, surface, cam_x, cam_y):
        self._draw_base(surface, cam_x, cam_y, self.COLOR, self.OUTLINE, self.SENSE_RING)
