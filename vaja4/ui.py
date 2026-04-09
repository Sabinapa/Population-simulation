"""
ui.py – celoten uporabniški vmesnik (baby-blue tema)

Razporeditev zaslona (1280 × 780):

  +------SIM_W=760------+------RIGHT_W=520------+
  |                     |        GRAF            | ← h=GRAPH_H=216
  |   SIMULACIJA        +------------------------+
  |   (760 × 432)       |     STATISTIKA         | ← h=STATS_H=216
  +---------------------+------------------------+ ← y=432
  |         DRSNIK HITROST SIMULACIJE            | ← h=30
  +-COL_W=426-+-COL_W=427-+-COL_W=427-----------+ ← y=462
  | NASTAVITVE | LISICA    | ZAJEC               | ← h=290
  +------------+-----------+---------------------+ ← y=752
  |              DRSNIK MUTACIJA                 | ← h=28
  +---------------------------------------------+ ← y=780
"""

import pygame
import math
from config import Config

# ── barve (baby-blue tema) ─────────────────────────────────────────────────
BG_DARK    = ( 10,  16,  26)
BG_MID     = ( 18,  27,  44)
BG_LIGHT   = ( 28,  42,  68)
GRID_COL   = ( 32,  50,  80)
ACCENT     = ( 95, 190, 240)    # baby blue
ACCENT2    = (235, 125,  45)    # oranžna
TEXT_MAIN  = (210, 232, 250)
TEXT_DIM   = (108, 140, 170)
BTN_HOVER  = ( 55, 145, 200)
BTN_NORM   = ( 28,  75, 130)
BTN_RED    = ( 90,  30,  30)
BTN_GREEN  = ( 28,  85,  40)
BTN_GREY   = ( 55,  60,  70)
RED_COL    = (225,  80,  65)
GREEN_COL  = ( 70, 215,  90)

# Graf barve (zajec=bela, lisica=rdeča, detelje=zelena – po sliki)
GRAPH_FOX    = (210,  60,  60)
GRAPH_RABBIT = (230, 230, 230)
GRAPH_CLOVER = ( 60, 210,  60)

FONT_TITLE = None
FONT_BODY  = None
FONT_SMALL = None

# ── dimenzije zaslona ─────────────────────────────────────────────────────
SCREEN_W = 1280
SCREEN_H = 780

SIM_W    = 760     # mora biti = cfg.VIEW_W
SIM_H    = 432     # mora biti = cfg.VIEW_H
RIGHT_X  = SIM_W
RIGHT_W  = SCREEN_W - SIM_W   # 520
GRAPH_H  = SIM_H // 2          # 216
STATS_H  = SIM_H - GRAPH_H     # 216

SPEED_Y  = SIM_H               # 432
SPEED_H  = 30

BOTTOM_Y = SPEED_Y + SPEED_H   # 462
BOTTOM_H = 290

MUT_Y    = BOTTOM_Y + BOTTOM_H # 752
MUT_H    = SCREEN_H - MUT_Y    # 28

COL1_X   = 0
COL2_X   = SCREEN_W // 3       # 426
COL3_X   = 2 * SCREEN_W // 3   # 853
COL_W    = SCREEN_W // 3        # 426

PX = 10   # horizontalni odmik
PY =  8   # vertikalni odmik

# Pozicije drsnikov v spodnjem panelu
_HDR_H   = 18             # višina naslova stolpca
_BPY0    = BOTTOM_Y + PY + _HDR_H + 16   # y prvega drsnika (rect) = 504
_BSTEP   = 39             # korak med drsniki


# ══════════════════════════════════════════════════════════════════════════════
class Button:
    def __init__(self, x, y, w, h, label, color=None):
        self.rect   = pygame.Rect(x, y, w, h)
        self.label  = label
        self.color  = color if color is not None else BTN_NORM
        self._hover = False

    def handle(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def draw(self, surf, font):
        col = BTN_HOVER if self._hover else self.color
        pygame.draw.rect(surf, col,    self.rect, border_radius=5)
        pygame.draw.rect(surf, ACCENT, self.rect, 1, border_radius=5)
        txt = font.render(self.label, True, TEXT_MAIN)
        surf.blit(txt, txt.get_rect(center=self.rect.center))


# ══════════════════════════════════════════════════════════════════════════════
class Slider:
    H = 12

    def __init__(self, x, y, w, label, vmin, vmax, value,
                 integer=False, locked=False):
        self.rect    = pygame.Rect(x, y, w, self.H)
        self.label   = label
        self.vmin    = vmin
        self.vmax    = vmax
        self.value   = value
        self.integer = integer
        self.locked  = locked   # zaklenjeno med delovanjem simulacije
        self._drag   = False

    def handle(self, event, sim_running=False):
        if self.locked and sim_running:
            self._drag = False
            return
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

    def draw(self, surf, font, sim_running=False):
        x, y, w  = self.rect.x, self.rect.y, self.rect.w
        disabled = self.locked and sim_running
        t_col    = TEXT_DIM if disabled else TEXT_MAIN
        trk_col  = (16, 24, 36) if disabled else BG_LIGHT
        fil_col  = (45, 68, 95) if disabled else ACCENT
        hdl_col  = TEXT_DIM    if disabled else TEXT_MAIN

        val_str  = str(int(self.value)) if self.integer else f"{self.value:.2f}"
        _text(surf, font, f"{self.label}: {val_str}", (x, y - 14), t_col)

        pygame.draw.rect(surf, trk_col, self.rect, border_radius=3)
        t  = (self.value - self.vmin) / max(1e-9, self.vmax - self.vmin)
        fw = int(t * w)
        if fw > 0:
            pygame.draw.rect(surf, fil_col, (x, y, fw, self.H), border_radius=3)
        pygame.draw.circle(surf, hdl_col, (x + fw, y + self.H // 2), 6)


# ══════════════════════════════════════════════════════════════════════════════
class UI:
    def __init__(self, cfg: Config):
        self.cfg    = cfg
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

        global FONT_TITLE, FONT_BODY, FONT_SMALL
        pygame.font.init()
        FONT_TITLE = pygame.font.SysFont("segoeui", 13, bold=True)
        FONT_BODY  = pygame.font.SysFont("segoeui", 12)
        FONT_SMALL = pygame.font.SysFont("segoeui", 11)

        # Simulacijska površina in overlay za obroče zaznavanja
        self.sim_surface    = pygame.Surface((SIM_W, SIM_H))
        self._sense_overlay = pygame.Surface((SIM_W, SIM_H), pygame.SRCALPHA)

        sw_nav = COL_W - PX * 2   # širina vsebine v NASTAVITVE stolpcu

        # ── NASTAVITVE gumbi ──────────────────────────────────────────────
        bw = (sw_nav - 8) // 3
        y_btn = BOTTOM_Y + PY + _HDR_H + 2
        self.btn_start = Button(COL1_X+PX,         y_btn, bw, 25, "▶ Start")
        self.btn_pause = Button(COL1_X+PX+bw+4,    y_btn, bw, 25, "⏸ Pavza")
        self.btn_reset = Button(COL1_X+PX+bw*2+8,  y_btn, bw, 25, "↺ Reset", BTN_RED)

        tw = (sw_nav - 12) // 4
        y_ter = y_btn + 31
        self.terrain_btns = [
            Button(COL1_X+PX + i*(tw+4), y_ter, tw, 21, lbl)
            for i, lbl in enumerate(["Reka", "Jezero", "Delta", "Dolina"])
        ]

        self.btn_visual = Button(COL1_X+PX, y_ter+27, sw_nav, 21,
                                 "Vizualizacija: VKLOPLJENA", BTN_GREEN)

        # ── Drsnik hitrosti (polna širina, med sim in spodnjim panelom) ───
        self.slider_speed = Slider(
            PX, SPEED_Y + 9, SCREEN_W - PX*2,
            "Hitrost simulacije", 0.2, 5.0, cfg.sim_speed)

        # ── Drsnik mutacije (polna širina, spodaj) ────────────────────────
        self.slider_mutation = Slider(
            PX, MUT_Y + 8, SCREEN_W - PX*2,
            "Mutacija", 0.0, 0.5, cfg.mutation_chance)

        # ── Drsniki lisice (stolpec 2) ────────────────────────────────────
        self.fox_sliders = [
            Slider(COL2_X+PX, _BPY0 + i*_BSTEP, COL_W-PX*2,
                   lbl, mn, mx, val, integer=intg, locked=True)
            for i, (lbl, mn, mx, val, intg) in enumerate([
                ("Število",     1,   30,  cfg.initial_foxes,    True),
                ("Hitrost",    20,  130,  cfg.fox_speed,         False),
                ("Velikost",    4,   22,  cfg.fox_size,          True),
                ("Zaznava",    30,  200,  cfg.fox_sense_radius,  False),
                ("Čas lakote", 30,  300,  cfg.fox_max_hunger,    False),
                ("Čas žeje",   20,  200,  cfg.fox_max_thirst,    False),
                ("Prag razm.", 0.3, 0.9,  cfg.fox_repro_drive,   False),
            ])
        ]

        # ── Drsniki zajca (stolpec 3) ─────────────────────────────────────
        self.rabbit_sliders = [
            Slider(COL3_X+PX, _BPY0 + i*_BSTEP, COL_W-PX*2,
                   lbl, mn, mx, val, integer=intg, locked=True)
            for i, (lbl, mn, mx, val, intg) in enumerate([
                ("Število",     5,   80,  cfg.initial_rabbits,    True),
                ("Hitrost",    20,  120,  cfg.rabbit_speed,        False),
                ("Velikost",    3,   18,  cfg.rabbit_size,         True),
                ("Zaznava",    20,  150,  cfg.rabbit_sense_radius, False),
                ("Čas lakote", 20,  200,  cfg.rabbit_max_hunger,   False),
                ("Čas žeje",   15,  150,  cfg.rabbit_max_thirst,   False),
                ("Prag razm.", 0.3, 0.9,  cfg.rabbit_repro_drive,  False),
            ])
        ]

        self._keys_down = set()

    # ══════════════════════════════════════════════════════════════════════
    def handle_event(self, event, sim):
        cfg = self.cfg

        if event.type == pygame.KEYDOWN: self._keys_down.add(event.key)
        if event.type == pygame.KEYUP:   self._keys_down.discard(event.key)

        if self.btn_start.handle(event):
            if not sim.running:
                self._apply_sliders_to_cfg()
                sim.start()
            else:
                sim.paused = False

        if self.btn_pause.handle(event):
            sim.paused = not sim.paused

        if self.btn_reset.handle(event):
            sim.running = False
            sim.paused  = False

        if self.btn_visual.handle(event):
            sim.show_visual = not sim.show_visual
            if sim.show_visual:
                self.btn_visual.label = "Vizualizacija: VKLOPLJENA"
                self.btn_visual.color = BTN_GREEN
            else:
                self.btn_visual.label = "Vizualizacija: IZKLOPLJENA"
                self.btn_visual.color = BTN_GREY

        for i, btn in enumerate(self.terrain_btns):
            if btn.handle(event):
                cfg.terrain_type = i + 1
                if sim.running and sim.terrain:
                    sim.terrain.rebake()

        running = sim.running
        self.slider_speed.handle(event)
        self.slider_mutation.handle(event)
        for sl in self.fox_sliders:    sl.handle(event, sim_running=running)
        for sl in self.rabbit_sliders: sl.handle(event, sim_running=running)

        cfg.sim_speed       = self.slider_speed.value
        cfg.mutation_chance = self.slider_mutation.value

    def _apply_sliders_to_cfg(self):
        cfg = self.cfg
        fs  = self.fox_sliders
        rs  = self.rabbit_sliders

        cfg.initial_foxes       = int(fs[0].value)
        cfg.fox_speed           = fs[1].value
        cfg.fox_size            = int(fs[2].value)
        cfg.fox_sense_radius    = fs[3].value
        cfg.fox_max_hunger      = fs[4].value
        cfg.fox_max_thirst      = fs[5].value
        cfg.fox_repro_drive     = fs[6].value

        cfg.initial_rabbits     = int(rs[0].value)
        cfg.rabbit_speed        = rs[1].value
        cfg.rabbit_size         = int(rs[2].value)
        cfg.rabbit_sense_radius = rs[3].value
        cfg.rabbit_max_hunger   = rs[4].value
        cfg.rabbit_max_thirst   = rs[5].value
        cfg.rabbit_repro_drive  = rs[6].value

        cfg.sim_speed       = self.slider_speed.value
        cfg.mutation_chance = self.slider_mutation.value

    # ══════════════════════════════════════════════════════════════════════
    def draw(self, sim):
        self.screen.fill(BG_DARK)
        self._update_camera(sim)

        self._draw_sim(sim)
        self._draw_graph_panel(sim)
        self._draw_stats_panel(sim)
        self._draw_speed_bar()
        self._draw_bottom_panel(sim)
        self._draw_mutation_bar()

        # Razdelilne črte
        scr = self.screen
        pygame.draw.line(scr, BG_LIGHT, (RIGHT_X, 0),       (RIGHT_X, SIM_H),  1)
        pygame.draw.line(scr, BG_LIGHT, (RIGHT_X, GRAPH_H), (SCREEN_W, GRAPH_H), 1)
        pygame.draw.line(scr, BG_LIGHT, (0, SPEED_Y),       (SCREEN_W, SPEED_Y), 1)
        pygame.draw.line(scr, BG_LIGHT, (0, BOTTOM_Y),      (SCREEN_W, BOTTOM_Y), 1)
        pygame.draw.line(scr, BG_LIGHT, (COL2_X, BOTTOM_Y), (COL2_X, MUT_Y),   1)
        pygame.draw.line(scr, BG_LIGHT, (COL3_X, BOTTOM_Y), (COL3_X, MUT_Y),   1)
        pygame.draw.line(scr, BG_LIGHT, (0, MUT_Y),         (SCREEN_W, MUT_Y), 1)

    # ── simulacijska površina ─────────────────────────────────────────────
    def _draw_sim(self, sim):
        cfg = self.cfg
        ss  = self.sim_surface
        ss.fill((12, 18, 30))

        if sim.terrain:
            ss.blit(sim.terrain.surface, (-cfg.cam_x, -cfg.cam_y))

            if sim.running and sim.show_visual:
                for cl in sim.clovers:
                    cl.draw(ss, cfg.cam_x, cfg.cam_y)

                # Obroči zaznavanja (SRCALPHA overlay, ena površina na sličico)
                self._sense_overlay.fill((0, 0, 0, 0))
                for rb in sim.rabbits:
                    sx, sy = int(rb.x - cfg.cam_x), int(rb.y - cfg.cam_y)
                    r = int(rb.sense_radius)
                    if -r < sx < SIM_W + r and -r < sy < SIM_H + r:
                        pygame.draw.circle(self._sense_overlay,
                                           (200, 200, 150, 38), (sx, sy), r, 1)
                for fx in sim.foxes:
                    sx, sy = int(fx.x - cfg.cam_x), int(fx.y - cfg.cam_y)
                    r = int(fx.sense_radius)
                    if -r < sx < SIM_W + r and -r < sy < SIM_H + r:
                        pygame.draw.circle(self._sense_overlay,
                                           (255, 150, 50, 38), (sx, sy), r, 1)
                ss.blit(self._sense_overlay, (0, 0))

                for rb in sim.rabbits: rb.draw(ss, cfg.cam_x, cfg.cam_y)
                for fx in sim.foxes:   fx.draw(ss, cfg.cam_x, cfg.cam_y)

            elif sim.running and not sim.show_visual:
                f1 = pygame.font.SysFont("segoeui", 17, bold=True)
                f2 = pygame.font.SysFont("segoeui", 12)
                m1 = f1.render("Vizualizacija izklopljena", True, ACCENT)
                m2 = f2.render("Simulacija poteka v ozadju  –  grafi se posodabljajo",
                               True, TEXT_DIM)
                ss.blit(m1, (SIM_W//2 - m1.get_width()//2, SIM_H//2 - 18))
                ss.blit(m2, (SIM_W//2 - m2.get_width()//2, SIM_H//2 + 8))

        # Obroba simulacije
        pygame.draw.rect(ss, ACCENT, (0, 0, SIM_W, SIM_H), 1)
        self.screen.blit(ss, (0, 0))

    # ── graf (desno zgoraj) ───────────────────────────────────────────────
    def _draw_graph_panel(self, sim):
        surf = self.screen
        pygame.draw.rect(surf, BG_MID, (RIGHT_X, 0, RIGHT_W, GRAPH_H))

        _text(surf, FONT_TITLE, "Graf populacije",
              (RIGHT_X + PX, PY), ACCENT)

        # Margins znotraj grafa
        mx, mt, mb, mr = 36, 22, 18, 8
        px0 = RIGHT_X + mx
        py0 = mt
        pw  = RIGHT_W - mx - mr
        ph  = GRAPH_H - mt - mb

        # Osi
        pygame.draw.line(surf, TEXT_DIM, (px0, py0),    (px0,    py0+ph), 1)
        pygame.draw.line(surf, TEXT_DIM, (px0, py0+ph), (px0+pw, py0+ph), 1)

        if not sim.running:
            self._draw_y_ticks(surf, px0, py0, pw, ph, 100)
            return

        series = [
            (sim.history_fox,    GRAPH_FOX,    "Lisice"),
            (sim.history_rabbit, GRAPH_RABBIT, "Zajci"),
            (sim.history_clover, GRAPH_CLOVER, "Detelje"),
        ]
        all_vals = [v for s, _, _ in series for v in s]
        if not all_vals:
            self._draw_y_ticks(surf, px0, py0, pw, ph, 100)
            return

        max_v = max(all_vals) or 1
        if max_v >= 10:
            mag      = 10 ** math.floor(math.log10(max_v))
            max_nice = math.ceil(max_v / mag) * mag
        else:
            max_nice = max(10, math.ceil(max_v / 5) * 5)

        self._draw_y_ticks(surf, px0, py0, pw, ph, max_nice)

        n_data = max((len(s) for s, _, _ in series if s), default=0)
        if n_data > 1:
            n_xt = min(5, n_data - 1)
            for i in range(n_xt + 1):
                idx = int(i / n_xt * (n_data - 1))
                gx  = px0 + int(idx / (n_data - 1) * pw)
                pygame.draw.line(surf, GRID_COL, (gx, py0), (gx, py0+ph), 1)
                lbl = FONT_SMALL.render(str(idx * 30), True, TEXT_DIM)
                surf.blit(lbl, (gx - lbl.get_width()//2, py0+ph+3))

        for data, color, _ in series:
            if len(data) < 2:
                continue
            n   = len(data)
            pts = [(px0 + int(i/(n-1)*pw),
                    max(py0, min(py0+ph, py0+ph - int(v/max_nice*ph))))
                   for i, v in enumerate(data)]
            pygame.draw.lines(surf, color, False, pts, 2)

        # Oznaka x-osi
        _text(surf, FONT_SMALL, "čas (koraki)",
              (px0 + pw//2 - 24, py0+ph+3), TEXT_DIM)

        # Legenda barv
        lx = px0 + 2
        for _, color, name in series:
            pygame.draw.line(surf, color, (lx, py0+10), (lx+12, py0+10), 2)
            _text(surf, FONT_SMALL, name, (lx+15, py0+4), color)
            lx += 68

    def _draw_y_ticks(self, surf, px0, py0, pw, ph, max_nice):
        n_yticks = 5
        for i in range(n_yticks):
            val = int(i * max_nice / (n_yticks - 1))
            gy  = py0 + ph - int(i / (n_yticks - 1) * ph)
            pygame.draw.line(surf, GRID_COL, (px0, gy), (px0+pw, gy), 1)
            lbl = FONT_SMALL.render(str(val), True, TEXT_DIM)
            surf.blit(lbl, (px0 - lbl.get_width() - 3, gy - lbl.get_height()//2))

    # ── statistika (desno spodaj) ─────────────────────────────────────────
    def _draw_stats_panel(self, sim):
        surf = self.screen
        pygame.draw.rect(surf, BG_MID, (RIGHT_X, GRAPH_H, RIGHT_W, STATS_H))

        _text(surf, FONT_TITLE, "Statistika",
              (RIGHT_X + PX, GRAPH_H + PY), ACCENT)

        y  = GRAPH_H + PY + 20
        dy = 20

        n_fox    = len(sim.foxes)   if sim.running else 0
        n_rabbit = len(sim.rabbits) if sim.running else 0
        n_clover = len(sim.clovers) if sim.running else 0
        step     = sim.tick         if sim.running else 0
        elapsed  = sim.elapsed      if sim.running else 0.0

        _text(surf, FONT_BODY, f"Lisice:   {n_fox}",    (RIGHT_X+PX, y),       GRAPH_FOX)
        _text(surf, FONT_BODY, f"Zajci:    {n_rabbit}", (RIGHT_X+PX, y+dy),    GRAPH_RABBIT)
        _text(surf, FONT_BODY, f"Detelje:  {n_clover}", (RIGHT_X+PX, y+dy*2),  GRAPH_CLOVER)
        _text(surf, FONT_BODY, f"Korak:    {step}",     (RIGHT_X+PX, y+dy*3),  TEXT_DIM)
        _text(surf, FONT_BODY, f"Čas:      {elapsed:.0f} s",
                                                         (RIGHT_X+PX, y+dy*4), TEXT_DIM)

        # Status simulacije
        if not sim.running:
            st, sc = "● Ustavljena", RED_COL
        elif sim.paused:
            st, sc = "⏸ Pavza", ACCENT2
        else:
            vis_tag = "" if sim.show_visual else "  [brez vizualizacije]"
            st, sc  = f"▶ Teče{vis_tag}", ACCENT
        _text(surf, FONT_BODY, st, (RIGHT_X+PX, y+dy*5), sc)

        # Trend populacije zajcev
        if sim.running:
            tt, tc = _population_trend(sim.history_rabbit)
            if tt:
                _text(surf, FONT_BODY, f"Trend:    {tt}",
                      (RIGHT_X+PX, y+dy*6), tc)

    # ── pas hitrosti simulacije (polna širina) ────────────────────────────
    def _draw_speed_bar(self):
        surf = self.screen
        pygame.draw.rect(surf, BG_MID, (0, SPEED_Y, SCREEN_W, SPEED_H))
        self.slider_speed.draw(surf, FONT_SMALL)

    # ── spodnji 3-stolpčni panel ──────────────────────────────────────────
    def _draw_bottom_panel(self, sim):
        surf    = self.screen
        running = sim.running

        # Ozadja stolpcev
        pygame.draw.rect(surf, BG_MID,  (0,      BOTTOM_Y, COL_W,           BOTTOM_H))
        pygame.draw.rect(surf, BG_DARK, (COL2_X, BOTTOM_Y, COL_W,           BOTTOM_H))
        pygame.draw.rect(surf, BG_MID,  (COL3_X, BOTTOM_Y, SCREEN_W-COL3_X, BOTTOM_H))

        # ── Stolpec 1: NASTAVITVE ──────────────────────────────────────────
        _text(surf, FONT_SMALL, "NASTAVITVE",
              (COL1_X+PX, BOTTOM_Y+PY), TEXT_DIM)
        _text(surf, FONT_TITLE, "EKOSISTEM SIMULACIJA",
              (COL1_X+PX, BOTTOM_Y+PY+13), ACCENT)

        for btn in (self.btn_start, self.btn_pause, self.btn_reset):
            btn.draw(surf, FONT_BODY)

        _text(surf, FONT_SMALL, "Teren:", (COL1_X+PX, BOTTOM_Y+PY+_HDR_H+28), TEXT_DIM)
        for btn in self.terrain_btns:
            btn.draw(surf, FONT_SMALL)
        active_r = self.terrain_btns[self.cfg.terrain_type - 1].rect
        pygame.draw.rect(surf, ACCENT, active_r, 2, border_radius=5)

        self.btn_visual.draw(surf, FONT_SMALL)

        # Namigi
        hint_y = self.btn_visual.rect.bottom + 12
        _text(surf, FONT_SMALL, "WASD / ↑↓←→  pomik kamere",
              (COL1_X+PX, hint_y), TEXT_DIM)
        _text(surf, FONT_SMALL, "ESC  izhod",
              (COL1_X+PX, hint_y + 13), TEXT_DIM)

        # ── Stolpec 2: Lastnosti lisice ────────────────────────────────────
        _text(surf, FONT_TITLE, "Lastnosti lisice (plenilec)",
              (COL2_X+PX, BOTTOM_Y+PY), GRAPH_FOX)
        if running:
            _text(surf, FONT_SMALL, "omejeno med izvajanjem",
                  (COL2_X+PX, BOTTOM_Y+PY+14), TEXT_DIM)
        for sl in self.fox_sliders:
            sl.draw(surf, FONT_SMALL, sim_running=running)

        # ── Stolpec 3: Lastnosti zajca ─────────────────────────────────────
        _text(surf, FONT_TITLE, "Lastnosti zajca (plen)",
              (COL3_X+PX, BOTTOM_Y+PY), GRAPH_RABBIT)
        if running:
            _text(surf, FONT_SMALL, "omejeno med izvajanjem",
                  (COL3_X+PX, BOTTOM_Y+PY+14), TEXT_DIM)
        for sl in self.rabbit_sliders:
            sl.draw(surf, FONT_SMALL, sim_running=running)

    # ── pas mutacije (polna širina, spodaj) ───────────────────────────────
    def _draw_mutation_bar(self):
        surf = self.screen
        pygame.draw.rect(surf, BG_MID, (0, MUT_Y, SCREEN_W, MUT_H))
        self.slider_mutation.draw(surf, FONT_SMALL)

    # ── premikanje kamere ─────────────────────────────────────────────────
    def _update_camera(self, sim):
        if not sim.running:
            return
        cfg   = self.cfg
        speed = cfg.cam_speed / cfg.FPS
        keys  = self._keys_down
        if pygame.K_a   in keys or pygame.K_LEFT  in keys:
            cfg.cam_x = max(0, cfg.cam_x - speed)
        if pygame.K_d   in keys or pygame.K_RIGHT in keys:
            cfg.cam_x = min(cfg.MAP_W - SIM_W, cfg.cam_x + speed)
        if pygame.K_w   in keys or pygame.K_UP    in keys:
            cfg.cam_y = max(0, cfg.cam_y - speed)
        if pygame.K_s   in keys or pygame.K_DOWN  in keys:
            cfg.cam_y = min(cfg.MAP_H - SIM_H, cfg.cam_y + speed)


# ══════════════════════════════════════════════════════════════════════════════
# Pomožne funkcije
# ══════════════════════════════════════════════════════════════════════════════

def _text(surf, font, txt, pos, color=TEXT_MAIN):
    surf.blit(font.render(txt, True, color), pos)


def _population_trend(history):
    """Vrne (besedilo, barva) glede na trend zajcev ali (None, None)."""
    if len(history) < 10:
        return None, None
    recent = sum(history[-5:]) / 5
    prev   = sum(history[-10:-5]) / 5
    if recent < 2:
        return "IZUMIRANJE !", RED_COL
    ratio = (recent - prev) / max(prev, 1.0)
    if   ratio > 0.08:  return "RASTE  ↑", GREEN_COL
    elif ratio < -0.08: return "UPADA  ↓", RED_COL
    else:               return "STABILNO →", ACCENT
