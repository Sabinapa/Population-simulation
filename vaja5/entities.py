
# entities.py – razredi entitet: Fox (lisica), Rabbit (zajec), Clover (radič)
import math
import random
import pygame

# ── Poimenovane konstante (zamenjajo magična števila v kodi) ──────────────────
REPRO_FILL_RATE     = 0.008   # hitrost polnjenja reprodukcijskega nagona na sekundo
DRINK_RATE          = 0.016   # zmanjšanje žeje na sekundo med pitjem
WANDER_SPEED_FACTOR = 0.4     # tavanje uporablja ta delež maksimalne hitrosti
RABBIT_MATE_RADIUS  = 14      # razdalja v pikslih za paritev zajcev
FOX_MATE_RADIUS     = 16      # razdalja v pikslih za paritev lisic
HUNT_SATIATION      = 0.5     # zmanjšanje lakote ko lisica ujame zajca


# ── Pomožne funkcije ──────────────────────────────────────────────────────────
def _dist(ax, ay, bx, by):
    # Vrne evklidsko razdaljo med dvema točkama.
    return math.hypot(bx - ax, by - ay)


def _normalize(dx, dy):
    # Vrne enotski vektor v smeri (dx, dy); (0, 0) če je dolžina nič.
    d = math.hypot(dx, dy)
    if d < 1e-9:
        return 0.0, 0.0
    return dx / d, dy / d


def _vary(base: float, variation: float) -> float:
    # Vrne base pomnožen z naključnim faktorjem v [1-variation, 1+variation].
    return base * (1.0 + random.uniform(-variation, variation))


def _mutate(value: float, cfg) -> float:
    # Z verjetnostjo mutation_chance premakne vrednost za ±mutation_amount.
    if random.random() < cfg.mutation_chance:
        value *= 1.0 + random.uniform(-cfg.mutation_amount, cfg.mutation_amount)
    return value


def _inherit(v_a: float, v_b: float, cfg) -> float:
    # Lastnost potomca = povprečje staršev, nato variacija in možna mutacija.
    base = (v_a + v_b) / 2.0
    base = _vary(base, cfg.fox_variation)
    base = _mutate(base, cfg)
    return base


# ── Osnovna entiteta ──────────────────────────────────────────────────────────
class Entity:
    def __init__(self, x: float, y: float, cfg):
        self.x    = x
        self.y    = y
        self.cfg  = cfg
        self.dead = False

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int):
        pass


# ── Clover – radič (hrana za zajce) ──────────────────────────────────────────
class Clover(Entity):
    REGEN_TIME  = 20.0
    COLOR       = (155, 75, 210)    # vijolična
    COLOR_EATEN = ( 80, 38, 118)    # temno vijolična – označevalec pojedenega radiča

    def __init__(self, x, y, cfg):
        super().__init__(x, y, cfg)
        self.eaten = False
        # Radič se ne obnavlja – zalogo se samo zmanjšuje
    def update(self, dt, terrain, clover_list):
        pass

    def eat(self):
        self.eaten = True

    def draw(self, surface, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        if self.eaten:
            pygame.draw.circle(surface, self.COLOR_EATEN, (sx, sy), 3)
        else:
            pygame.draw.circle(surface, self.COLOR, (sx, sy), 4)


# ── Osnovna žival ─────────────────────────────────────────────────────────────
class Animal(Entity):
    """
    Skupno obnašanje za vse živali.

    Vrstni red prioritet (od najvišje):
        Zajec:  beg > razmnoževanje > žeja > lakota > tavanje
        Lisica: razmnoževanje > žeja > lov > tavanje
    """

    def __init__(self, x, y, gender: str, cfg,
                 speed_base, size_base, sense_base,
                 max_hunger, max_thirst, max_age,
                 repro_drive, variation):
        super().__init__(x, y, cfg)

        self.gender = gender
        self.age    = 0.0

        # Lastnosti podedujejo variacijo ±variation od baznih vrednosti
        self.speed        = _vary(speed_base,  variation)
        self.size         = max(3, int(_vary(size_base, variation)))
        self.sense_radius = _vary(sense_base,  variation)
        self.max_hunger   = _vary(max_hunger,  variation)
        self.max_thirst   = _vary(max_thirst,  variation)
        self.max_age      = _vary(max_age,     variation)
        self.repro_drive  = repro_drive

        self.hunger  = 0.0   # 0.0 = sit, 1.0 = smrt
        self.thirst  = 0.0   # 0.0 = hidrirano, 1.0 = smrt
        self.repro   = 0.0   # 0.0 = brez nagona; repro_drive = prag za iskanje partnerja

        self.repro_cooldown = random.uniform(20.0, 40.0)
        self.newborn_timer  = 4.0   # sekunde rožnate barve pri rojstvu

        self._dir_x        = random.choice([-1, 1]) * 1.0
        self._dir_y        = random.choice([-1, 1]) * 1.0
        self._wander_timer = 0.0

        # Stopnje porabe se sorazmerno povečajo s hitrostjo (žeja) in velikostjo (lakota)
        self._thirst_rate = 1.0 / self.max_thirst * (1.0 + 0.3 * (self.speed / speed_base - 1))
        self._hunger_rate = 1.0 / self.max_hunger * (1.0 + 0.3 * (self.size  / size_base  - 1))

    # ── Osnovno posodabljanje na korak ────────────────────────────────────────
    def _base_update(self, dt, terrain):
        self.age          += dt
        self.newborn_timer = max(0.0, self.newborn_timer - dt * self.cfg.sim_speed)

        # Žeja narašča hitreje ko je žival lačna – dehidracija pospešuje lakoto
        thirst_mult  = 1.0 + 0.5 * (self.hunger / self.max_hunger)
        self.thirst += dt * self._thirst_rate * self.cfg.sim_speed * thirst_mult

        self.repro_cooldown = max(0.0, self.repro_cooldown - dt * self.cfg.sim_speed)
        self.hunger        += dt * self._hunger_rate * self.cfg.sim_speed

        if self.repro_cooldown <= 0:
            self.repro = min(1.0, self.repro + dt * REPRO_FILL_RATE * self.cfg.sim_speed)

        if self.thirst >= 1.0 or self.hunger >= 1.0 or self.age >= self.max_age:
            self.dead = True

    # ── Pitje ─────────────────────────────────────────────────────────────────
    def _drink(self, terrain):
        # Zmanjša žejo ko je žival dovolj blizu vodne celice.
        nearest = terrain.nearest_water(self.x, self.y, max_dist=self.cfg.CELL * 4)
        if nearest:
            wx, wy = nearest
            if _dist(self.x, self.y, wx, wy) < self.cfg.CELL * 3:
                self.thirst = max(0.0, self.thirst - DRINK_RATE * self.cfg.sim_speed)

    # ── Pomočniki za gibanje ──────────────────────────────────────────────────
    def _move_towards(self, tx, ty, dt, terrain):
        # Premakne se proti cilju; drsi vzdolž sten ko je neposredna pot blokirana.
        dx, dy = tx - self.x, ty - self.y
        if math.hypot(dx, dy) < 1.0:
            return
        nx, ny = _normalize(dx, dy)
        step   = self.speed * dt * self.cfg.sim_speed
        self._slide_move(nx, ny, step, terrain)
        self._clamp(terrain)

    def _slide_move(self, nx, ny, step, terrain):
        # Premakne se v smeri (nx, ny)*step; drsi ob ovirah če je pot blokirana.
        new_x = self.x + nx * step
        new_y = self.y + ny * step

        if terrain.is_passable(new_x, new_y):
            self.x, self.y = new_x, new_y
            return

        did_move = False
        if terrain.is_passable(new_x, self.y):
            self.x   = new_x
            did_move = True
        if terrain.is_passable(self.x, new_y):
            self.y   = new_y
            did_move = True

        if not did_move:
            # Poskusi pravokotne smeri kot zadnja možnost
            for perp_nx, perp_ny in ((-ny, nx), (ny, -nx)):
                px = self.x + perp_nx * step * 0.8
                py = self.y + perp_ny * step * 0.8
                if terrain.is_passable(px, py):
                    self.x, self.y = px, py
                    break

    def _wander(self, dt, terrain):
        # Naključno tavanje; izbere novo smer vsakih 1,5–4 sekunde.
        self._wander_timer -= dt
        if self._wander_timer <= 0:
            angle              = random.uniform(0, 2 * math.pi)
            self._dir_x        = math.cos(angle)
            self._dir_y        = math.sin(angle)
            self._wander_timer = random.uniform(1.5, 4.0)

        step  = self.speed * WANDER_SPEED_FACTOR * dt * self.cfg.sim_speed
        new_x = self.x + self._dir_x * step
        new_y = self.y + self._dir_y * step

        if terrain.is_passable(new_x, new_y):
            self.x, self.y = new_x, new_y
        elif terrain.is_passable(new_x, self.y):
            self.x      = new_x
            self._dir_y = random.choice([-1, 1]) * abs(self._dir_y)
        elif terrain.is_passable(self.x, new_y):
            self.y      = new_y
            self._dir_x = random.choice([-1, 1]) * abs(self._dir_x)
        else:
            angle              = random.uniform(0, 2 * math.pi)
            self._dir_x        = math.cos(angle)
            self._dir_y        = math.sin(angle)
            self._wander_timer = 0.2

        self._clamp(terrain)

    def _clamp(self, terrain):
        # Ohranja žival znotraj meja mape.
        cfg    = self.cfg
        self.x = max(0, min(cfg.MAP_W - 1, self.x))
        self.y = max(0, min(cfg.MAP_H - 1, self.y))

    # ── Risanje ───────────────────────────────────────────────────────────────
    def _draw_base(self, surface, cam_x, cam_y, color, outline, sense_ring_color):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        pygame.draw.circle(surface, sense_ring_color, (sx, sy), int(self.sense_radius), 1)

        # Novorojenčki se iz rožnate postopoma pobarvajo v naravno barvo v 4 sekundah
        if self.newborn_timer > 0:
            t = self.newborn_timer / 4.0
            color   = (
                int(color[0] * (1 - t) + 255 * t),
                int(color[1] * (1 - t) + 105 * t),
                int(color[2] * (1 - t) + 180 * t),
            )
            outline = (220, 80, 150)

        pygame.draw.circle(surface, color,   (sx, sy), self.size)
        pygame.draw.circle(surface, outline, (sx, sy), self.size, 1)

        # Vrstice stanja nad telesom: modra = hidracija, rdeča = sitost
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


# ── Rabbit – zajec ────────────────────────────────────────────────────────────
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

        # Beg pred lisicami je absolutna prednostna naloga
        if self._flee(foxes, dt, terrain):
            return

        # Prioriteta 1: razmnoževanje – ovirano le ob kritični žeji/lakoti
        if (self.repro >= self.repro_drive
                and self.repro_cooldown <= 0
                and self.thirst < 0.85
                and self.hunger < 0.90):
            partner = self._find_partner(rabbits)
            if partner:
                if _dist(self.x, self.y, partner.x, partner.y) < RABBIT_MATE_RADIUS:
                    self._reproduce(partner, rabbits, new_rabbits)
                    self.repro          = 0.0
                    self.repro_cooldown = random.uniform(30.0, 60.0)
                    return
                self._move_towards(partner.x, partner.y, dt, terrain)
                return

        # Prioriteta 2: žeja
        if self.thirst > 0.45:
            water = terrain.nearest_water(self.x, self.y, 320)
            if water:
                self._move_towards(water[0], water[1], dt, terrain)
                self._drink(terrain)
                return

        # Prioriteta 3: lakota – poišči najbližji nepojeden radič
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
        # Vrne najbližji nepojeden radič znotraj zaznavnega radija.
        best, best_score = None, self.sense_radius
        for clover in clovers:
            if clover.eaten:
                continue
            distance = _dist(self.x, self.y, clover.x, clover.y)
            if distance < best_score:
                best_score, best = distance, clover
        return best

    def _find_partner(self, rabbits):
        # Vrne najboljšega parnega kandidata (bližje in večje je boljše).
        best, best_score = None, self.sense_radius
        for rabbit in rabbits:
            if rabbit is self or rabbit.gender == self.gender or rabbit.repro_cooldown > 0 or rabbit.dead:
                continue
            distance = _dist(self.x, self.y, rabbit.x, rabbit.y)
            score    = distance / (rabbit.size + 1)   # manjše = bližje in večje
            if score < best_score:
                best_score, best = score, rabbit
        return best

    def _reproduce(self, partner, rabbits, new_rabbits):
        # Ustvari 1–3 potomce z podedovanimi in morda mutiranimi lastnostmi.
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
        # Beži stran od vseh lisic znotraj zaznavnega radija. Vrne True med begom.
        nearby = [fox for fox in foxes
                  if _dist(self.x, self.y, fox.x, fox.y) < self.sense_radius]
        if not nearby:
            return False

        # Povprečni vektor bega stran od vseh bližnjih lisic
        avg_dx = sum(self.x - fox.x for fox in nearby)
        avg_dy = sum(self.y - fox.y for fox in nearby)
        ndx, ndy = _normalize(avg_dx, avg_dy)

        # Zavrti 90° če pot bega vodi proti oddaljeni lisici
        tx, ty = self.x + ndx * 50, self.y + ndy * 50
        if any(_dist(tx, ty, fox.x, fox.y) < 30 for fox in foxes if fox not in nearby):
            ndx, ndy = -ndy, ndx

        step = self.speed * 1.15 * dt * self.cfg.sim_speed
        self._slide_move(ndx, ndy, step, terrain)
        self._clamp(terrain)
        return True

    def draw(self, surface, cam_x, cam_y):
        self._draw_base(surface, cam_x, cam_y, self.COLOR, self.OUTLINE, self.SENSE_RING)


# ── Fox – lisica ──────────────────────────────────────────────────────────────
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

        # Prioriteta 1: razmnoževanje – ovirano le ob kritični žeji/lakoti
        if (self.repro >= self.repro_drive
                and self.repro_cooldown <= 0
                and self.thirst < 0.85
                and self.hunger < 0.90):
            partner = self._find_partner(foxes)
            if partner:
                if _dist(self.x, self.y, partner.x, partner.y) < FOX_MATE_RADIUS:
                    self._reproduce(partner, foxes, new_foxes)
                    self.repro          = 0.0
                    self.repro_cooldown = random.uniform(40.0, 80.0)
                    return
                self._move_towards(partner.x, partner.y, dt, terrain)
                return

        # Prioriteta 2: žeja
        if self.thirst > 0.45:
            water = terrain.nearest_water(self.x, self.y, 380)
            if water:
                self._move_towards(water[0], water[1], dt, terrain)
                self._drink(terrain)
                return

        # Prioriteta 3: lov
        if self.hunger > 0.30:
            prey = self._find_best_prey(rabbits)
            if prey:
                if _dist(self.x, self.y, prey.x, prey.y) < self.size + prey.size + 2:
                    prey.dead   = True
                    self.hunger = max(0.0, self.hunger - HUNT_SATIATION)
                else:
                    self._move_towards(prey.x, prey.y, dt, terrain)
                return

        self._wander(dt, terrain)

    def _find_best_prey(self, rabbits):
        # Vrne zajca ki ga je najlažje ujeti: blizu, velik in počasen dobi boljši rezultat.
        best, best_score = None, float("inf")
        for rabbit in rabbits:
            if rabbit.dead:
                continue
            distance = _dist(self.x, self.y, rabbit.x, rabbit.y)
            if distance > self.sense_radius:
                continue
            speed_factor = self.speed / max(rabbit.speed, 1.0)
            score        = distance / (rabbit.size * speed_factor + 1e-9)
            if score < best_score:
                best_score, best = score, rabbit
        return best

    def _find_partner(self, foxes):
        # Vrne najboljšega parnega kandidata (bližje in večje je boljše).
        best, best_score = None, self.sense_radius
        for fox in foxes:
            if fox is self or fox.gender == self.gender or fox.repro_cooldown > 0 or fox.dead:
                continue
            distance = _dist(self.x, self.y, fox.x, fox.y)
            score    = distance / (fox.size + 1)
            if score < best_score:
                best_score, best = score, fox
        return best

    def _reproduce(self, partner, foxes, new_foxes):
        # Ustvari 1–2 potomca z podedovanimi in morda mutiranimi lastnostmi.
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
