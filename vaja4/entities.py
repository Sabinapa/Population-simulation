"""
entities.py – razredi za vse entitete v simulaciji.

Hierarhija:
    Entity (bazni razred)
    ├── Animal
    │   ├── Fox    (plenilec)
    │   └── Rabbit (plen)
    └── Clover     (hrana za zajce)
"""

import math
import random
import pygame


# ══════════════════════════════════════════════════════════════════════════════
# Pomožna matematika
# ══════════════════════════════════════════════════════════════════════════════

def _dist(ax, ay, bx, by):
    return math.hypot(bx - ax, by - ay)

def _normalize(dx, dy):
    d = math.hypot(dx, dy)
    if d < 1e-9:
        return 0.0, 0.0
    return dx / d, dy / d

def _vary(base: float, variation: float) -> float:
    return base * (1.0 + random.uniform(-variation, variation))

def _mutate(value: float, cfg) -> float:
    if random.random() < cfg.mutation_chance:
        value *= 1.0 + random.uniform(-cfg.mutation_amount, cfg.mutation_amount)
    return value

def _inherit(v_a: float, v_b: float, cfg) -> float:
    base = (v_a + v_b) / 2.0
    base = _vary(base, cfg.fox_variation)
    base = _mutate(base, cfg)
    return base


# ══════════════════════════════════════════════════════════════════════════════
# Bazni razred
# ══════════════════════════════════════════════════════════════════════════════

class Entity:
    def __init__(self, x: float, y: float, cfg):
        self.x    = x
        self.y    = y
        self.cfg  = cfg
        self.dead = False

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int):
        pass


# ══════════════════════════════════════════════════════════════════════════════
# Detelja (hrana)
# ══════════════════════════════════════════════════════════════════════════════

class Clover(Entity):
    REGEN_TIME  = 20.0
    COLOR       = (155, 75, 210)   # vijolična – radič
    COLOR_EATEN = ( 80, 38, 118)   # prosojno vijolična – pojeden radič (~50 % prosojnost)

    def __init__(self, x, y, cfg):
        super().__init__(x, y, cfg)
        self.eaten       = False
        self.regen_timer = 0.0

    def update(self, dt, terrain, clover_list):
        pass   # radič se ne obnavlja – hrana samo upada

    def eat(self):
        self.eaten = True

    def draw(self, surface, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        if self.eaten:
            # Prikaži pojeden radič kot temno/prosojno piko
            pygame.draw.circle(surface, self.COLOR_EATEN, (sx, sy), 3)
        else:
            pygame.draw.circle(surface, self.COLOR, (sx, sy), 4)


# ══════════════════════════════════════════════════════════════════════════════
# Osnovna žival
# ══════════════════════════════════════════════════════════════════════════════

class Animal(Entity):
    """
    Skupne lastnosti in logika za vse živali.

    Prioritetna vrsta potreb:
        1. Žeja
        2. Lakota
        3. Razmnoževanje
        4. Brezdelno tavanje
    """

    def __init__(self, x, y, gender: str, cfg,
                 speed_base, size_base, sense_base,
                 max_hunger, max_thirst, max_age,
                 repro_drive, variation):
        super().__init__(x, y, cfg)

        self.gender = gender
        self.age    = 0.0
        self.dead   = False

        self.speed        = _vary(speed_base,  variation)
        self.size         = max(3, int(_vary(size_base, variation)))
        self.sense_radius = _vary(sense_base,  variation)
        self.max_hunger   = _vary(max_hunger,  variation)
        self.max_thirst   = _vary(max_thirst,  variation)
        self.max_age      = _vary(max_age,     variation)
        self.repro_drive  = repro_drive

        self.hunger  = 0.0
        self.thirst  = 0.0
        self.repro   = 0.0

        self.repro_cooldown = random.uniform(20.0, 40.0)

        self._dir_x = random.choice([-1, 1]) * 1.0
        self._dir_y = random.choice([-1, 1]) * 1.0
        self._wander_timer = 0.0

        self._thirst_rate = 1.0 / self.max_thirst * (1.0 + 0.3 * (self.speed / speed_base - 1))
        self._hunger_rate = 1.0 / self.max_hunger * (1.0 + 0.3 * (self.size  / size_base  - 1))

    # ── splošna posodobitev ───────────────────────────────────────────────

    def _base_update(self, dt, terrain):
        self.age    += dt
        self.thirst += dt * self._thirst_rate * self.cfg.sim_speed
        self.repro_cooldown = max(0.0, self.repro_cooldown - dt)

        hunger_mult  = 1.0 + 0.5 * (self.thirst / self.max_thirst)
        self.hunger += dt * self._hunger_rate * self.cfg.sim_speed * hunger_mult

        if self.repro_cooldown <= 0:
            self.repro = min(1.0, self.repro + dt * 0.002 * self.cfg.sim_speed)

        if self.thirst >= 1.0 or self.hunger >= 1.0 or self.age >= self.max_age:
            self.dead = True

    def _drink(self, terrain):
        """Pije vodo ob robu vode (povečan doseg zaznavanja vode)."""
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

        # Poskusi diagonalno gibanje
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
        """Naključno tavanje s pametnim obravnavanjem ovir."""
        self._wander_timer -= dt
        if self._wander_timer <= 0:
            angle          = random.uniform(0, 2 * math.pi)
            self._dir_x    = math.cos(angle)
            self._dir_y    = math.sin(angle)
            self._wander_timer = random.uniform(1.5, 4.0)

        step  = self.speed * 0.4 * dt * self.cfg.sim_speed
        new_x = self.x + self._dir_x * step
        new_y = self.y + self._dir_y * step

        if terrain.is_passable(new_x, new_y):
            self.x, self.y = new_x, new_y
        elif terrain.is_passable(new_x, self.y):
            self.x         = new_x
            self._dir_y    = random.choice([-1, 1]) * abs(self._dir_y)
        elif terrain.is_passable(self.x, new_y):
            self.y         = new_y
            self._dir_x    = random.choice([-1, 1]) * abs(self._dir_x)
        else:
            # Popolnoma blokirano – takoj izberi novo smer
            angle          = random.uniform(0, 2 * math.pi)
            self._dir_x    = math.cos(angle)
            self._dir_y    = math.sin(angle)
            self._wander_timer = 0.2

        self._clamp(terrain)

    def _clamp(self, terrain):
        cfg    = self.cfg
        self.x = max(0, min(cfg.MAP_W - 1, self.x))
        self.y = max(0, min(cfg.MAP_H - 1, self.y))

    # ── risanje ───────────────────────────────────────────────────────────

    def _draw_base(self, surface, cam_x, cam_y, color, outline, sense_ring_color):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        # Krog zaznavanja (tanek obroč pred telesom)
        pygame.draw.circle(surface, sense_ring_color, (sx, sy), int(self.sense_radius), 1)

        # Telo bitja
        pygame.draw.circle(surface, color,   (sx, sy), self.size)
        pygame.draw.circle(surface, outline, (sx, sy), self.size, 1)

        # Statusni trakovi nad bitjem
        bar_w = self.size * 2
        bar_h = 3
        bx    = sx - self.size
        by    = sy - self.size - 6

        # Žeja (modra)
        pygame.draw.rect(surface, (25, 70, 190),
                         (bx, by, bar_w, bar_h))
        pygame.draw.rect(surface, (90, 175, 255),
                         (bx, by, int(bar_w * (1 - self.thirst)), bar_h))

        # Lakota (rdeča)
        pygame.draw.rect(surface, (175, 25, 25),
                         (bx, by + bar_h + 1, bar_w, bar_h))
        pygame.draw.rect(surface, (255, 115, 75),
                         (bx, by + bar_h + 1, int(bar_w * (1 - self.hunger)), bar_h))


# ══════════════════════════════════════════════════════════════════════════════
# Zajec (plen)
# ══════════════════════════════════════════════════════════════════════════════

class Rabbit(Animal):
    COLOR        = (220, 220, 200)
    OUTLINE      = (140, 130, 110)
    SENSE_RING   = (200, 200, 155)   # barva obroča zaznavanja

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

    # ── update ────────────────────────────────────────────────────────────

    def update(self, dt, terrain, foxes, rabbits, clovers, new_rabbits: list):
        self._base_update(dt, terrain)
        if self.dead:
            return

        # ── BEG pred lisicami (absolutna prioriteta – pred vsem) ──────────
        if self._flee(foxes, dt, terrain):
            return

        # ── PRIORITETA 1: razmnoževanje ───────────────────────────────────
        # Ob veliki želji za razmnoževanje preneha iskati vodo in hrano.
        # Blokira se samo pri kritični žeji/lakoti (tik pred smrtjo).
        if (self.repro >= self.repro_drive
                and self.repro_cooldown <= 0
                and self.thirst < 0.85
                and self.hunger < 0.90):
            partner = self._find_partner(rabbits)
            if partner:
                if _dist(self.x, self.y, partner.x, partner.y) < 14:
                    self._reproduce(partner, rabbits, new_rabbits)
                    self.repro          = 0.0
                    self.repro_cooldown = random.uniform(30.0, 60.0)
                    return
                self._move_towards(partner.x, partner.y, dt, terrain)
                return

        # ── PRIORITETA 2: žeja ────────────────────────────────────────────
        if self.thirst > 0.45:
            water = terrain.nearest_water(self.x, self.y, 320)
            if water:
                self._move_towards(water[0], water[1], dt, terrain)
                self._drink(terrain)
                return

        # ── PRIORITETA 3: lakota ──────────────────────────────────────────
        if self.hunger > 0.40:
            target = self._find_food(clovers)
            if target:
                if _dist(self.x, self.y, target.x, target.y) < self.size + 6:
                    target.eat()
                    self.hunger = max(0.0, self.hunger - 0.4)
                else:
                    self._move_towards(target.x, target.y, dt, terrain)
                return

        self._wander(dt, terrain)

    def _find_food(self, clovers):
        best, bd = None, self.sense_radius
        for cl in clovers:
            if cl.eaten:
                continue
            d = _dist(self.x, self.y, cl.x, cl.y)
            if d < bd:
                bd, best = d, cl
        return best

    def _find_partner(self, rabbits):
        best, bd = None, self.sense_radius
        for rb in rabbits:
            if rb is self or rb.gender == self.gender or rb.repro_cooldown > 0 or rb.dead:
                continue
            d     = _dist(self.x, self.y, rb.x, rb.y)
            score = d / (rb.size + 1)
            if score < bd:
                bd, best = score, rb
        return best

    def _reproduce(self, partner, rabbits, new_rabbits):
        cfg = self.cfg
        if len(rabbits) + len(new_rabbits) >= cfg.max_rabbits:
            return
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

    def _flee(self, foxes, dt, terrain) -> bool:
        nearby = [fx for fx in foxes
                  if _dist(self.x, self.y, fx.x, fx.y) < self.sense_radius]
        if not nearby:
            return False

        avg_dx = sum(self.x - fx.x for fx in nearby)
        avg_dy = sum(self.y - fx.y for fx in nearby)
        ndx, ndy = _normalize(avg_dx, avg_dy)

        # Preveri konflikt z oddaljeno lisico
        tx, ty = self.x + ndx * 50, self.y + ndy * 50
        if any(_dist(tx, ty, fx.x, fx.y) < 30 for fx in foxes if fx not in nearby):
            ndx, ndy = -ndy, ndx

        step  = self.speed * 1.15 * dt * self.cfg.sim_speed
        new_x = self.x + ndx * step
        new_y = self.y + ndy * step

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
                for perp_nx, perp_ny in ((-ndy, ndx), (ndy, -ndx)):
                    px = self.x + perp_nx * step * 0.8
                    py = self.y + perp_ny * step * 0.8
                    if terrain.is_passable(px, py):
                        self.x, self.y = px, py
                        break

        self._clamp(terrain)
        return True

    def draw(self, surface, cam_x, cam_y):
        self._draw_base(surface, cam_x, cam_y, self.COLOR, self.OUTLINE, self.SENSE_RING)


# ══════════════════════════════════════════════════════════════════════════════
# Lisica (plenilec)
# ══════════════════════════════════════════════════════════════════════════════

class Fox(Animal):
    COLOR      = (220, 100, 30)
    OUTLINE    = (140,  60, 10)
    SENSE_RING = (255, 150, 55)   # barva obroča zaznavanja

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

    # ── update ────────────────────────────────────────────────────────────

    def update(self, dt, terrain, foxes, rabbits, new_foxes: list):
        self._base_update(dt, terrain)
        if self.dead:
            return

        # ── PRIORITETA 1: razmnoževanje ───────────────────────────────────
        # Ob veliki želji za razmnoževanje preneha iskati vodo in hrano.
        # Blokira se samo pri kritični žeji/lakoti (tik pred smrtjo).
        if (self.repro >= self.repro_drive
                and self.repro_cooldown <= 0
                and self.thirst < 0.85
                and self.hunger < 0.90):
            partner = self._find_partner(foxes)
            if partner:
                if _dist(self.x, self.y, partner.x, partner.y) < 16:
                    self._reproduce(partner, foxes, new_foxes)
                    self.repro          = 0.0
                    self.repro_cooldown = random.uniform(40.0, 80.0)
                    return
                self._move_towards(partner.x, partner.y, dt, terrain)
                return

        # ── PRIORITETA 2: žeja ────────────────────────────────────────────
        if self.thirst > 0.45:
            water = terrain.nearest_water(self.x, self.y, 380)
            if water:
                self._move_towards(water[0], water[1], dt, terrain)
                self._drink(terrain)
                return

        # ── PRIORITETA 3: lov ─────────────────────────────────────────────
        if self.hunger > 0.30:
            prey = self._find_best_prey(rabbits)
            if prey:
                if _dist(self.x, self.y, prey.x, prey.y) < self.size + prey.size + 2:
                    prey.dead    = True
                    self.hunger  = max(0.0, self.hunger - 0.5)
                else:
                    self._move_towards(prey.x, prey.y, dt, terrain)
                return

        self._wander(dt, terrain)

    def _find_best_prey(self, rabbits):
        best, best_score = None, float("inf")
        for rb in rabbits:
            if rb.dead:
                continue
            d = _dist(self.x, self.y, rb.x, rb.y)
            if d > self.sense_radius:
                continue
            speed_factor = self.speed / max(rb.speed, 1.0)
            score        = d / (rb.size * speed_factor + 1e-9)
            if score < best_score:
                best_score, best = score, rb
        return best

    def _find_partner(self, foxes):
        best, bd = None, self.sense_radius
        for fx in foxes:
            if fx is self or fx.gender == self.gender or fx.repro_cooldown > 0 or fx.dead:
                continue
            d     = _dist(self.x, self.y, fx.x, fx.y)
            score = d / (fx.size + 1)
            if score < bd:
                bd, best = score, fx
        return best

    def _reproduce(self, partner, foxes, new_foxes):
        cfg = self.cfg
        if len(foxes) + len(new_foxes) >= cfg.max_foxes:
            return
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

    def draw(self, surface, cam_x, cam_y):
        self._draw_base(surface, cam_x, cam_y, self.COLOR, self.OUTLINE, self.SENSE_RING)
