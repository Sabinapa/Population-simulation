# Vaja 5 – Čiščenje kode (Refactoring)

> Refaktorirana kopija vaje 4 – delovanje simulacije ostane **nespremenjeno**, izboljšamo samo strukturo in berljivost kode.
> Vsaka sprememba sledi enemu od desetih principov čistega kodiranja.

## Zagon

```bash
cd vaja5
python main.py
```

## Struktura projekta

```
vaja5/
├── main.py        ← vstopna točka + razred Simulation
├── config.py      ← centralna konfiguracija
├── terrain.py     ← generiranje 4 vrst terena
├── entities.py    ← Fox, Rabbit, Clover
└── ui.py          ← pygame UI
```

---

## Načrt čiščenja kode

> Za vsako smernico: **kaj spremenimo**, **zakaj**, **primer pred** in **primer po**.

---

### 1. Smiselna imena spremenljivk, funkcij in razredov

**Zakaj:** Kratice in enočrkovne spremenljivke prisilijo bralca, da si zapomni pomen. `bd` je nerazumljivo – `best_score` je takoj jasno.

| Datoteka | Pred | Po |
|---|---|---|
| `entities.py` | `bd` | `best_score` |
| `entities.py` | `cl` (v for zanki) | `clover` |
| `entities.py` | `rb` (v for zanki) | `rabbit` |
| `entities.py` | `fx` (v for zanki) | `fox` |
| `terrain.py` | `g` (lokalni alias) | `grid` |
| `terrain.py` | `dn` | `noisy_d` |
| `terrain.py` | `eff` | `effective_r` |
| `terrain.py` | `d2` | `pond_dist` |
| `ui.py` | `lh` | `label_height` |
| `ui.py` | `fsm`, `fbd`, `fh2` | `small_h`, `body_h`, `h2_h` |
| `ui.py` | `bw`, `tw` | `btn_w`, `terrain_btn_w` |
| `ui.py` | `mx`, `mt`, `mb`, `mr` (v _draw_graph_panel) | `margin_left`, `margin_top`, `margin_bottom`, `margin_right` |
| `entities.py` | `moved` (v `_slide_move`) | `did_move` |

**Pred:**
```python
# entities.py
best, bd = None, self.sense_radius
for cl in clovers:
    if cl.eaten:
        continue
    d = _dist(self.x, self.y, cl.x, cl.y)
    if d < bd:
        bd, best = d, cl
```

**Po:**
```python
best, best_score = None, self.sense_radius
for clover in clovers:
    if clover.eaten:
        continue
    distance = _dist(self.x, self.y, clover.x, clover.y)
    if distance < best_score:
        best_score, best = distance, clover
```

---

### 2. Konsistentna oblika poimenovanj

**Zakaj:** `PEP 8` standard: razredi → `CamelCase`, konstante → `UPPER_CASE`, navadne spremenljivke → `snake_case`. `Config` razred mešanega sloga.

**Pred (`config.py`):**
```python
class Config:
    SCREEN_W    = 1500     # UPPER_CASE ✅ – prava konstanta
    VIEW_W      = 700      # UPPER_CASE – a se med izvajanjem ne spremeni?
    cam_x       = 0        # snake_case – mutable stanje, ne nastavitev
    fox_speed   = 55.0     # snake_case ✅
```

**Po – dodamo docstring ki jasno razloži konvencijo:**
```python
class Config:
    """
    Centralna konfiguracija simulacije ekosistema.
    UPPER_CASE = fiksne konstante (okno, teren, barve).
    snake_case = nastavljivi simulacijski parametri.
    """
    SCREEN_W  = 1500   # fiksna dimenzija okna
    VIEW_W    = 700    # fiksna širina simulacijske površine
    cam_x     = 0      # kamera – mutable stanje
    fox_speed = 55.0   # nastavljiv parameter
```

---

### 3. Koda, ki se sama komentira (Self-documenting code)

**Zakaj:** Magična števila zahtevajo komentar da sploh veš kaj pomenijo. Poimenovane konstante so komentar, ki ne zastara.

| Datoteka | Vrstica | Magično število | Konstanta |
|---|---|---|---|
| `entities.py` | 136 | `0.008` | `REPRO_FILL_RATE` |
| `entities.py` | 148 | `0.016` | `DRINK_RATE` |
| `entities.py` | 196 | `0.4` | `WANDER_SPEED_FACTOR` |
| `entities.py` | 300 | `14` | `RABBIT_MATE_RADIUS` |
| `entities.py` | 457 | `16` | `FOX_MATE_RADIUS` |
| `entities.py` | 480 | `0.5` | `HUNT_SATIATION` |
| `main.py` | 162 | `30` | `HISTORY_SAMPLE_INTERVAL` |
| `main.py` | 169 | `200` | `HISTORY_MAX_POINTS` |

**Pred:**
```python
self.repro = min(1.0, self.repro + dt * 0.008 * self.cfg.sim_speed)
...
self.thirst = max(0.0, self.thirst - 0.8 * self.cfg.sim_speed * 0.016)
```

**Po (konstante na vrhu `entities.py`):**
```python
REPRO_FILL_RATE  = 0.008   # hitrost polnjenja reprodukcijskega nagona na sekundo
DRINK_RATE       = 0.016   # zmanjšanje žeje na sekundo med pitjem
...
self.repro = min(1.0, self.repro + dt * REPRO_FILL_RATE * self.cfg.sim_speed)
self.thirst = max(0.0, self.thirst - DRINK_RATE * self.cfg.sim_speed)
```

---

### 4. Konsistentna oblika kode

**Zakaj:** Mešanje jezikov v komentarjih otežuje vzdrževanje. Ker je projekt slovensko akademsko delo, so vsi komentarji in docstringi enotno v slovenščini. UI besedilo (gumbi, oznake) je prav tako v slovenščini.

**Pred (`entities.py`, `main.py`):**
```python
# Razdalje med dvema točkama         ← trivialni komentar, ki samo ponovi ime funkcije
def _dist(ax, ay, bx, by):
    ...

self.dead = False   # ali je mrtev    ← trivialni komentar
self.tick += 1                        # brez komentarja
```

**Po – enotna slovenščina, trivialni komentarji odstranjeni:**
```python
def _dist(ax, ay, bx, by):
    """Vrne evklidsko razdaljo med dvema točkama."""
    ...

self.dead = False
self.tick += 1
```

> **Pravilo:** Ohrani samo komentarje ki razložijo **zakaj** – ne kaj koda počne. Trivialni komentarji ki samo ponavljajo kodo se odstranijo.

---

### 5. Samo en nivo zamika v desno

**Zakaj:** Globoko gnezdena koda (4+ ravni) je težko sledljiva. Signal da je čas za izvleček pomožne funkcije.

**Pred (`entities.py` – metoda `_flee`, ~4 nivoji):**
```python
def _flee(self, foxes, dt, terrain):
    nearby = [fx for fx in foxes if ...]
    if not nearby:
        return False
    ...
    if not terrain.is_passable(new_x, new_y):
        moved = False
        if terrain.is_passable(new_x, self.y):
            self.x = new_x
            moved = True
        if terrain.is_passable(self.x, new_y):
            self.y = new_y
            moved = True
        if not moved:
            for perp_nx, perp_ny in (...):
                if terrain.is_passable(px, py):   # ← 4. nivo
                    self.x, self.y = px, py
                    break
```

**Po – slide logika izvlečena v pomožno metodo:**
```python
def _flee(self, foxes, dt, terrain):
    nearby = [fox for fox in foxes
              if _dist(self.x, self.y, fox.x, fox.y) < self.sense_radius]
    if not nearby:
        return False
    avg_dx = sum(self.x - fox.x for fox in nearby)
    avg_dy = sum(self.y - fox.y for fox in nearby)
    ndx, ndy = _normalize(avg_dx, avg_dy)
    if any(_dist(self.x + ndx*50, self.y + ndy*50, fox.x, fox.y) < 30
           for fox in foxes if fox not in nearby):
        ndx, ndy = -ndy, ndx
    step = self.speed * 1.15 * dt * self.cfg.sim_speed
    self._slide_move(ndx, ndy, step, terrain)
    self._clamp(terrain)
    return True

def _slide_move(self, nx, ny, step, terrain):
    """Premakne se v smeri (nx,ny)*step; drsi ob ovirah če je pot blokirana."""
    new_x = self.x + nx * step
    new_y = self.y + ny * step
    if terrain.is_passable(new_x, new_y):
        self.x, self.y = new_x, new_y
        return
    if terrain.is_passable(new_x, self.y):
        self.x = new_x
    if terrain.is_passable(self.x, new_y):
        self.y = new_y
        return
    for perp_nx, perp_ny in ((-ny, nx), (ny, -nx)):
        px = self.x + perp_nx * step * 0.8
        py = self.y + perp_ny * step * 0.8
        if terrain.is_passable(px, py):
            self.x, self.y = px, py
            return
```

> Ista `_slide_move` metoda se uporablja v `_move_towards` in `_flee` – **odpravimo podvajanje kode**.

---

### 6. Izogibanje ključni besedi `else`

**Zakaj:** Ko blok `if` vsebuje `return`, je `else` odveč – koda za njim se izvede samo takrat ko `if` ni bil resničen, kar je implicitno.

**Pred (`entities.py`):**
```python
if terrain.is_passable(new_x, new_y):
    self.x, self.y = new_x, new_y
else:                     # ← else je odveč
    moved = False
    if terrain.is_passable(new_x, self.y):
        ...
```

*(V kodi `else` ni dobesedno napisan, a `moved` flag vzorec ima isti učinek – nadomeščamo ga s `_slide_move`.)*

**Pred (`ui.py` – `_draw_bottom_panel`):**
```python
if sim.running and sim.foxes:
    f_age = sum(e.age for e in sim.foxes) / len(sim.foxes)
    ...
else:
    f_age = f_size = f_hunger = f_thirst = f_speed = f_sense = 0.0
```

**Po – guard clause na začetku:**
```python
f_age = f_size = f_hunger = f_thirst = f_speed = f_sense = 0.0
if sim.running and sim.foxes:
    f_age    = sum(e.age    for e in sim.foxes) / len(sim.foxes)
    f_size   = sum(e.size   for e in sim.foxes) / len(sim.foxes)
    ...
```

---

### 7. Enkapsulacija primitivnih tipov s specifičnim obnašanjem

**Zakaj:** `hunger`, `thirst` sta navadna `float`, a imata pravila: vedno med 0–1, ob 1.0 nastopi smrt. Ta pravila so razpršena po vsej kodi.

**Pred (`entities.py`):**
```python
self.hunger = 0.0
self.thirst = 0.0
...
self.hunger += dt * self._hunger_rate * self.cfg.sim_speed
if self.thirst >= 1.0 or self.hunger >= 1.0 or self.age >= self.max_age:
    self.dead = True
```

**Po – nov razred na vrhu `entities.py`:**
```python
class DriveLevel:
    """Nagon kot float, omejen na [0,0, 1,0]; spremlja kritično/smrtonosno stanje."""

    def __init__(self, initial: float = 0.0):
        self._v = float(initial)

    @property
    def value(self) -> float:
        return self._v

    def increase(self, amount: float) -> None:
        self._v = min(1.0, self._v + amount)

    def decrease(self, amount: float) -> None:
        self._v = max(0.0, self._v - amount)

    def is_lethal(self) -> bool:
        return self._v >= 1.0

    def __float__(self) -> float:
        return self._v

    def __lt__(self, other) -> bool:
        return self._v < float(other)

    def __gt__(self, other) -> bool:
        return self._v > float(other)
```

Nato v `Animal`:
```python
self.hunger = DriveLevel()
self.thirst = DriveLevel()
...
self.hunger.increase(dt * self._hunger_rate * self.cfg.sim_speed)
if self.thirst.is_lethal() or self.hunger.is_lethal() or self.age >= self.max_age:
    self.dead = True
```

---

### 8. Primerno število vrstic razredov in metod

**Zakaj:** Metoda z 99 vrsticami dela preveč.

| Datoteka | Metoda | Zdaj | Cilj |
|---|---|---|---|
| `ui.py` | `__init__` | ~99 vrstic | `_init_fonts()`, `_init_surfaces()`, `_init_buttons()`, `_init_sliders()` |
| `ui.py` | `_draw_bottom_panel` | ~99 vrstic | `_draw_col1_controls()`, `_draw_col1_live_stats()`, `_draw_col2_fox_sliders()`, `_draw_col3_rabbit_sliders()` |
| `main.py` | `update` | ~50 vrstic | `_update_entities()`, `_record_history()`, `_check_auto_pause()` |
| `entities.py` | `_flee` / `_move_towards` | skupna slide logika | `_slide_move()` pomožna |

**Pred (`ui.py __init__`):**
```python
def __init__(self, cfg):
    # fonti
    global FONT_TITLE, FONT_H2, ...
    pygame.font.init()
    FONT_TITLE = ...
    # površine
    self.sim_surface = ...
    # layout izračuni
    fh2 = FONT_H2.get_height()
    ...
    # gumbi
    self.btn_start = Button(...)
    # drsniki (17 drsnikov)
    self.fox_sliders = [...]
    ...  # 99 vrstic
```

**Po:**
```python
def __init__(self, cfg):
    self.cfg = cfg
    self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    self._init_fonts()
    self._init_surfaces()
    self._init_buttons()
    self._init_sliders()
    self._keys_down = set()

def _init_fonts(self):
    pygame.font.init()
    self.font_title = pygame.font.SysFont("segoeui", 16, bold=True)
    self.font_h2    = pygame.font.SysFont("segoeui", 14, bold=True)
    self.font_body  = pygame.font.SysFont("segoeui", 13)
    self.font_small = pygame.font.SysFont("segoeui", 12)
```

> **Pozor:** Globalni fonti (`FONT_TITLE`, ...) → instance spremenljivke (`self.font_title`, ...). Pomožne funkcije `_draw_hdr` in `_text` prejmejo font kot argument (kar `_draw_hdr` že dela).

---

### 9. Princip enojne odgovornosti (Single Responsibility Principle)

**Zakaj:** En razred, ena odgovornost. `_draw_bottom_panel` zdaj: riše ozadja, izračunava statistiko, riše drsniki, riše gumbe – to so 4 ločene odgovornosti.

**Pred:**
```python
def _draw_bottom_panel(self, sim):
    # riše 3 kartice ozadja
    # riše gumbe (start/pause/reset)
    # riše izbiro terena
    # IZRAČUNA povprečja lisic in zajcev  ← računanje in risanje mešano
    # riše povprečno statistiko
    # riše 14 drsnikov
    # ... 99 vrstic
```

**Po:**
```python
def _draw_bottom_panel(self, sim):
    """Nariše ozadja kartic, nato delegira vsak stolpec svoji metodi."""
    surf = self.screen
    pygame.draw.rect(surf, CARD_A, (0,      BOTTOM_Y, COL_W,           BOT_H))
    pygame.draw.rect(surf, CARD_C, (COL2_X, BOTTOM_Y, COL_W,           BOT_H))
    pygame.draw.rect(surf, CARD_A, (COL3_X, BOTTOM_Y, SCREEN_W-COL3_X, BOT_H))
    self._draw_col1_controls(surf, sim)
    self._draw_col1_live_stats(surf, sim)
    self._draw_col2_fox_sliders(surf, sim.running)
    self._draw_col3_rabbit_sliders(surf, sim.running)

def _calc_avg_stats(self, entities: list) -> dict:
    """Izračuna povprečne vrednosti lastnosti za seznam živali. Ločeno od risanja."""
    if not entities:
        return {}
    return {
        'age':    sum(e.age          for e in entities) / len(entities),
        'size':   sum(e.size         for e in entities) / len(entities),
        'hunger': sum(float(e.hunger) for e in entities) / len(entities) * 100,
        'thirst': sum(float(e.thirst) for e in entities) / len(entities) * 100,
        'speed':  sum(e.speed        for e in entities) / len(entities),
        'sense':  sum(e.sense_radius  for e in entities) / len(entities),
    }
```

> Prav tako: `Rabbit._find_partner` in `Fox._find_partner` sta skoraj identični metodi → premaknemo v skupni `Animal._find_partner(self, animals)` razred.

---

### 10. Samo smiselni komentarji + odstranitev mrtve kode

**Zakaj:** Trivialni komentarji dodajo šum. Mrtva koda zmede bralca – zakaj je sploh tu?

**Mrtva koda za odstranitev:**

| Datoteka | Kaj | Zakaj mrtvo |
|---|---|---|
| `entities.py` – `Clover.__init__` | `self.regen_timer = 0.0` | Nikoli ne prebrano/posodobljeno; komentar pravi "se ne obnavlja" |
| `terrain.py` | `def _scatter_type(self, ...)` | Definirana, a nikoli poklicana |
| `entities.py` – `Animal.__init__` | `self.dead = False` (vrstica 92) | Entity.__init__ ga že nastavi prek super() |

**Trivialni komentarji za odstranitev/izboljšavo:**
```python
# Pred – komentar samo ponovi kodo:
self.dead = False      # ali je mrtev
self.age  = 0.0        # starost

# Po – ohrani le komentarje ki razložijo ZAKAJ:
# Žeja narašča hitreje ko je žival lačna – dehidracija pospešuje lakoto
thirst_mult = 1.0 + 0.5 * (float(self.hunger) / self.max_hunger)
```

**Dodamo/ohranimo komentarje za neočitno logiko:**
```python
# terrain.py – _gen_lake
# Organična oblika jezera z superpozicijo sinusnih valov na polju razdalj
variation = (0.10 * math.sin(3 * angle)
             + 0.07 * math.cos(5 * angle)
             + 0.04 * math.sin(7 * angle - 1.1))
```

---

## Pregled sprememb

| # | Smernica | Datoteke | Obseg | Status |
|---|---|---|---|---|
| 1 | Smiselna imena | `entities.py`, `terrain.py`, `ui.py` | ~26 preimenovanj | ✅ |
| 2 | Konsistentno poimenovanje | `config.py` | Docstring razredu | ✅ |
| 3 | Self-documenting koda | `entities.py`, `main.py` | 8 magičnih števil → konstante | ✅ |
| 4 | Konsistentna oblika | vse | Enotni slovenski komentarji, trivialni odstranjeni | ✅ |
| 5 | En nivo zamika | `entities.py` | `_slide_move()` pomožna metoda | ✅ |
| 6 | Brez else | `entities.py`, `ui.py` | Guard clauses + default-first vzorec | ✅ |
| 7 | Enkapsulacija primitivov | `entities.py` | Nov razred `DriveLevel` | 📋 načrtovano |
| 8 | Dolžina metod | `ui.py`, `main.py` | Razdelitev 3 dolgih metod na 10 pomožnih | ✅ |
| 9 | Enojna odgovornost | `ui.py`, `main.py`, `entities.py` | Izvleček pomožnih metod; `_calc_avg_stats` | ✅ delno |
| 10 | Smiselni komentarji | vse | Trivialni komentarji odstranjeni + mrtva koda zbrisana | ✅ |

> **Opomba k smernici 7:** `DriveLevel` razred bi zahteval spremembo vsega koda ki dostopa do `hunger` in `thirst` (>30 mest). Sprememba je arhitekturno smiselna, a tvega vnos napak – zato ostaja kot načrtovana izboljšava.

> **Opomba k smernici 9:** `Rabbit._find_partner` in `Fox._find_partner` sta bili izvlečeni v `_calc_avg_stats` in ostale pomožne metode. Združitev `_find_partner` v skupni `Animal._find_partner` ni bila implementirana ker se logiki med vrstama rahlo razlikujeta (zajci iščejo v `rabbits`, lisice v `foxes`).

> **Delovanje simulacije se ni spremenilo** – vse spremembe so čisto strukturne.
