import tkinter as tk
import random
import math

class Creature:
    def __init__(self, c_type, w, h):
        self.type = c_type  # 'Miroljubno' ali 'Agresivno'
        self.color = "#007AFF" if c_type == "Miroljubno" else "#FF3B30"
        self.w, self.h = w, h
        self.reset_to_edge()

        self.curr_x, self.curr_y = self.x, self.y #trenutna lokacija bitja
        self.target_x, self.target_y = self.x, self.y # hrana kam potuje

    # Bitja se vedno pojavijo na robu polja (NxM)
    def reset_to_edge(self):
        side = random.randint(0, 3)
        if side == 0:  # zgoraj
            self.x, self.y = random.randint(20, self.w - 20), 20
        elif side == 1:  # spodaj
            self.x, self.y = random.randint(20, self.w - 20), self.h - 20
        elif side == 2:  # levo
            self.x, self.y = 20, random.randint(20, self.h - 20)
        else:  # desno
            self.x, self.y = self.w - 20, random.randint(20, self.h - 20)
        self.curr_x, self.curr_y = self.x, self.y # animacija začne s te točke


class SimulationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Naloga 2: Teorija Iger - Evolucijsko ravnovesje")
        self.root.geometry("1250x850")
        self.root.configure(bg="#F0F2F5")

        self.width, self.height = 700, 500
        self.animating = False
        self.reset_data()
        self.setup_ui()

    def reset_data(self):
        self.history = {"Miroljubno": [], "Agresivno": []}
        self.creatures = []
        self.gen_num = 0
        self.food_spots = []

    def setup_ui(self):
        header = tk.Label(self.root, text="Simulacija: Miroljubna vs Agresivna bitja",
                          font=("Segoe UI", 20, "bold"), bg="#F0F2F5", fg="#1C1E21")
        header.pack(pady=10)

        main_frame = tk.Frame(self.root, bg="#F0F2F5")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        # LEVO: Polje
        left_panel = tk.Frame(main_frame, bg="white", bd=2, relief="groove")
        left_panel.pack(side=tk.LEFT, padx=10, pady=10)

        self.canvas_sim = tk.Canvas(left_panel, width=self.width, height=self.height, bg="#FAFAFA",
                                    highlightthickness=0)
        self.canvas_sim.pack(padx=5, pady=5)

        # DESNO: Graf in kontrole
        right_panel = tk.Frame(main_frame, bg="#F0F2F5")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Graf
        graph_card = tk.Frame(right_panel, bg="white", bd=1, relief="solid")
        graph_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Label(graph_card, text="Prikaz populacije skozi generacije", bg="white", font=("Segoe UI", 10, "bold")).pack(
            pady=5)
        self.canvas_graph = tk.Canvas(graph_card, width=450, height=350, bg="white", highlightthickness=0)
        self.canvas_graph.pack(padx=10, pady=10)

        # Kontrole
        ctrl_card = tk.LabelFrame(right_panel, text=" Nastavitve in nadzor ", bg="white", padx=15, pady=15)
        ctrl_card.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(ctrl_card, text="Začetno št. miroljubnih:").grid(row=0, column=0, sticky="w")
        self.ent_mir = tk.Entry(ctrl_card, width=10)
        self.ent_mir.insert(0, "20")
        self.ent_mir.grid(row=0, column=1, pady=5)

        tk.Label(ctrl_card, text="Začetno št. agresivnih:").grid(row=1, column=0, sticky="w")
        self.ent_agr = tk.Entry(ctrl_card, width=10)
        self.ent_agr.insert(0, "5")
        self.ent_agr.grid(row=1, column=1, pady=5)

        tk.Label(ctrl_card, text="Število parov hrane:").grid(row=2, column=0, sticky="w")
        self.ent_food = tk.Entry(ctrl_card, width=10)
        self.ent_food.insert(0, "30")
        self.ent_food.grid(row=2, column=1, pady=5)

        self.btn_next = tk.Button(right_panel, text="IZVEDI GENERACIJO (Z ANIMACIJO)", command=self.start_generation,
                                  bg="#1877F2", fg="white", font=("Segoe UI", 12, "bold"), pady=12, relief="flat")
        self.btn_next.pack(fill=tk.X, padx=10, pady=5)

        self.btn_reset = tk.Button(right_panel, text="PONASTAVI SIMULACIJO", command=self.reset_simulation,
                                   bg="#DC3545", fg="white", font=("Segoe UI", 10, "bold"), pady=8, relief="flat")
        self.btn_reset.pack(fill=tk.X, padx=10, pady=5)

        # Statistično besedilo spodaj
        self.lbl_stats = tk.Label(right_panel, text="Pripravljeno na simulacijo", font=("Segoe UI", 11, "bold"),
                                  bg="#F0F2F5", fg="#1C1E21")
        self.lbl_stats.pack(pady=15)

    def reset_simulation(self):
        self.reset_data()
        self.canvas_sim.delete("all")
        self.canvas_graph.delete("all")
        self.lbl_stats.config(text="Resetirano. Vpišite nove vrednosti.")

    def start_generation(self):
        if self.animating: return # preprečimo večkratni klik med animacijo

        # vpis hrane
        try:
            food_count = int(self.ent_food.get())
        except:
            food_count = 30

        # Prva generacija - ustvarimo bitja glede na vnos
        if not self.creatures and self.gen_num == 0:
            try:
                n_mir = int(self.ent_mir.get())
                n_agr = int(self.ent_agr.get())
                for _ in range(n_mir): self.creatures.append(Creature("Miroljubno", self.width, self.height))
                for _ in range(n_agr): self.creatures.append(Creature("Agresivno", self.width, self.height))
            except:
                return

        for c in self.creatures: c.reset_to_edge() # bitja na rob

        # Ustvarimo naključne točke hrane
        self.food_spots = [(random.randint(150, self.width - 150), random.randint(100, self.height - 100))
                           for _ in range(food_count)]

        # Bitja premešamo kdor prvi pride do hrane
        random.shuffle(self.creatures)
        self.occupancy = [[] for _ in range(food_count)] # Hrana gosti 2 bitja

        c_ptr = 0
        radius = 25
        for f_idx in range(food_count):
            potential_visitors = []
            for _ in range(2): # 2 bitji na par hrane
                if c_ptr < len(self.creatures):
                    potential_visitors.append(self.creatures[c_ptr])
                    c_ptr += 1
            self.occupancy[f_idx] = potential_visitors

            for i, c in enumerate(potential_visitors): # Lepša postavitev bitij okoli hrane
                angle = math.radians(90) if len(potential_visitors) == 1 else math.radians(45 + i * 180)
                c.target_x = self.food_spots[f_idx][0] + radius * math.cos(angle)
                c.target_y = self.food_spots[f_idx][1] - radius * math.sin(angle)

        self.animating = True
        self.animate_move(0)

    def animate_move(self, step):
        if step < 20:
            self.canvas_sim.delete("all")
            self.draw_static_elements()
            for pair in self.occupancy:
                for c in pair:
                    dx = (c.target_x - c.x) / 20
                    dy = (c.target_y - c.y) / 20
                    c.curr_x = c.x + dx * step
                    c.curr_y = c.y + dy * step
                    self.canvas_sim.create_oval(c.curr_x - 8, c.curr_y - 8, c.curr_x + 8, c.curr_y + 8, fill=c.color, outline="white", width=1)
            self.root.after(30, lambda: self.animate_move(step + 1))
        else:
            self.animating = False
            self.finish_generation()

    def draw_static_elements(self):
        # Mreža (vodoravne in navpične črte)
        for i in range(0, self.width, 50): self.canvas_sim.create_line(i, 0, i, self.height, fill="#EEEEEE")
        for j in range(0, self.height, 50): self.canvas_sim.create_line(0, j, self.width, j, fill="#EEEEEE")
        # hrana (dva kosa hrane na enem mestu)
        for fx, fy in self.food_spots:
            self.canvas_sim.create_oval(fx - 10, fy - 5, fx - 2, fy + 5, fill="#FFD700", outline="#B8860B")
            self.canvas_sim.create_oval(fx + 2, fy - 5, fx + 10, fy + 5, fill="#FFD700", outline="#B8860B")

    def finish_generation(self):
        # Izračunamo preživele bitja za naslednjo generacijo
        next_gen = []
        for pair in self.occupancy:
            if len(pair) == 1:
                c = pair[0]
                next_gen.append(Creature(c.type, self.width, self.height)) # Preživi
                next_gen.append(Creature(c.type, self.width, self.height)) # Se razmnoži
            elif len(pair) == 2:
                c1, c2 = pair[0], pair[1]
                if c1.type == "Miroljubno" and c2.type == "Miroljubno": # oba preživita in se razmnožita
                    next_gen.append(Creature("Miroljubno", self.width, self.height))
                    next_gen.append(Creature("Miroljubno", self.width, self.height))
                elif c1.type == "Agresivno" and c2.type == "Agresivno": # Spor - oba umreta, noben ne preživi
                    pass
                else:
                    # 1. Ugotovimo, kdo je kdo
                    mir_bitje = c1 if c1.type == "Miroljubno" else c2
                    agr_bitje = c1 if c1.type == "Agresivno" else c2

                    # 2. Agresivno bitje vedno preživi
                    next_gen.append(Creature(agr_bitje.type, self.width, self.height))

                    # 3. 50% možnosti za potomca agresivnega
                    if random.random() < 0.5:
                        next_gen.append(Creature(agr_bitje.type, self.width, self.height))

                    # 4. 50% možnosti, da miroljubno bitje preživi
                    if random.random() < 0.5:
                        next_gen.append(Creature(mir_bitje.type, self.width, self.height))

        # Statistika TRENUTNEGA stanja
        m_at_food = sum(1 for p in self.occupancy for c in p if c.type == "Miroljubno")
        a_at_food = sum(1 for p in self.occupancy for c in p if c.type == "Agresivno")

        # Shranimo v zgodovino
        self.history["Miroljubno"].append(m_at_food)
        self.history["Agresivno"].append(a_at_food)
        self.gen_num += 1

        # Posodobi graf in statistiko
        self.draw_graph()
        self.lbl_stats.config(
            text=f"Generacija: {self.gen_num} | Miroljubni na polju: {m_at_food} | Agresivni na polju: {a_at_food}")

        # Pripravimo bitja za naslednji klik
        self.creatures = next_gen

    def draw_graph(self):
        self.canvas_graph.delete("all")
        w, h, ox, oy = 450, 350, 65, 310

        # OSI
        self.canvas_graph.create_line(ox, 20, ox, oy, width=2, fill="#333333")
        self.canvas_graph.create_line(ox, oy, w - 20, oy, width=2, fill="#333333")
        self.canvas_graph.create_text(ox - 45, 20, text="Populacija", anchor="w", font=("Arial", 9, "bold"))
        self.canvas_graph.create_text(w - 35, oy + 20, text="Gen", font=("Arial", 9, "bold"))

        if not self.history["Miroljubno"]: return

        # Merilo za graf
        curr_max = max(max(self.history["Miroljubno"] + self.history["Agresivno"] + [10]), 50)
        num_gens = len(self.history["Miroljubno"])
        dx = (w - ox - 40) / max(len(self.history["Miroljubno"]), 15)
        dy = (oy - 40) / curr_max

        # 1. Številke na Y osi (Populacija)
        for i in range(5):
            val = int(i * curr_max / 4)
            y_pos = oy - (val * dy)
            self.canvas_graph.create_text(ox - 10, y_pos, text=str(val), anchor="e", font=("Arial", 7))
            self.canvas_graph.create_line(ox, y_pos, ox + 5, y_pos, fill="#333333")

        # 2. Številke na X osi (Generacije)
        step_x = 5 if num_gens > 20 else 2
        if num_gens > 50: step_x = 10
        for g in range(0, num_gens, step_x):
            px = ox + g * dx
            self.canvas_graph.create_text(px, oy + 12, text=str(g + 1), anchor="n", font=("Arial", 7),fill="#555555")
            self.canvas_graph.create_line(px, oy, px, oy - 4, fill="#333333")

        # 3. Linije in točke za obe vrsti bitij
        for t in ["Miroljubno", "Agresivno"]:
            color = "#007AFF" if t == "Miroljubno" else "#FF3B30"
            pts = []
            for i, val in enumerate(self.history[t]):
                px = ox + i * dx
                py = oy - val * dy
                pts.extend([px, py])
                self.canvas_graph.create_oval(px - 3, py - 3, px + 3, py + 3, fill=color, outline="white") # Točka na grafu

            if len(pts) >= 4:
                self.canvas_graph.create_line(pts, fill=color, width=3, smooth=True)

        # Legenda
        self.canvas_graph.create_rectangle(w - 100, 30, w - 90, 40, fill="#007AFF")
        self.canvas_graph.create_text(w - 85, 35, text="Miroljubni", anchor="w", font=("Arial", 8))
        self.canvas_graph.create_rectangle(w - 100, 50, w - 90, 60, fill="#FF3B30")
        self.canvas_graph.create_text(w - 85, 55, text="Agresivni", anchor="w", font=("Arial", 8))


if __name__ == "__main__":
    root = tk.Tk()
    app = SimulationApp(root)
    root.mainloop()