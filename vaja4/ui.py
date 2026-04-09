"""
ui.py – celoten uporabniški vmesnik

Razporeditev zaslona:
  +----------+---------------------------+
  |  PANEL   |                           |
  |  (320px) |   SIMULACIJA (960×720)   |
  |          |                           |
  +----------+---------------------------+

Panel (levo) vsebuje:
  - Naslov + stanje
  - Gumbi (Start, Pavza, Reset)
  - Izbira terena
  - Drsniki za parametre
  - Statistike
  - Graf populacije z osmi in mrežo
  - Namigi za upravljanje
"""

import pygame
import math
from config import Config

# ── barve ─────────────────────────────────────────────────────────────────
BG_DARK   = (18,  22,  30)
BG_MID    = (28,  34,  46)
BG_LIGHT  = (40,  50,  68)
GRID_COL  = (38,  48,  66)
ACCENT    = (80, 180, 120)
ACCENT2   = (220, 100,  40)
TEXT_MAIN = (220, 225, 235)
TEXT_DIM  = (120, 132, 155)
BTN_HOVER = (60, 140, 100)
BTN_NORM  = (38,  90,  65)
RED_COL   = (220,  70,  60)
BLUE_COL  = ( 60, 130, 220)
GREEN_COL = ( 80, 200,  80)

FONT_TITLE = None
FONT_BODY  = None
FONT_SMALL = None

PANEL_W = 320      # širina levega panela
SIM_X   = PANEL_W  # x-odmik simulacije na zaslonu
PX      = 10       # notranji levi odmik v panelu

# ── fiksni y-položaji elementov panela ────────────────────────────────────
_SY0      = 155    # y prvega drsnika (bar)
_STEP     = 44     # razmak med drsniki
_STAT_DIV = 452    # y razdelilne črte "Statistike"
_STAT_Y   = 468    # y prve vrstice statistike
_GRAPH_DIV= 548    # y razdelilne črte "Graf"
_GRAPH_Y  = 563    # y zgornjega roba grafa
_HINT_Y   = 750    # y namigov za kamero


# ══════════════════════════════════════════════════════════════════════════════
class Button:
    def __init__(self, x, y, w, h, label, color=BTN_NORM):
        self.rect   = pygame.Rect(x, y, w, h)
        self.label  = label
        self.color  = color
        self._hover = False

    def handle(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def draw(self, surf, font):
        col = BTN_HOVER if self._hover else self.color
        pygame.draw.rect(surf, col,    self.rect, border_radius=6)
        pygame.draw.rect(surf, ACCENT, self.rect, 1, border_radius=6)
        txt = font.render(self.label, True, TEXT_MAIN)
        surf.blit(txt, txt.get_rect(center=self.rect.center))


# ══════════════════════════════════════════════════════════════════════════════
class Slider:
    H = 12

    def __init__(self, x, y, w, label, vmin, vmax, value, integer=False):
        self.rect    = pygame.Rect(x, y, w, self.H)
        self.label   = label
        self.vmin    = vmin
        self.vmax    = vmax
        self.value   = value
        self.integer = integer
        self._drag   = False

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.inflate(0, 14).collidepoint(event.pos):
                self._drag = True
        if event.type == pygame.MOUSEBUTTONUP:
            self._drag = False
        if event.type == pygame.MOUSEMOTION and self._drag:
            t = (event.pos[0] - self.rect.x) / self.rect.w
            self.value = self.vmin + max(0.0, min(1.0, t)) * (self.vmax - self.vmin)
            if self.integer:
                self.value = int(round(self.value))

    def draw(self, surf, font):
        x, y, w = self.rect.x, self.rect.y, self.rect.w
        val_str  = str(int(self.value)) if self.integer else f"{self.value:.2f}"
        _text(surf, font, f"{self.label}: {val_str}", (x, y - 15), TEXT_MAIN)

        # Tirnica
        pygame.draw.rect(surf, BG_LIGHT, self.rect, border_radius=3)
        # Zapolnjeni del
        t  = (self.value - self.vmin) / max(1e-9, self.vmax - self.vmin)
        fw = int(t * w)
        if fw > 0:
            pygame.draw.rect(surf, ACCENT, (x, y, fw, self.H), border_radius=3)
        # Ročaj
        pygame.draw.circle(surf, TEXT_MAIN, (x + fw, y + self.H // 2), 6)


# ══════════════════════════════════════════════════════════════════════════════
class UI:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.screen = pygame.display.set_mode((cfg.SCREEN_W, cfg.SCREEN_H))

        global FONT_TITLE, FONT_BODY, FONT_SMALL
        pygame.font.init()
        FONT_TITLE = pygame.font.SysFont("segoeui", 15, bold=True)
        FONT_BODY  = pygame.font.SysFont("segoeui", 13)
        FONT_SMALL = pygame.font.SysFont("segoeui", 11)

        self.sim_surface = pygame.Surface((cfg.VIEW_W, cfg.VIEW_H))

        # ── gumbi ─────────────────────────────────────────────────────────
        sw = PANEL_W - PX * 2
        bw = (sw - 8) // 3
        self.btn_start = Button(PX,         52, bw, 28, "▶ Start")
        self.btn_pause = Button(PX+bw+4,    52, bw, 28, "⏸ Pavza")
        self.btn_reset = Button(PX+bw*2+8,  52, bw, 28, "↺ Reset", (70, 40, 40))

        # ── gumbi za teren ────────────────────────────────────────────────
        tw = (sw - 12) // 4
        self.terrain_btns = [
            Button(PX + i * (tw + 4), 90, tw, 24, lbl)
            for i, lbl in enumerate(["Reka", "Jezero", "Multi", "Perlin"])
        ]

        # ── drsniki ───────────────────────────────────────────────────────
        self.sliders = [
            Slider(PX, _SY0,          sw, "Lisice",     1,   30,  cfg.initial_foxes,   integer=True),
            Slider(PX, _SY0+_STEP,    sw, "Zajci",      5,   80,  cfg.initial_rabbits, integer=True),
            Slider(PX, _SY0+_STEP*2,  sw, "Detelje",   10,  150,  cfg.initial_clovers, integer=True),
            Slider(PX, _SY0+_STEP*3,  sw, "Hitrost L", 20,  120,  cfg.fox_speed),
            Slider(PX, _SY0+_STEP*4,  sw, "Hitrost Z", 20,  100,  cfg.rabbit_speed),
            Slider(PX, _SY0+_STEP*5,  sw, "Mutacija",  0.0, 0.5,  cfg.mutation_chance),
            Slider(PX, _SY0+_STEP*6,  sw, "Sim čas",   0.2, 5.0,  cfg.sim_speed),
        ]

        # ── graf ──────────────────────────────────────────────────────────
        self.graph_rect = pygame.Rect(PX, _GRAPH_Y, sw, _HINT_Y - _GRAPH_Y - 4)

        self._keys_down = set()

    # ══════════════════════════════════════════════════════════════════════
    def handle_event(self, event, sim):
        cfg = self.cfg

        if event.type == pygame.KEYDOWN: self._keys_down.add(event.key)
        if event.type == pygame.KEYUP:   self._keys_down.discard(event.key)

        if self.btn_start.handle(event):
            if not sim.running:
                self._apply_sliders(sim)
                sim.start()
            else:
                sim.paused = False

        if self.btn_pause.handle(event):
            sim.paused = not sim.paused

        if self.btn_reset.handle(event):
            sim.running = False
            sim.paused  = False

        for i, btn in enumerate(self.terrain_btns):
            if btn.handle(event):
                cfg.terrain_type = i + 1
                if sim.running and sim.terrain:
                    sim.terrain.rebake()

        for sl in self.sliders:
            sl.handle(event)
        self._sync_sliders(cfg)

    def _apply_sliders(self, sim):
        cfg, s = self.cfg, self.sliders
        cfg.initial_foxes   = int(s[0].value)
        cfg.initial_rabbits = int(s[1].value)
        cfg.initial_clovers = int(s[2].value)
        cfg.fox_speed       = s[3].value
        cfg.rabbit_speed    = s[4].value
        cfg.mutation_chance = s[5].value
        cfg.sim_speed       = s[6].value

    def _sync_sliders(self, cfg):
        cfg.sim_speed       = self.sliders[6].value
        cfg.mutation_chance = self.sliders[5].value

    # ══════════════════════════════════════════════════════════════════════
    def draw(self, sim):
        screen, cfg = self.screen, self.cfg
        self._update_camera(sim)
        screen.fill(BG_DARK)

        # ── simulacijska površina (desno) ─────────────────────────────────
        ss = self.sim_surface
        ss.fill((20, 28, 38))
        if sim.terrain:
            ss.blit(sim.terrain.surface, (-cfg.cam_x, -cfg.cam_y))
            for cl in sim.clovers: cl.draw(ss, cfg.cam_x, cfg.cam_y)
            for rb in sim.rabbits: rb.draw(ss, cfg.cam_x, cfg.cam_y)
            for fx in sim.foxes:   fx.draw(ss, cfg.cam_x, cfg.cam_y)
        pygame.draw.rect(ss, ACCENT, (0, 0, cfg.VIEW_W, cfg.VIEW_H), 1)
        screen.blit(ss, (SIM_X, 0))

        # ── panel (levo) ──────────────────────────────────────────────────
        panel = pygame.Surface((PANEL_W, cfg.SCREEN_H))
        panel.fill(BG_MID)
        self._draw_panel(panel, sim)
        screen.blit(panel, (0, 0))

        # Ločilna črta med panelom in simulacijo
        pygame.draw.line(screen, ACCENT, (PANEL_W, 0), (PANEL_W, cfg.SCREEN_H), 1)

    # ──────────────────────────────────────────────────────────────────────
    def _draw_panel(self, surf, sim):
        cfg = self.cfg

        # ── naslov ────────────────────────────────────────────────────────
        _text(surf, FONT_TITLE, "EKOSISTEM  SIMULACIJA", (PX, 10), ACCENT)

        # ── stanje ────────────────────────────────────────────────────────
        if not sim.running:
            status, scol = "● Ustavljena", RED_COL
        elif sim.paused:
            status, scol = "⏸ Pavza", ACCENT2
        else:
            status, scol = f"▶  korak: {sim.tick}", ACCENT
        _text(surf, FONT_SMALL, status, (PX, 30), scol)

        # ── gumbi ─────────────────────────────────────────────────────────
        for btn in (self.btn_start, self.btn_pause, self.btn_reset):
            btn.draw(surf, FONT_BODY)

        # ── teren ─────────────────────────────────────────────────────────
        _text(surf, FONT_SMALL, "Teren:", (PX, 82), TEXT_DIM)
        for btn in self.terrain_btns:
            btn.draw(surf, FONT_SMALL)
        # Označi aktiven teren
        active_r = self.terrain_btns[cfg.terrain_type - 1].rect
        pygame.draw.rect(surf, ACCENT, active_r, 2, border_radius=6)

        # ── drsniki ───────────────────────────────────────────────────────
        _div(surf, 124, "Začetne nastavitve")
        for sl in self.sliders:
            sl.draw(surf, FONT_SMALL)

        # ── statistike ────────────────────────────────────────────────────
        _div(surf, _STAT_DIV, "Statistike")
        n_fox    = len(sim.foxes)   if sim.running else 0
        n_rabbit = len(sim.rabbits) if sim.running else 0
        n_clover = len(sim.clovers) if sim.running else 0
        _text(surf, FONT_BODY, f"Lisice:   {n_fox}",    (PX,    _STAT_Y),      ACCENT2)
        _text(surf, FONT_BODY, f"Zajci:    {n_rabbit}", (PX,    _STAT_Y + 18), (130, 200, 130))
        _text(surf, FONT_BODY, f"Detelje:  {n_clover}", (PX,    _STAT_Y + 36), GREEN_COL)
        _text(surf, FONT_BODY, f"Čas:      {sim.elapsed:.0f} s",
                                                         (PX,    _STAT_Y + 54), TEXT_DIM)

        # ── graf ──────────────────────────────────────────────────────────
        _div(surf, _GRAPH_DIV, "Graf populacije")
        self._draw_graph(surf, self.graph_rect, sim)

        # ── namigi za kamero ──────────────────────────────────────────────
        _text(surf, FONT_SMALL, "WASD / ↑↓←→  pomik kamere", (PX, _HINT_Y),      TEXT_DIM)
        _text(surf, FONT_SMALL, "ESC  izhod",                 (PX, _HINT_Y + 14), TEXT_DIM)

    # ──────────────────────────────────────────────────────────────────────
    def _draw_graph(self, surf, rect, sim):
        """Linijski graf populacij z osmi, mrežo in oznakami."""
        # Margins znotraj rect: levo za Y-oznake, spodaj za X-oznake
        mx, mt, mb, mr = 32, 4, 18, 4

        # Ozadje
        pygame.draw.rect(surf, BG_DARK,  rect, border_radius=4)
        pygame.draw.rect(surf, BG_LIGHT, rect, 1, border_radius=4)

        # Koordinate risalnega področja (znotraj rect)
        px0 = rect.x + mx
        py0 = rect.y + mt
        pw  = rect.w - mx - mr
        ph  = rect.h - mt - mb

        # Osi
        pygame.draw.line(surf, TEXT_DIM, (px0, py0),      (px0,      py0 + ph), 1)  # Y
        pygame.draw.line(surf, TEXT_DIM, (px0, py0 + ph), (px0 + pw, py0 + ph), 1)  # X

        if not sim.running:
            self._draw_y_ticks(surf, px0, py0, pw, ph, 100, rect)
            return

        series = [
            (sim.history_fox,    ACCENT2,   "Lis"),
            (sim.history_rabbit, GREEN_COL, "Zaj"),
            (sim.history_clover, BLUE_COL,  "Det"),
        ]

        all_vals = [v for s, _, _ in series for v in s]
        if not all_vals:
            self._draw_y_ticks(surf, px0, py0, pw, ph, 100, rect)
            return

        # Zaokrožena lestvica za Y os
        max_v = max(all_vals) or 1
        if max_v >= 10:
            mag      = 10 ** math.floor(math.log10(max_v))
            max_nice = math.ceil(max_v / mag) * mag
        else:
            max_nice = max(10, math.ceil(max_v / 5) * 5)

        # ── Y os: mreža in oznake ──────────────────────────────────────────
        self._draw_y_ticks(surf, px0, py0, pw, ph, max_nice, rect)

        # ── X os: mreža in oznake ─────────────────────────────────────────
        n_data = max((len(s) for s, _, _ in series if s), default=0)
        if n_data > 1:
            n_xticks = min(4, n_data - 1)
            for i in range(n_xticks + 1):
                idx = int(i / n_xticks * (n_data - 1))
                gx  = px0 + int(idx / (n_data - 1) * pw)
                pygame.draw.line(surf, GRID_COL, (gx, py0), (gx, py0 + ph), 1)
                lbl = FONT_SMALL.render(str(idx * 30), True, TEXT_DIM)
                surf.blit(lbl, (gx - lbl.get_width() // 2, py0 + ph + 3))

        # ── Linije podatkov ───────────────────────────────────────────────
        for data, color, _ in series:
            if len(data) < 2:
                continue
            n   = len(data)
            pts = []
            for i, v in enumerate(data):
                gx = px0 + int(i / (n - 1) * pw)
                gy = py0 + ph - int(v / max_nice * ph)
                pts.append((gx, max(py0, min(py0 + ph, gy))))
            pygame.draw.lines(surf, color, False, pts, 2)

        # ── Legenda (zgoraj desno) ─────────────────────────────────────────
        lx = px0 + pw - 140
        for _, color, name in series:
            pygame.draw.line(surf, color, (lx, py0 + 9), (lx + 14, py0 + 9), 2)
            _text(surf, FONT_SMALL, name, (lx + 17, py0 + 3), color)
            lx += 48

    def _draw_y_ticks(self, surf, px0, py0, pw, ph, max_nice, rect):
        """Nariše Y mrežo in oznake."""
        n_yticks = 5
        for i in range(n_yticks):
            val = int(i * max_nice / (n_yticks - 1))
            gy  = py0 + ph - int(i / (n_yticks - 1) * ph)
            pygame.draw.line(surf, GRID_COL, (px0, gy), (px0 + pw, gy), 1)
            lbl = FONT_SMALL.render(str(val), True, TEXT_DIM)
            surf.blit(lbl, (rect.x + 1, gy - lbl.get_height() // 2))

    # ──────────────────────────────────────────────────────────────────────
    def _update_camera(self, sim):
        if not sim.running:
            return
        cfg   = self.cfg
        speed = cfg.cam_speed / cfg.FPS
        keys  = self._keys_down
        if pygame.K_a in keys or pygame.K_LEFT  in keys: cfg.cam_x = max(0, cfg.cam_x - speed)
        if pygame.K_d in keys or pygame.K_RIGHT in keys: cfg.cam_x = min(cfg.MAP_W - cfg.VIEW_W, cfg.cam_x + speed)
        if pygame.K_w in keys or pygame.K_UP    in keys: cfg.cam_y = max(0, cfg.cam_y - speed)
        if pygame.K_s in keys or pygame.K_DOWN  in keys: cfg.cam_y = min(cfg.MAP_H - cfg.VIEW_H, cfg.cam_y + speed)


# ══════════════════════════════════════════════════════════════════════════════
# Pomožne funkcije
# ══════════════════════════════════════════════════════════════════════════════

def _text(surf, font, txt, pos, color=TEXT_MAIN):
    surf.blit(font.render(txt, True, color), pos)


def _div(surf, y, label):
    """Razdelilna črta z oznako sekcije."""
    sw = PANEL_W - PX * 2
    pygame.draw.line(surf, BG_LIGHT, (PX, y + 6), (PX + sw, y + 6), 1)
    lbl = FONT_SMALL.render(f" {label} ", True, TEXT_DIM)
    surf.blit(lbl, (PX + 8, y))