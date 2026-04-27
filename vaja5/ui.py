import pygame
import math
from config import Config

# ── Barvna paleta UI ──────────────────────────────────────────────────────────
BG          = ( 11,  16,  24)   # barva ozadja celotnega okna
CARD_A      = ( 18,  26,  42)   # barva temnejše kartice (1. in 3. stolpec)
CARD_B      = ( 22,  33,  53)   # barva srednje kartice (statistike)
CARD_C      = ( 14,  20,  33)   # barva najtmnejše kartice (2. stolpec, vrstice)
BORDER      = ( 48,  72, 108)   # barva ločilnih črt med področji
ACCENT      = ( 82, 182, 238)   # poudarjena barva (naslovi, osi, rob simulacije)
TEXT_MAIN   = (215, 232, 250)   # barva glavnega besedila
LABEL       = (185, 210, 235)   # barva oznak drsnikov in opisov
TEXT_DIM    = (100, 132, 168)   # barva zatemnjenih/sekundarnih besedil
BTN_HOVER   = ( 65, 155, 215)   # barva gumba ob lebdenju miške
BTN_NORM    = ( 32,  82, 145)   # barva gumba v normalnem stanju
BTN_RED     = ( 95,  32,  32)   # barva gumba Reset
BTN_GREEN   = ( 30,  90,  42)   # barva gumba Vizualizacija (vklopljena)
BTN_GREY    = ( 55,  62,  72)   # barva gumba Vizualizacija (izklopljena)
GRAPH_FOX    = (215,  62,  62)  # barva krivulje lisic na grafu
GRAPH_RABBIT = (232, 232, 232)  # barva krivulje zajcev na grafu
GRAPH_CLOVER = (155,  75, 210)  # barva krivulje radiča na grafu
BIRTH_COLOR  = (255, 140, 200)  # barva oznake rojstev v tabeli statistik

# ── Konstante razporeditve ────────────────────────────────────────────────────
SCREEN_W = 1500             # širina okna v pikslih
SCREEN_H = 950              # višina okna v pikslih

SIM_W    = 700              # širina simulacijskega pogleda v pikslih
RIGHT_W  = SCREEN_W - SIM_W        # širina desnega področja (graf + statistike) = 800
RIGHT_X  = SIM_W                   # x koordinata začetka desnega področja = 700

SPEED_BAR_H    = 34         # višina vrstice za drsnik hitrosti simulacije
MUTATION_BAR_H = 34         # višina vrstice za drsnik mutacije
BOTTOM_PANEL_H = 335        # višina spodnje plošče z gumbi in drsniki
TOP_H    = SCREEN_H - SPEED_BAR_H - BOTTOM_PANEL_H - MUTATION_BAR_H   # višina zgornjega področja = 547

GRAPH_H  = int(TOP_H * 0.83)       # višina grafa populacije
STATS_H  = TOP_H - GRAPH_H         # višina področja statistik pod grafom
SIM_H    = TOP_H                    # višina simulacijskega pogleda (enaka zgornjemu področju)

SPEED_Y  = TOP_H                            # y koordinata vrstice hitrosti
BOTTOM_Y = SPEED_Y + SPEED_BAR_H           # y koordinata spodnje plošče
MUT_Y    = BOTTOM_Y + BOTTOM_PANEL_H       # y koordinata vrstice mutacije

COL_W    = SCREEN_W // 3    # širina vsakega od treh stolpcev spodnje plošče
COL2_X   = COL_W            # x koordinata začetka 2. stolpca
COL3_X   = COL_W * 2        # x koordinata začetka 3. stolpca

PX = 12     # horizontalni notranji odmik (padding) elementov od roba
PY = 12     # vertikalni notranji odmik (padding) elementov od roba


# ── Pomožne funkcije na nivoju modula ─────────────────────────────────────────
def _text(surf, font, txt, pos, color=TEXT_MAIN):
    surf.blit(font.render(txt, True, color), pos)


def _draw_hdr(surf, x, y, w, label, font, col=ACCENT, center_in=None):
    # Nariše razdelek naslov s podčrtajem; vrne y pod naslovom.
    s  = font.render(label, True, col)
    label_height = s.get_height()
    tx = (center_in // 2 - s.get_width() // 2) if center_in else x
    surf.blit(s, (tx, y))
    pygame.draw.line(surf, col, (x, y + label_height + 2), (x + w, y + label_height + 2), 1)
    return y + label_height + 9


# ── Gumb ──────────────────────────────────────────────────────────────────────
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


# ── Drsnik ────────────────────────────────────────────────────────────────────
class Slider:
    H = 10  # višina drsne vrstice v pikslih

    def __init__(self, x, y, w, label, vmin, vmax, value,
                 integer=False, locked=False):
        self.rect    = pygame.Rect(x, y, w, self.H)
        self.label   = label
        self.vmin    = vmin        # najmanjša vrednost drsnika
        self.vmax    = vmax        # največja vrednost drsnika
        self.value   = value       # trenutna vrednost drsnika
        self.integer = integer     # če True, vrednost zaokrožena na celo število
        self.locked  = locked      # če True, drsnik zaklenjen med izvajanjem simulacije
        self._drag   = False       # ali uporabnik trenutno vleče drsnik

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

        # Barve glede na stanje (zaklenjen / aktiven)
        trk_col  = (16, 24, 36) if disabled else (28, 44, 66)  # barva tira
        fil_col  = (42, 65, 95) if disabled else ACCENT         # barva zapolnjenega dela
        hdl_col  = TEXT_DIM    if disabled else (210, 235, 255) # barva ročice
        val_col  = TEXT_DIM    if disabled else ACCENT          # barva prikazane vrednosti

        val_str      = str(int(self.value)) if self.integer else f"{self.value:.2f}"
        val_surf     = font.render(val_str, True, val_col)
        label_height = val_surf.get_height()    # višina besedila za odmik nad drsnikom

        if self.label:
            lbl_surf = font.render(self.label, True, LABEL)
            surf.blit(lbl_surf, (x, y - label_height - 3))
        surf.blit(val_surf, (x + w - val_surf.get_width(), y - label_height - 3))

        pygame.draw.rect(surf, trk_col, self.rect, border_radius=4)
        pct = (self.value - self.vmin) / max(1e-9, self.vmax - self.vmin)
        fill_w = int(pct * w)   # širina zapolnjenega dela drsnika
        if fill_w > 0:
            pygame.draw.rect(surf, fil_col, (x, y, fill_w, self.H), border_radius=4)
        pygame.draw.circle(surf, hdl_col, (x + fill_w, y + self.H // 2), 6)


# ── UI ────────────────────────────────────────────────────────────────────────
class UI:
    def __init__(self, cfg: Config):
        self.cfg    = cfg
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self._keys_down = set()     # množica trenutno pritisnjenih tipk

        self._init_fonts()
        self._init_surfaces()
        self._init_buttons()
        self._init_sliders()

    # ── Pomočniki za inicializacijo ────────────────────────────────────────────
    def _init_fonts(self):
        pygame.font.init()
        self.font_title = pygame.font.SysFont("segoeui", 16, bold=True)    # naslovni font
        self.font_h2    = pygame.font.SysFont("segoeui", 14, bold=True)    # font podnaslovov
        self.font_body  = pygame.font.SysFont("segoeui", 13)               # font osnovnega besedila
        self.font_small = pygame.font.SysFont("segoeui", 12)               # font malih oznak

    def _init_surfaces(self):
        self.sim_surface    = pygame.Surface((SIM_W, SIM_H))               # površina simulacijskega pogleda
        self._sense_overlay = pygame.Surface((SIM_W, SIM_H), pygame.SRCALPHA)  # prosojna plast za zaznavne kroге

    def _init_buttons(self):
        h2_h    = self.font_h2.get_height()     # višina pisave podnaslovov
        small_h = self.font_small.get_height()  # višina pisave malih oznak

        hdr_span  = PY + h2_h + 11     # skupna višina naslova razdelka z razmakom
        y_btn     = BOTTOM_Y + PY      # y koordinata vrstice z gumbi Start/Pavza/Reset
        y_ter_lbl = y_btn + 36         # y koordinata oznake "Teren:"
        y_ter     = y_ter_lbl + small_h + 4    # y koordinata gumbov za izbiro terena
        y_vis     = y_ter + 22 + 8     # y koordinata gumba za vizualizacijo

        self._y_ter_lbl = y_ter_lbl    # shranimo za risanje oznake terena
        self._y_vis     = y_vis        # shranimo za izračun položaja drsnika radiča
        self._hdr_span  = hdr_span     # shranimo za izračun začetka drsnikov

        btn_w = (COL_W - PX * 2 - 8) // 3      # širina vsakega od treh kontrolnih gumbov
        self.btn_start = Button(PX,                 y_btn, btn_w, 26, "▶ Start")
        self.btn_pause = Button(PX + btn_w + 4,     y_btn, btn_w, 26, "⏸ Pavza")
        self.btn_reset = Button(PX + btn_w * 2 + 8, y_btn, btn_w, 26, "↺ Reset", BTN_RED)

        terrain_btn_w = (COL_W - PX * 2 - 12) // 4    # širina vsakega gumba za izbiro terena
        self.terrain_btns = [
            Button(PX + i * (terrain_btn_w + 4), y_ter, terrain_btn_w, 22, lbl)
            for i, lbl in enumerate(["Reka", "Jezero", "Delta", "Dolina"])
        ]

        self.btn_visual = Button(PX, y_vis, COL_W - PX * 2, 23,
                                 "Vizualizacija: VKLOPLJENA", BTN_GREEN)

    def _init_sliders(self):
        small_h = self.font_small.get_height()  # višina pisave za izračun razmikov

        y_vis       = self._y_vis
        y_clover    = y_vis + 23 + small_h + 18    # y koordinata drsnika za radič
        self._y_clover_bar = y_clover

        # Drsnik hitrosti (polna širina, vedno odklenjen)
        lbl_spd_w = self.font_small.size("Hitrost simulacije")[0]   # širina oznake drsnika hitrosti
        self._lbl_spd_w = lbl_spd_w
        self.slider_speed = Slider(
            PX + lbl_spd_w + PX,
            SPEED_Y + 24,
            SCREEN_W - PX * 3 - lbl_spd_w,
            "", 0.2, 15.0, self.cfg.sim_speed)

        # Drsnik mutacije (zaklenjen med simulacijo)
        self.slider_mutation = Slider(
            COL_W + PX, MUT_Y + 24,
            SCREEN_W - COL_W - PX * 2,
            "", 0.0, 0.5, self.cfg.mutation_chance, locked=True)

        # Drsnik radiča (zaklenjen med simulacijo)
        self.slider_clover = Slider(
            PX, y_clover, COL_W - PX * 2,
            "Radič", 10, 500, self.cfg.initial_clovers, integer=True, locked=True)

        cfg             = self.cfg
        sliders_y_start = BOTTOM_Y + self._hdr_span + 20       # y koordinata prvega drsnika v stolpcih
        slider_row_step = max(30, (BOTTOM_PANEL_H - (sliders_y_start - BOTTOM_Y) - 16) // 7)  # razmik med drsniki

        # Drsniki za lisico (2. stolpec)
        self.fox_sliders = [
            Slider(COL2_X + PX, sliders_y_start + i * slider_row_step, COL_W - PX * 2,
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

        # Drsniki za zajca (3. stolpec)
        self.rabbit_sliders = [
            Slider(COL3_X + PX, sliders_y_start + i * slider_row_step, COL_W - PX * 2,
                   lbl, mn, mx, val, integer=intg, locked=True)
            for i, (lbl, mn, mx, val, intg) in enumerate([
                ("Število",     5,  150,  cfg.initial_rabbits,     True),
                ("Hitrost",    20,  120,  cfg.rabbit_speed,        False),
                ("Velikost",    3,   18,  cfg.rabbit_size,         True),
                ("Zaznava",    20,  150,  cfg.rabbit_sense_radius, False),
                ("Čas lakote", 20,  200,  cfg.rabbit_max_hunger,   False),
                ("Čas žeje",   15,  150,  cfg.rabbit_max_thirst,   False),
                ("Prag razm.", 0.3, 0.9,  cfg.rabbit_repro_drive,  False),
            ])
        ]

    # ── Obravnava dogodkov ────────────────────────────────────────────────────
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

        # Gumbi za teren – aktivni le pred zagonom simulacije
        for i, btn in enumerate(self.terrain_btns):
            if btn.handle(event) and not sim.running:
                cfg.terrain_type = i + 1
                sim.preview_terrain()

        running = sim.running
        self.slider_speed.handle(event)
        self.slider_mutation.handle(event, sim_running=running)
        self.slider_clover.handle(event, sim_running=running)
        for sl in self.fox_sliders:    sl.handle(event, sim_running=running)
        for sl in self.rabbit_sliders: sl.handle(event, sim_running=running)

        cfg.sim_speed       = self.slider_speed.value
        cfg.mutation_chance = self.slider_mutation.value

    def _apply_sliders_to_cfg(self):
        # Prenese vrednosti vseh drsnikov v konfiguracijo pred zagonom simulacije.
        cfg = self.cfg
        fs  = self.fox_sliders      # seznam drsnikov za lisico
        rs  = self.rabbit_sliders   # seznam drsnikov za zajca

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

    # ── Risanje okvirja ───────────────────────────────────────────────────────
    def draw(self, sim):
        self.screen.fill(BG)
        self._update_camera(sim)

        self._draw_sim(sim)
        self._draw_graph_panel(sim)
        self._draw_stats_panel(sim)
        self._draw_speed_bar()
        self._draw_bottom_panel(sim)
        self._draw_mutation_bar()

        # Ločilne črte med področji okna
        scr = self.screen
        pygame.draw.line(scr, BORDER, (RIGHT_X, 0),       (RIGHT_X, SIM_H),     1)
        pygame.draw.line(scr, BORDER, (RIGHT_X, GRAPH_H), (SCREEN_W, GRAPH_H),  1)
        pygame.draw.line(scr, BORDER, (0, SPEED_Y),       (SCREEN_W, SPEED_Y),  1)
        pygame.draw.line(scr, BORDER, (0, BOTTOM_Y),      (SCREEN_W, BOTTOM_Y), 1)
        pygame.draw.line(scr, BORDER, (COL2_X, BOTTOM_Y), (COL2_X, MUT_Y),      1)
        pygame.draw.line(scr, BORDER, (COL3_X, BOTTOM_Y), (COL3_X, MUT_Y),      1)
        pygame.draw.line(scr, BORDER, (0, MUT_Y),         (SCREEN_W, MUT_Y),    1)

    # ── Simulacijski pogled ───────────────────────────────────────────────────
    def _draw_sim(self, sim):
        cfg = self.cfg
        ss  = self.sim_surface
        ss.fill((12, 18, 30))

        if sim.terrain:
            ss.blit(sim.terrain.surface, (-cfg.cam_x, -cfg.cam_y))

            if not sim.running:
                overlay = pygame.Surface((SIM_W, SIM_H), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 110))
                ss.blit(overlay, (0, 0))
                f1 = pygame.font.SysFont("segoeui", 18, bold=True)
                f2 = pygame.font.SysFont("segoeui", 13)
                m1 = f1.render("PREDOGLED TERENA", True, ACCENT)
                m2 = f2.render("Pritisni  ▶ Start  za zagon simulacije", True, TEXT_DIM)
                ss.blit(m1, (SIM_W // 2 - m1.get_width() // 2, SIM_H // 2 - 20))
                ss.blit(m2, (SIM_W // 2 - m2.get_width() // 2, SIM_H // 2 + 8))

            elif sim.show_visual:
                for clover in sim.clovers:
                    clover.draw(ss, cfg.cam_x, cfg.cam_y)

                self._sense_overlay.fill((0, 0, 0, 0))
                for rabbit in sim.rabbits:
                    sx, sy = int(rabbit.x - cfg.cam_x), int(rabbit.y - cfg.cam_y)
                    r = int(rabbit.sense_radius)
                    if -r < sx < SIM_W + r and -r < sy < SIM_H + r:
                        pygame.draw.circle(self._sense_overlay,
                                           (200, 200, 150, 35), (sx, sy), r, 1)
                for fox in sim.foxes:
                    sx, sy = int(fox.x - cfg.cam_x), int(fox.y - cfg.cam_y)
                    r = int(fox.sense_radius)
                    if -r < sx < SIM_W + r and -r < sy < SIM_H + r:
                        pygame.draw.circle(self._sense_overlay,
                                           (255, 150, 50, 35), (sx, sy), r, 1)
                ss.blit(self._sense_overlay, (0, 0))

                for rabbit in sim.rabbits: rabbit.draw(ss, cfg.cam_x, cfg.cam_y)
                for fox    in sim.foxes:   fox.draw(ss, cfg.cam_x, cfg.cam_y)

            else:
                f1 = pygame.font.SysFont("segoeui", 17, bold=True)
                f2 = pygame.font.SysFont("segoeui", 12)
                m1 = f1.render("Vizualizacija izklopljena", True, ACCENT)
                m2 = f2.render("Simulacija poteka v ozadju  –  grafi se posodabljajo",
                               True, TEXT_DIM)
                ss.blit(m1, (SIM_W // 2 - m1.get_width() // 2, SIM_H // 2 - 18))
                ss.blit(m2, (SIM_W // 2 - m2.get_width() // 2, SIM_H // 2 + 8))

        pygame.draw.rect(ss, ACCENT, (0, 0, SIM_W, SIM_H), 1)
        self.screen.blit(ss, (0, 0))

    # ── Graf populacije ───────────────────────────────────────────────────────
    def _draw_graph_panel(self, sim):
        surf    = self.screen
        small_h = self.font_small.get_height()
        pygame.draw.rect(surf, CARD_A, (RIGHT_X, 0, RIGHT_W, GRAPH_H))
        _draw_hdr(surf, RIGHT_X + PX, PY, RIGHT_W - PX * 2, "Graf populacije", self.font_h2)

        margin_left   = 54      # odmik grafičnega področja od levega roba
        margin_top    = 48      # odmik grafičnega področja od zgornjega roba
        margin_bottom = small_h * 2 + 12    # odmik za oznake osi X
        margin_right  = 76      # odmik za vrednostne oznake desno od grafa

        px0 = RIGHT_X + margin_left        # x koordinata levega roba grafa
        py0 = margin_top                   # y koordinata zgornjega roba grafa
        pw  = RIGHT_W - margin_left - margin_right  # širina grafičnega področja
        ph  = GRAPH_H  - margin_top  - margin_bottom    # višina grafičnega področja

        pygame.draw.rect(surf, (8, 12, 22),  (px0, py0, pw, ph))
        pygame.draw.rect(surf, (24, 38, 62), (px0, py0, pw, ph), 1)

        series   = []
        all_vals = []
        if sim.running:
            series = [
                (sim.history_fox,    GRAPH_FOX,    "Lisice"),
                (sim.history_rabbit, GRAPH_RABBIT, "Zajci"),
                (sim.history_clover, GRAPH_CLOVER, "Radič"),
            ]
            all_vals = [v for s, _, _ in series for v in s]

        max_v = max(all_vals) if all_vals else 100
        if max_v >= 10:
            mag      = 10 ** math.floor(math.log10(max_v))
            max_nice = math.ceil(max_v / mag) * mag
        else:
            max_nice = max(10, math.ceil(max_v / 5) * 5)

        # Mrežne črte in oznake osi Y
        num_y_ticks = 5     # število delilnih oznak na osi Y
        for i in range(num_y_ticks + 1):
            val = int(i * max_nice / num_y_ticks)
            gy  = py0 + ph - int(i / num_y_ticks * ph)     # y koordinata mrežne črte
            pygame.draw.line(surf, (20, 32, 52), (px0, gy), (px0 + pw, gy), 1)
            pygame.draw.line(surf, (60, 90, 130), (px0 - 4, gy), (px0, gy), 1)
            lbl = self.font_small.render(str(val), True, (110, 150, 190))
            surf.blit(lbl, (px0 - lbl.get_width() - 7, gy - small_h // 2))

        # Mrežne črte, oznake klop in oznaka osi X
        n_data      = max((len(s) for s, _, _ in series if s), default=2)
        num_x_ticks = min(7, max(1, n_data - 1))   # število delilnih oznak na osi X
        tick_y      = py0 + ph + 6                 # y koordinata oznak osi X
        axis_y      = tick_y + small_h + 4         # y koordinata napisa "čas (koraki)"

        for i in range(num_x_ticks + 1):
            frac = i / num_x_ticks
            idx  = int(frac * max(n_data - 1, 1))
            gx   = px0 + int(frac * pw)     # x koordinata navpične mrežne črte
            pygame.draw.line(surf, (20, 32, 52), (gx, py0), (gx, py0 + ph), 1)
            pygame.draw.line(surf, (60, 90, 130), (gx, py0 + ph), (gx, py0 + ph + 4), 1)
            lbl = self.font_small.render(str(idx * 30), True, (110, 150, 190))
            surf.blit(lbl, (gx - lbl.get_width() // 2, tick_y))

        ax_lbl = self.font_small.render("čas  (koraki)", True, (70, 100, 140))
        surf.blit(ax_lbl, (px0 + pw // 2 - ax_lbl.get_width() // 2, axis_y))

        axis_color = (55, 85, 130)  # barva osi grafa
        pygame.draw.line(surf, axis_color, (px0, py0),      (px0,      py0 + ph), 2)
        pygame.draw.line(surf, axis_color, (px0, py0 + ph), (px0 + pw, py0 + ph), 2)

        if not series:
            return

        # Nariši krivulje in vrednostne oznake desno od grafa
        labels_x  = px0 + pw + 8   # x koordinata vrednostnih oznak desno od grafa
        used_y    = []              # seznam že zasedenih y koordinat oznak (za izogibanje prekrivanju)
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

            ex, ey = pts[-1]    # koordinata zadnje točke krivulje
            pygame.draw.circle(surf, color,       (ex, ey), 5)
            pygame.draw.circle(surf, (8, 12, 22), (ex, ey), 2)

            label_y = ey - small_h // 2
            for uy in used_y:
                if abs(label_y - uy) < small_h + 2:
                    label_y = uy + small_h + 2
            used_y.append(label_y)
            val_s = self.font_small.render(f"{int(data[-1])}  {name}", True, color)
            surf.blit(val_s, (labels_x, label_y))

    # ── Plošča statistik ──────────────────────────────────────────────────────
    def _draw_stats_panel(self, sim):
        surf = self.screen
        pygame.draw.rect(surf, CARD_B, (RIGHT_X, GRAPH_H, RIGHT_W, STATS_H))
        sy = _draw_hdr(surf, RIGHT_X + PX, GRAPH_H + PY, RIGHT_W - PX * 2,
                       "Statistika", self.font_h2)

        n_fox    = len(sim.foxes)   if sim.running else 0
        n_rabbit = len(sim.rabbits) if sim.running else 0
        n_clover = sum(1 for c in sim.clovers if not c.eaten) if sim.running else 0
        step     = sim.tick         if sim.running else 0
        elapsed  = sim.elapsed      if sim.running else 0.0

        body_h = self.font_body.get_height()    # višina pisave za razmik med vrsticami
        col_w  = RIGHT_W // 3                   # širina vsakega od treh stolpcev statistik

        for i, (lbl, val, col) in enumerate([
            ("Lisice",  str(n_fox),    GRAPH_FOX),
            ("Zajci",   str(n_rabbit), GRAPH_RABBIT),
            ("Radič",   str(n_clover), GRAPH_CLOVER),
        ]):
            cx = RIGHT_X + PX + i * col_w      # x koordinata začetka stolpca
            _text(surf, self.font_body, lbl, (cx, sy), TEXT_DIM)
            lw = self.font_body.size(lbl)[0]   # širina oznake za odmik vrednosti
            _text(surf, self.font_title, val, (cx + lw + 8, sy - 1), col)

        sy2 = sy + body_h + 10     # y koordinata druge vrstice statistik (korak in čas)
        for i, (lbl, val) in enumerate([
            ("Korak", str(step)),
            ("Čas",   f"{elapsed:.0f} s"),
        ]):
            cx = RIGHT_X + PX + i * col_w
            _text(surf, self.font_body, lbl, (cx, sy2), TEXT_DIM)
            lw = self.font_body.size(lbl)[0]
            _text(surf, self.font_body, val, (cx + lw + 8, sy2), LABEL)

    # ── Vrstica hitrosti ──────────────────────────────────────────────────────
    def _draw_speed_bar(self):
        surf = self.screen
        pygame.draw.rect(surf, CARD_C, (0, SPEED_Y, SCREEN_W, SPEED_BAR_H))
        lbl = self.font_small.render("Hitrost simulacije", True, LABEL)
        surf.blit(lbl, (PX, SPEED_Y + SPEED_BAR_H // 2 - lbl.get_height() // 2))
        self.slider_speed.draw(surf, self.font_small)

    # ── Spodnja plošča ────────────────────────────────────────────────────────
    def _draw_bottom_panel(self, sim):
        # Nariše ozadja kartic, nato delegira vsak stolpec svoji metodi.
        surf = self.screen
        pygame.draw.rect(surf, CARD_A, (0,      BOTTOM_Y, COL_W,           BOTTOM_PANEL_H))
        pygame.draw.rect(surf, CARD_C, (COL2_X, BOTTOM_Y, COL_W,           BOTTOM_PANEL_H))
        pygame.draw.rect(surf, CARD_A, (COL3_X, BOTTOM_Y, SCREEN_W-COL3_X, BOTTOM_PANEL_H))

        self._draw_col1_controls(surf, sim)
        self._draw_col1_live_stats(surf, sim)
        self._draw_col2_fox_sliders(surf, sim.running)
        self._draw_col3_rabbit_sliders(surf, sim.running)

    def _draw_col1_controls(self, surf, sim):
        # Stolpec 1: kontrolni gumbi, izbira terena, preklopnik vizualizacije, drsnik radiča.
        running = sim.running

        for btn in (self.btn_start, self.btn_pause, self.btn_reset):
            btn.draw(surf, self.font_body)

        _text(surf, self.font_small, "Teren:", (PX, self._y_ter_lbl), LABEL)
        for btn in self.terrain_btns:
            btn.draw(surf, self.font_small)
        active_r = self.terrain_btns[self.cfg.terrain_type - 1].rect
        pygame.draw.rect(surf, ACCENT, active_r, 2, border_radius=5)

        self.btn_visual.draw(surf, self.font_small)
        self.slider_clover.draw(surf, self.font_small, sim_running=running)

    def _draw_col1_live_stats(self, surf, sim):
        # Stolpec 1 (spodaj): tabela živih povprečnih statistik za lisice in zajce.
        y_avgs = self._y_clover_bar + Slider.H + 14    # y koordinata začetka tabele statistik

        fox_stats    = self._calc_avg_stats(sim.foxes    if sim.running else [])
        rabbit_stats = self._calc_avg_stats(sim.rabbits  if sim.running else [])

        lbl_col_w = 68                                      # širina stolpca z oznakami vrstic
        val_col_w = (COL_W - PX * 2 - lbl_col_w) // 2     # širina vrednostnega stolpca za vsako vrsto
        x_fox = PX + lbl_col_w + val_col_w // 2            # x koordinata središča stolpca lisic
        x_rab = PX + lbl_col_w + val_col_w + val_col_w // 2    # x koordinata središča stolpca zajcev

        col_hdr_f = self.font_small.render("Lisica", True, GRAPH_FOX)
        col_hdr_r = self.font_small.render("Zajec",  True, GRAPH_RABBIT)
        surf.blit(col_hdr_f, (x_fox - col_hdr_f.get_width() // 2, y_avgs))
        surf.blit(col_hdr_r, (x_rab - col_hdr_r.get_width() // 2, y_avgs))
        y_avgs += col_hdr_f.get_height() + 3

        row_h = self.font_small.get_height() + 3   # višina ene vrstice tabele z razmakom
        for row_lbl, fv, rv, is_pct in [
            ("Starost",  fox_stats.get('age',    0.0), rabbit_stats.get('age',    0.0), False),
            ("Velikost", fox_stats.get('size',   0.0), rabbit_stats.get('size',   0.0), False),
            ("Lakota",   fox_stats.get('hunger', 0.0), rabbit_stats.get('hunger', 0.0), True),
            ("Žeja",     fox_stats.get('thirst', 0.0), rabbit_stats.get('thirst', 0.0), True),
            ("Hitrost",  fox_stats.get('speed',  0.0), rabbit_stats.get('speed',  0.0), False),
            ("Zaznava",  fox_stats.get('sense',  0.0), rabbit_stats.get('sense',  0.0), False),
        ]:
            ls = self.font_small.render(row_lbl + ":", True, TEXT_DIM)
            surf.blit(ls, (PX, y_avgs))

            fstr = f"{fv:.0f}%" if is_pct else f"{fv:.1f}"
            rstr = f"{rv:.0f}%" if is_pct else f"{rv:.1f}"

            fvs = self.font_small.render(fstr, True, GRAPH_FOX)
            rvs = self.font_small.render(rstr, True, GRAPH_RABBIT)
            surf.blit(fvs, (x_fox - fvs.get_width() // 2, y_avgs))
            surf.blit(rvs, (x_rab - rvs.get_width() // 2, y_avgs))
            y_avgs += row_h

        # Skupna rojstva od začetka simulacije
        ls  = self.font_small.render("Rojstva:", True, BIRTH_COLOR)
        surf.blit(ls, (PX, y_avgs))
        fvs = self.font_small.render(str(sim.births_fox),    True, GRAPH_FOX)
        rvs = self.font_small.render(str(sim.births_rabbit), True, GRAPH_RABBIT)
        surf.blit(fvs, (x_fox - fvs.get_width() // 2, y_avgs))
        surf.blit(rvs, (x_rab - rvs.get_width() // 2, y_avgs))

    def _calc_avg_stats(self, entities: list) -> dict:
        # Izračuna povprečne vrednosti lastnosti za seznam živali. Ločeno od risanja.
        if not entities:
            return {}
        n = len(entities)
        return {
            'age':    sum(e.age          for e in entities) / n,
            'size':   sum(e.size         for e in entities) / n,
            'hunger': sum(e.hunger       for e in entities) / n * 100,
            'thirst': sum(e.thirst       for e in entities) / n * 100,
            'speed':  sum(e.speed        for e in entities) / n,
            'sense':  sum(e.sense_radius for e in entities) / n,
        }

    def _draw_col2_fox_sliders(self, surf, running):
        # Stolpec 2: drsniki lastnosti lisice z naslovom.
        _draw_hdr(surf, COL2_X + PX, BOTTOM_Y + PY, COL_W - PX * 2,
                  "Lastnosti lisice  (plenilec)", self.font_h2, col=GRAPH_FOX)
        for sl in self.fox_sliders:
            sl.draw(surf, self.font_small, sim_running=running)

    def _draw_col3_rabbit_sliders(self, surf, running):
        # Stolpec 3: drsniki lastnosti zajca z naslovom.
        _draw_hdr(surf, COL3_X + PX, BOTTOM_Y + PY, COL_W - PX * 2,
                  "Lastnosti zajca  (plen)", self.font_h2, col=GRAPH_RABBIT)
        for sl in self.rabbit_sliders:
            sl.draw(surf, self.font_small, sim_running=running)

    # ── Vrstica mutacije ──────────────────────────────────────────────────────
    def _draw_mutation_bar(self):
        surf = self.screen
        pygame.draw.rect(surf, CARD_C, (0, MUT_Y, SCREEN_W, MUTATION_BAR_H))
        lbl = self.font_small.render("Mutacija", True, LABEL)
        surf.blit(lbl, (PX, MUT_Y + MUTATION_BAR_H // 2 - lbl.get_height() // 2))
        self.slider_mutation.draw(surf, self.font_small)

    # ── Kamera ────────────────────────────────────────────────────────────────
    def _update_camera(self, sim):
        # Premika kamero z WASD / smernimi tipkami.
        if not sim.running:
            return
        cfg   = self.cfg
        speed = cfg.cam_speed / cfg.FPS     # premik kamere na sličico
        keys  = self._keys_down
        if pygame.K_a   in keys or pygame.K_LEFT  in keys:
            cfg.cam_x = max(0, cfg.cam_x - speed)
        if pygame.K_d   in keys or pygame.K_RIGHT in keys:
            cfg.cam_x = min(cfg.MAP_W - SIM_W, cfg.cam_x + speed)
        if pygame.K_w   in keys or pygame.K_UP    in keys:
            cfg.cam_y = max(0, cfg.cam_y - speed)
        if pygame.K_s   in keys or pygame.K_DOWN  in keys:
            cfg.cam_y = min(cfg.MAP_H - SIM_H, cfg.cam_y + speed)