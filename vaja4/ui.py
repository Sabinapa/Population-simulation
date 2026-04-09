"""
ui.py – celoten uporabniški vmesnik

Razporeditev zaslona (1500 × 900):
  +------SIM_W=700------+------RIGHT_W=800------+
  |                     |        GRAF            | ← h=GRAPH_H=321
  |   SIMULACIJA        +------------------------+
  |   (700 × 494)       |     STATISTIKA         | ← h=STATS_H=173
  +---------------------+------------------------+ ← y=494
  |         DRSNIK HITROST SIMULACIJE            | ← h=38
  +-COL_W=500-+-COL_W=500-+-COL_W=500-----------+ ← y=532
  | NASTAVITVE | LISICA    | ZAJEC               | ← h=330
  +------------+-----------+---------------------+ ← y=862
  |              DRSNIK MUTACIJA                 | ← h=38
  +---------------------------------------------+ ← y=900
"""

import pygame
import math
from config import Config

# ── Barve ─────────────────────────────────────────────────────────────────
BG       = ( 11,  16,  24)
CARD_A   = ( 18,  26,  42)
CARD_B   = ( 22,  33,  53)
CARD_C   = ( 14,  20,  33)
BD       = ( 34,  52,  82)
BD2      = ( 48,  72, 108)
ACCENT   = ( 82, 182, 238)
TEXT_MAIN   = (215, 232, 250)
LABEL       = (185, 210, 235)
TEXT_DIM    = (100, 132, 168)
BTN_HOVER   = ( 65, 155, 215)
BTN_NORM    = ( 32,  82, 145)
BTN_RED     = ( 95,  32,  32)
BTN_GREEN   = ( 30,  90,  42)
BTN_GREY    = ( 55,  62,  72)
GRAPH_FOX    = (215,  62,  62)
GRAPH_RABBIT = (232, 232, 232)
GRAPH_CLOVER = (155,  75, 210)   # RADIČ – vijolična
GREEN_COL    = ( 88, 228, 108)
RED_COL      = (225,  80,  65)
ACCENT2      = (235, 125,  45)
GRID_COL     = ( 30,  46,  74)

# ── Dimenzije ─────────────────────────────────────────────────────────────
SCREEN_W = 1500
SCREEN_H = 900

SIM_W    = 700
RIGHT_W  = SCREEN_W - SIM_W   # 800
RIGHT_X  = SIM_W               # 700

SPD_H    = 34
MUT_H    = 34
BOT_H    = 285                              # zmanjšan – spodnji panel nižji
TOP_H    = SCREEN_H - SPD_H - BOT_H - MUT_H   # 547

GRAPH_H  = int(TOP_H * 0.83)   # ~454
STATS_H  = TOP_H - GRAPH_H     # ~93
SIM_H    = TOP_H               # 547

SPEED_Y  = TOP_H               # 547
BOTTOM_Y = SPEED_Y + SPD_H     # 581
MUT_Y    = BOTTOM_Y + BOT_H    # 866

COL_W    = SCREEN_W // 3       # 500
COL2_X   = COL_W               # 500
COL3_X   = COL_W * 2           # 1000

PX = 12
PY = 12

FONT_TITLE = None
FONT_H2    = None
FONT_BODY  = None
FONT_SMALL = None


# ══════════════════════════════════════════════════════════════════════════
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
        pygame.draw.rect(surf, col, self.rect, border_radius=7)
        txt = font.render(self.label, True, TEXT_MAIN)
        surf.blit(txt, txt.get_rect(center=self.rect.center))


# ══════════════════════════════════════════════════════════════════════════
class Slider:
    H = 10

    def __init__(self, x, y, w, label, vmin, vmax, value,
                 integer=False, locked=False):
        self.rect    = pygame.Rect(x, y, w, self.H)
        self.label   = label
        self.vmin    = vmin
        self.vmax    = vmax
        self.value   = value
        self.integer = integer
        self.locked  = locked
        self._drag   = False

    def handle(self, event, sim_running=False):
        if self.locked and sim_running:
            self._drag = False
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.inflate(0, 16).collidepoint(event.pos):
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
        trk_col  = (16, 24, 36) if disabled else (28, 44, 66)
        fil_col  = (42, 65, 95) if disabled else ACCENT
        hdl_col  = TEXT_DIM    if disabled else (210, 235, 255)
        val_col  = TEXT_DIM    if disabled else ACCENT

        val_str  = str(int(self.value)) if self.integer else f"{self.value:.2f}"
        val_surf = font.render(val_str, True, val_col)
        lh       = val_surf.get_height()

        if self.label:
            lbl_surf = font.render(self.label, True, LABEL)
            surf.blit(lbl_surf, (x, y - lh - 3))
        surf.blit(val_surf, (x + w - val_surf.get_width(), y - lh - 3))

        pygame.draw.rect(surf, trk_col, self.rect, border_radius=4)
        pct = (self.value - self.vmin) / max(1e-9, self.vmax - self.vmin)
        fw  = int(pct * w)
        if fw > 0:
            pygame.draw.rect(surf, fil_col, (x, y, fw, self.H), border_radius=4)
        pygame.draw.circle(surf, hdl_col, (x + fw, y + self.H // 2), 6)


# ══════════════════════════════════════════════════════════════════════════
class UI:
    def __init__(self, cfg: Config):
        self.cfg    = cfg
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

        global FONT_TITLE, FONT_H2, FONT_BODY, FONT_SMALL
        pygame.font.init()
        FONT_TITLE = pygame.font.SysFont("segoeui", 16, bold=True)
        FONT_H2    = pygame.font.SysFont("segoeui", 14, bold=True)
        FONT_BODY  = pygame.font.SysFont("segoeui", 13)
        FONT_SMALL = pygame.font.SysFont("segoeui", 12)

        self.sim_surface    = pygame.Surface((SIM_W, SIM_H))
        self._sense_overlay = pygame.Surface((SIM_W, SIM_H), pygame.SRCALPHA)

        # ── y-pozicije elementov v NASTAVITVE stolpcu ─────────────────────
        fh2  = FONT_H2.get_height()
        fsm  = FONT_SMALL.get_height()
        fbd  = FONT_BODY.get_height()

        _hdr_span = PY + fh2 + 11          # od BOTTOM_Y do konca naslova
        y_btn     = BOTTOM_Y + _hdr_span   # Start/Pause/Reset
        y_ter_lbl = y_btn + 36             # "Teren:" oznaka
        y_ter     = y_ter_lbl + fsm + 4    # terrain gumbi
        y_vis     = y_ter + 22 + 8         # Vizualizacija gumb

        # Koruza drsnik (pod Vizualizacija gumbom, namesto WASD)
        _y_kor_bar = y_vis + 23 + fsm + 18  # bar y (oznaka je lh+3 nad barom)
        self._y_kor_bar = _y_kor_bar

        # ── NASTAVITVE gumbi ───────────────────────────────────────────────
        bw = (COL_W - PX * 2 - 8) // 3
        self.btn_start = Button(PX,           y_btn, bw, 26, "▶ Start")
        self.btn_pause = Button(PX + bw + 4,  y_btn, bw, 26, "⏸ Pavza")
        self.btn_reset = Button(PX + bw*2+8,  y_btn, bw, 26, "↺ Reset",  BTN_RED)

        tw = (COL_W - PX * 2 - 12) // 4
        self.terrain_btns = [
            Button(PX + i*(tw+4), y_ter, tw, 22, lbl)
            for i, lbl in enumerate(["Reka", "Jezero", "Delta", "Dolina"])
        ]
        self._y_ter_lbl = y_ter_lbl

        self.btn_visual = Button(PX, y_vis, COL_W - PX*2, 23,
                                 "Vizualizacija: VKLOPLJENA", BTN_GREEN)

        # Radič drsnik
        self.slider_clover = Slider(
            PX, _y_kor_bar, COL_W - PX*2,
            "Radič", 10, 500, cfg.initial_clovers, integer=True, locked=True)

        # ── Drsnik hitrosti (polna širina) ─────────────────────────────────
        lbl_spd_w = FONT_SMALL.size("Hitrost simulacije")[0]
        self._lbl_spd_w = lbl_spd_w
        self.slider_speed = Slider(
            PX + lbl_spd_w + PX,
            SPEED_Y + 24,
            SCREEN_W - PX*3 - lbl_spd_w,
            "", 0.2, 15.0, cfg.sim_speed)

        # ── Drsnik mutacije (od COL_W, spodaj) – zaklenjen med izvajanjem ──
        self.slider_mutation = Slider(
            COL_W + PX, MUT_Y + 24,
            SCREEN_W - COL_W - PX*2,
            "", 0.0, 0.5, cfg.mutation_chance, locked=True)

        # ── Fox/rabbit: _BPY0 brez badge (samo header + mal razmika) ──────
        _BPY0  = BOTTOM_Y + _hdr_span + 20  # brez badge – bliže naslovu
        _BSTEP = max(30, (BOT_H - (_BPY0 - BOTTOM_Y) - 16) // 7)

        # ── Drsniki lisice (stolpec 2) ─────────────────────────────────────
        self.fox_sliders = [
            Slider(COL2_X+PX, _BPY0 + i*_BSTEP, COL_W-PX*2,
                   lbl, mn, mx, val, integer=intg, locked=True)
            for i, (lbl, mn, mx, val, intg) in enumerate([
                ("Število",     1,   60,  cfg.initial_foxes,    True),
                ("Hitrost",    20,  130,  cfg.fox_speed,        False),
                ("Velikost",    4,   22,  cfg.fox_size,         True),
                ("Zaznava",    30,  200,  cfg.fox_sense_radius, False),
                ("Čas lakote", 30,  300,  cfg.fox_max_hunger,   False),
                ("Čas žeje",   20,  200,  cfg.fox_max_thirst,   False),
                ("Prag razm.", 0.3, 0.9,  cfg.fox_repro_drive,  False),
            ])
        ]

        # ── Drsniki zajca (stolpec 3) ──────────────────────────────────────
        self.rabbit_sliders = [
            Slider(COL3_X+PX, _BPY0 + i*_BSTEP, COL_W-PX*2,
                   lbl, mn, mx, val, integer=intg, locked=True)
            for i, (lbl, mn, mx, val, intg) in enumerate([
                ("Število",     5,  150,  cfg.initial_rabbits,    True),
                ("Hitrost",    20,  120,  cfg.rabbit_speed,       False),
                ("Velikost",    3,   18,  cfg.rabbit_size,        True),
                ("Zaznava",    20,  150,  cfg.rabbit_sense_radius,False),
                ("Čas lakote", 20,  200,  cfg.rabbit_max_hunger,  False),
                ("Čas žeje",   15,  150,  cfg.rabbit_max_thirst,  False),
                ("Prag razm.", 0.3, 0.9,  cfg.rabbit_repro_drive, False),
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

        # Teren samo pred zagonom – takoj prikaže predogled
        for i, btn in enumerate(self.terrain_btns):
            if btn.handle(event) and not sim.running:
                cfg.terrain_type = i + 1
                sim.preview_terrain()

        running = sim.running
        self.slider_speed.handle(event)                              # hitrost – vedno
        self.slider_mutation.handle(event, sim_running=running)      # zaklenjena med izvajanjem
        self.slider_clover.handle(event, sim_running=running)
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

        cfg.initial_clovers = int(self.slider_clover.value)
        cfg.sim_speed       = self.slider_speed.value
        cfg.mutation_chance = self.slider_mutation.value

    # ══════════════════════════════════════════════════════════════════════
    def draw(self, sim):
        self.screen.fill(BG)
        self._update_camera(sim)

        self._draw_sim(sim)
        self._draw_graph_panel(sim)
        self._draw_stats_panel(sim)
        self._draw_speed_bar()
        self._draw_bottom_panel(sim)
        self._draw_mutation_bar()

        scr = self.screen
        pygame.draw.line(scr, BD2, (RIGHT_X, 0),       (RIGHT_X, SIM_H),        1)
        pygame.draw.line(scr, BD2, (RIGHT_X, GRAPH_H), (SCREEN_W, GRAPH_H),     1)
        pygame.draw.line(scr, BD2, (0, SPEED_Y),       (SCREEN_W, SPEED_Y),     1)
        pygame.draw.line(scr, BD2, (0, BOTTOM_Y),      (SCREEN_W, BOTTOM_Y),    1)
        pygame.draw.line(scr, BD2, (COL2_X, BOTTOM_Y), (COL2_X, MUT_Y),         1)
        pygame.draw.line(scr, BD2, (COL3_X, BOTTOM_Y), (COL3_X, MUT_Y),         1)
        pygame.draw.line(scr, BD2, (0, MUT_Y),         (SCREEN_W, MUT_Y),       1)

    # ── simulacijska površina ─────────────────────────────────────────────
    def _draw_sim(self, sim):
        cfg = self.cfg
        ss  = self.sim_surface
        ss.fill((12, 18, 30))

        if sim.terrain:
            ss.blit(sim.terrain.surface, (-cfg.cam_x, -cfg.cam_y))

            # Predogled terena – simulacija še ni zagona
            if not sim.running:
                overlay = pygame.Surface((SIM_W, SIM_H), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 110))
                ss.blit(overlay, (0, 0))
                f1 = pygame.font.SysFont("segoeui", 18, bold=True)
                f2 = pygame.font.SysFont("segoeui", 13)
                m1 = f1.render("PREDOGLED TERENA", True, ACCENT)
                m2 = f2.render("Pritisni  ▶ Start  za zagon simulacije", True, TEXT_DIM)
                ss.blit(m1, (SIM_W//2 - m1.get_width()//2, SIM_H//2 - 20))
                ss.blit(m2, (SIM_W//2 - m2.get_width()//2, SIM_H//2 + 8))

            elif sim.running and sim.show_visual:
                for cl in sim.clovers:
                    cl.draw(ss, cfg.cam_x, cfg.cam_y)

                self._sense_overlay.fill((0, 0, 0, 0))
                for rb in sim.rabbits:
                    sx, sy = int(rb.x - cfg.cam_x), int(rb.y - cfg.cam_y)
                    r = int(rb.sense_radius)
                    if -r < sx < SIM_W + r and -r < sy < SIM_H + r:
                        pygame.draw.circle(self._sense_overlay,
                                           (200, 200, 150, 35), (sx, sy), r, 1)
                for fx in sim.foxes:
                    sx, sy = int(fx.x - cfg.cam_x), int(fx.y - cfg.cam_y)
                    r = int(fx.sense_radius)
                    if -r < sx < SIM_W + r and -r < sy < SIM_H + r:
                        pygame.draw.circle(self._sense_overlay,
                                           (255, 150, 50, 35), (sx, sy), r, 1)
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

        pygame.draw.rect(ss, ACCENT, (0, 0, SIM_W, SIM_H), 1)
        self.screen.blit(ss, (0, 0))

    # ── graf (desno zgoraj) ───────────────────────────────────────────────
    def _draw_graph_panel(self, sim):
        surf = self.screen
        pygame.draw.rect(surf, CARD_A, (RIGHT_X, 0, RIGHT_W, GRAPH_H))
        _draw_hdr(surf, RIGHT_X+PX, PY, RIGHT_W-PX*2, "Graf populacije")

        fsm_h = FONT_SMALL.get_height()   # ~12 px

        # Robovi: levo za y-oznake, zgoraj pod naslovno vrstico,
        # spodaj za x-oznake + napis osi, desno za vrednostne labele
        mx = 54           # levo  – dovolj za "300", "1200" …
        mt = 48           # zgoraj – pod header linijo
        mb = fsm_h * 2 + 12   # spodaj – vrstica za tick številke + vrstica za "čas"
        mr = 76           # desno  – za "999 Radič"

        px0 = RIGHT_X + mx
        py0 = mt
        pw  = RIGHT_W - mx - mr
        ph  = GRAPH_H - mt - mb

        # Ozadje grafa
        pygame.draw.rect(surf, (8, 12, 22),  (px0, py0, pw, ph))
        pygame.draw.rect(surf, (24, 38, 62), (px0, py0, pw, ph), 1)

        # Izračun max vrednosti za os Y
        if sim.running:
            series = [
                (sim.history_fox,    GRAPH_FOX,    "Lisice"),
                (sim.history_rabbit, GRAPH_RABBIT, "Zajci"),
                (sim.history_clover, GRAPH_CLOVER, "Radič"),
            ]
            all_vals = [v for s, _, _ in series for v in s]
        else:
            series   = []
            all_vals = []

        max_v = max(all_vals) if all_vals else 100
        if max_v >= 10:
            mag      = 10 ** math.floor(math.log10(max_v))
            max_nice = math.ceil(max_v / mag) * mag
        else:
            max_nice = max(10, math.ceil(max_v / 5) * 5)

        # ── Y-os: mrežne črte + oznake ───────────────────────────────────
        N_Y = 5
        for i in range(N_Y + 1):
            val = int(i * max_nice / N_Y)
            gy  = py0 + ph - int(i / N_Y * ph)
            # mrežna črta
            pygame.draw.line(surf, (20, 32, 52), (px0, gy), (px0 + pw, gy), 1)
            # kratka tick-ica na osi
            pygame.draw.line(surf, (60, 90, 130), (px0 - 4, gy), (px0, gy), 1)
            # oznaka – desno poravnana
            lbl = FONT_SMALL.render(str(val), True, (110, 150, 190))
            surf.blit(lbl, (px0 - lbl.get_width() - 7, gy - fsm_h // 2))

        # ── X-os: mrežne črte + oznake + napis osi ───────────────────────
        n_data = max((len(s) for s, _, _ in series if s), default=2)
        n_xt   = min(7, max(1, n_data - 1))
        tick_y = py0 + ph + 6               # prva vrstica: številke
        axis_y = tick_y + fsm_h + 4         # druga vrstica: "čas (koraki)"

        for i in range(n_xt + 1):
            frac = i / n_xt
            idx  = int(frac * max(n_data - 1, 1))
            gx   = px0 + int(frac * pw)
            # navpična mrežna črta
            pygame.draw.line(surf, (20, 32, 52), (gx, py0), (gx, py0 + ph), 1)
            # kratka tick-ica na osi
            pygame.draw.line(surf, (60, 90, 130), (gx, py0 + ph), (gx, py0 + ph + 4), 1)
            # oznaka
            lbl = FONT_SMALL.render(str(idx * 30), True, (110, 150, 190))
            surf.blit(lbl, (gx - lbl.get_width() // 2, tick_y))

        # napis x-osi – centriran, v drugi vrstici
        ax_lbl = FONT_SMALL.render("čas  (koraki)", True, (70, 100, 140))
        surf.blit(ax_lbl, (px0 + pw // 2 - ax_lbl.get_width() // 2, axis_y))

        # ── Osi (robni črti) ──────────────────────────────────────────────
        AX_COL = (55, 85, 130)
        pygame.draw.line(surf, AX_COL, (px0, py0),       (px0,       py0 + ph), 2)
        pygame.draw.line(surf, AX_COL, (px0, py0 + ph),  (px0 + pw,  py0 + ph), 2)

        if not series:
            return

        # ── Krivulje ──────────────────────────────────────────────────────
        dot_x  = px0 + pw + 8
        used_y = []
        for data, color, name in series:
            if len(data) < 2:
                continue
            n   = len(data)
            pts = [
                (px0 + int(i / (n - 1) * pw),
                 max(py0 + 1, min(py0 + ph - 1,
                     py0 + ph - int(v / max_nice * ph))))
                for i, v in enumerate(data)
            ]
            pygame.draw.aalines(surf, color, False, pts)

            # Pika + vrednostna oznaka desno od grafa
            ex, ey = pts[-1]
            pygame.draw.circle(surf, color,        (ex, ey), 5)
            pygame.draw.circle(surf, (8, 12, 22),  (ex, ey), 2)

            label_y = ey - fsm_h // 2
            for uy in used_y:
                if abs(label_y - uy) < fsm_h + 2:
                    label_y = uy + fsm_h + 2
            used_y.append(label_y)
            val_s = FONT_SMALL.render(f"{int(data[-1])}  {name}", True, color)
            surf.blit(val_s, (dot_x, label_y))

    def _draw_y_ticks(self, surf, px0, py0, pw, ph, max_nice):
        """Ohranjena za morebitno zunanja klica – zdaj notranje ni več v uporabi."""
        for i in range(6):
            val = int(i * max_nice / 5)
            gy  = py0 + ph - int(i / 5 * ph)
            pygame.draw.line(surf, (20, 32, 52), (px0, gy), (px0 + pw, gy), 1)
            lbl = FONT_SMALL.render(str(val), True, (110, 150, 190))
            surf.blit(lbl, (px0 - lbl.get_width() - 7, gy - FONT_SMALL.get_height() // 2))

    # ── statistika (desno spodaj) – kompaktna 2-vrstična oblika ──────────
    def _draw_stats_panel(self, sim):
        surf = self.screen
        pygame.draw.rect(surf, CARD_B, (RIGHT_X, GRAPH_H, RIGHT_W, STATS_H))
        sy = _draw_hdr(surf, RIGHT_X+PX, GRAPH_H+PY, RIGHT_W-PX*2, "Statistika")

        n_fox    = len(sim.foxes)   if sim.running else 0
        n_rabbit = len(sim.rabbits) if sim.running else 0
        n_clover = sum(1 for c in sim.clovers if not c.eaten) if sim.running else 0
        step     = sim.tick         if sim.running else 0
        elapsed  = sim.elapsed      if sim.running else 0.0

        fh    = FONT_BODY.get_height()
        col_w = RIGHT_W // 3

        # ── Vrstica 1: Lisice  Zajci  Radič ───────────────────────────────
        for i, (lbl, val, col) in enumerate([
            ("Lisice",  str(n_fox),    GRAPH_FOX),
            ("Zajci",   str(n_rabbit), GRAPH_RABBIT),
            ("Radič",   str(n_clover), GRAPH_CLOVER),
        ]):
            cx = RIGHT_X + PX + i * col_w
            _text(surf, FONT_BODY, lbl, (cx, sy), TEXT_DIM)
            lw = FONT_BODY.size(lbl)[0]
            _text(surf, FONT_TITLE, val, (cx + lw + 8, sy - 1), col)

        # ── Vrstica 2: Korak  Čas ─────────────────────────────────────────
        sy2 = sy + fh + 10
        for i, (lbl, val) in enumerate([
            ("Korak",  str(step)),
            ("Čas",    f"{elapsed:.0f} s"),
        ]):
            cx = RIGHT_X + PX + i * col_w
            _text(surf, FONT_BODY, lbl, (cx, sy2), TEXT_DIM)
            lw = FONT_BODY.size(lbl)[0]
            _text(surf, FONT_BODY, val, (cx + lw + 8, sy2), LABEL)

    # ── pas hitrosti simulacije ───────────────────────────────────────────
    def _draw_speed_bar(self):
        surf = self.screen
        pygame.draw.rect(surf, CARD_C, (0, SPEED_Y, SCREEN_W, SPD_H))
        lbl = FONT_SMALL.render("Hitrost simulacije", True, LABEL)
        surf.blit(lbl, (PX, SPEED_Y + SPD_H//2 - lbl.get_height()//2))
        self.slider_speed.draw(surf, FONT_SMALL)

    # ── spodnji 3-stolpčni panel ──────────────────────────────────────────
    def _draw_bottom_panel(self, sim):
        surf    = self.screen
        running = sim.running

        pygame.draw.rect(surf, CARD_A,  (0,      BOTTOM_Y, COL_W,           BOT_H))
        pygame.draw.rect(surf, CARD_C,  (COL2_X, BOTTOM_Y, COL_W,           BOT_H))
        pygame.draw.rect(surf, CARD_A,  (COL3_X, BOTTOM_Y, SCREEN_W-COL3_X, BOT_H))

        # ── Stolpec 1: NASTAVITVE ──────────────────────────────────────────
        s  = FONT_H2.render("EKOSISTEM SIMULACIJA", True, ACCENT)
        tx = COL_W // 2 - s.get_width() // 2
        surf.blit(s, (tx, BOTTOM_Y + PY))
        lh = s.get_height()
        pygame.draw.line(surf, ACCENT,
                         (PX, BOTTOM_Y+PY+lh+2), (COL_W-PX, BOTTOM_Y+PY+lh+2), 1)

        for b in (self.btn_start, self.btn_pause, self.btn_reset):
            b.draw(surf, FONT_BODY)

        _text(surf, FONT_SMALL, "Teren:", (PX, self._y_ter_lbl), LABEL)
        for btn in self.terrain_btns:
            btn.draw(surf, FONT_SMALL)
        active_r = self.terrain_btns[self.cfg.terrain_type - 1].rect
        pygame.draw.rect(surf, ACCENT, active_r, 2, border_radius=5)

        self.btn_visual.draw(surf, FONT_SMALL)

        # Radič drsnik
        self.slider_clover.draw(surf, FONT_SMALL, sim_running=running)

        # ── Stolpec 2: Lastnosti lisice (brez badge) ───────────────────────
        _draw_hdr(surf, COL2_X+PX, BOTTOM_Y+PY, COL_W-PX*2,
                  "Lastnosti lisice  (plenilec)", GRAPH_FOX)
        for sl in self.fox_sliders:
            sl.draw(surf, FONT_SMALL, sim_running=running)

        # ── Stolpec 3: Lastnosti zajca (brez badge) ────────────────────────
        _draw_hdr(surf, COL3_X+PX, BOTTOM_Y+PY, COL_W-PX*2,
                  "Lastnosti zajca  (plen)", GRAPH_RABBIT)
        for sl in self.rabbit_sliders:
            sl.draw(surf, FONT_SMALL, sim_running=running)

    # ── pas mutacije ──────────────────────────────────────────────────────
    def _draw_mutation_bar(self):
        surf = self.screen
        pygame.draw.rect(surf, CARD_C, (0, MUT_Y, SCREEN_W, MUT_H))
        lbl = FONT_SMALL.render("Mutacija", True, LABEL)
        surf.blit(lbl, (PX, MUT_Y + MUT_H//2 - lbl.get_height()//2))
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


# ══════════════════════════════════════════════════════════════════════════
# Pomožne funkcije
# ══════════════════════════════════════════════════════════════════════════

def _text(surf, font, txt, pos, color=TEXT_MAIN):
    surf.blit(font.render(txt, True, color), pos)


def _draw_hdr(surf, x, y, w, label, col=ACCENT, font=None, center_in=None):
    if font is None:
        font = FONT_H2
    s  = font.render(label, True, col)
    lh = s.get_height()
    tx = (center_in // 2 - s.get_width() // 2) if center_in else x
    surf.blit(s, (tx, y))
    pygame.draw.line(surf, col, (x, y+lh+2), (x+w, y+lh+2), 1)
    return y + lh + 9


def _population_trend(history):
    if len(history) < 10:
        return None, None
    recent = sum(history[-5:]) / 5
    prev   = sum(history[-10:-5]) / 5
    if recent < 2:
        return "IZUMIRANJE !", RED_COL
    ratio = (recent - prev) / max(prev, 1.0)
    if   ratio >  0.08: return "RASTE  ↑",   GREEN_COL
    elif ratio < -0.08: return "UPADA  ↓",   RED_COL
    else:               return "STABILNO →", ACCENT
