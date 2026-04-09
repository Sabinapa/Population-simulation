import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import random
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

SAFE_ZONE = 40

class Creature:
    def __init__(self, x, y, speed, size, perception, energy):
        self.x, self.y = x, y
        self.speed = speed
        self.size = size
        self.perception = perception
        # strošek energije za premikanje: velikost^3 * hitrost^2 + zaznava, deljeno s faktorjem za uravnoteženje
        self.cost = (self.size ** 3 * self.speed ** 2 + self.perception) * 0.0001 # velikost3 * hitrost2 + zaznava
        self.max_energy = energy
        self.energy = energy
        self.food_eaten = 0
        self.is_dead = False
        self.has_returned = False
        self.angle = random.uniform(0, 2 * math.pi) # naključna začetna smer

    def move(self, width, height, foods, creatures):
        # Najprej preveri, ali je bitje mrtvo ali že vrnjeno
        if self.is_dead or self.has_returned: return

        self.energy -= self.cost

        # Preverjanje prezivetja
        if self.energy <= 0:
            self.is_dead = True
            return

        dx, dy = 0, 0
        found_target = False # hrana/plen

        # 1.PRIORITETA: bezanje pred večjimi plenilci
        for other in creatures:
            if other != self and not other.is_dead and other.size > self.size * 1.2: # bitje večje vsaj 20% je plenilec
                dist = math.hypot(self.x - other.x, self.y - other.y)
                if dist < self.perception: # če je plenilec v zaznavnem območju, nastavi smer bežanja
                    dx, dy = self.x - other.x, self.y - other.y
                    found_target = True
                    break

        # 2.PRIORITETA: iskanje hrane, če ni plenilcev v bližini
        if not found_target and self.food_eaten < 2:
            target_f = None
            min_d = self.perception # iščemo najbližjo hrano v zaznavnem območju
            for f in foods: # preveri vsako hrano (rastlinsko)
                d = math.hypot(self.x - f[0], self.y - f[1])
                if d < min_d: min_d, target_f = d, f # najbližji kos hrane

            # če je najdena hrana, izračunaj smer proti njej
            if target_f:
                dx, dy = target_f[0] - self.x, target_f[1] - self.y
                found_target = True
            else:
                # Ce ni hrane, išči manjše plenilce (bitja, ki jih lahko pojeste)
                for other in creatures:
                    if other != self and not other.is_dead and self.size > other.size * 1.2: # 20%
                        d = math.hypot(self.x - other.x, self.y - other.y)
                        if d < self.perception: # če je plen v zaznavnem območju, nastavi smer proti njemu
                            dx, dy = other.x - self.x, other.y - self.y
                            found_target = True
                            break

        # 3. PRIORITETA: vračanje DOMOV ali RANDOM HOJA
        if not found_target:
            if self.food_eaten >= 1: # 1 kos hrane vrača domov
                tx = 0 if self.x < width / 2 else width # levi ali desni rob
                dx, dy = tx - self.x, 0
            else:
                self.angle += random.uniform(-0.3, 0.3) # naključna sprememba smeri za raziskovanje
                dx, dy = math.cos(self.angle), math.sin(self.angle)

        # Premikanje bitja glede na izračunano smer
        dist = math.hypot(dx, dy)
        if dist > 0:
            # normaliziraj smer in premakni bitje glede na hitrost
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        # Varovalo (bitje ostane znotraj roba)
        self.x = max(self.size, min(width - self.size, self.x))
        self.y = max(self.size, min(height - self.size, self.y))

        # en ali več kos hrane in ce nahaja v SAFE ZONE
        if self.food_eaten >= 1:
            if self.x <= SAFE_ZONE or self.x >= width - SAFE_ZONE or self.y <= SAFE_ZONE or self.y >= height - SAFE_ZONE:
                self.has_returned = True

class EvolutionApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Evolucijski LAB")
        self.geometry("1500x950")
        self.running = False
        self.gen_count = 0
        self.creatures, self.foods = [], [] # seznam bitij in hrane
        # slovar za shranjevanje zgodovine generacij
        self.history = {"speed": [], # povprecna hitrost
                        "size": [], # povprecna velikost
                        "perc": [], # povprecna zaznava
                        "creatures": [], # stevilo prezivelih bitij
                        "food_start": [] # stevilo hrane na zacetku generacije
                        }
        self.sim_speed = 1
        self.current_food_n = 0
        self.setup_ui()

    def setup_ui(self):
        # Nastavitve mreze
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # SIMULACIJSKO OKNO (LEVI PANEL) okvir in platno
        self.sim_frame = ctk.CTkFrame(self, corner_radius=15)
        self.sim_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        self.canvas = tk.Canvas(self.sim_frame, bg="#0d0d0d", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)

        # DESNI PANEL (VEČJI GRAF + MANJŠA ANALITIKA)
        self.right_panel = ctk.CTkFrame(self, corner_radius=15)
        self.right_panel.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")

        # priprava prostora za graf
        self.fig, self.ax = plt.subplots(figsize=(4, 8), dpi=100)
        self.fig.patch.set_facecolor('#1a1a1a')
        self.ax.set_facecolor('#0d0d0d')
        # povezava grafa z uporabniskim vmesnikom (tkinter)
        self.canvas_graph = FigureCanvasTkAgg(self.fig, master=self.right_panel)
        self.canvas_graph.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # STATUS POD GRAFOM - prikaz trenutne generacije, stevila zivih bitij in hrane
        self.status_container = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.status_container.pack(pady=5, fill="x")

        self.lbl_gen = ctk.CTkLabel(self.status_container, text="Generacija: 0", font=("Arial", 16, "bold"), text_color="white")
        self.lbl_gen.pack(pady=2)
        self.lbl_alive = ctk.CTkLabel(self.status_container, text="Živih bitij: 0", font=("Arial", 16, "bold"), text_color="#00f2ff")
        self.lbl_alive.pack(pady=2)
        self.lbl_food = ctk.CTkLabel(self.status_container, text="Količina hrane: 0", font=("Arial", 16, "bold"), text_color="#2ecc71")
        self.lbl_food.pack(pady=2)

        # NADZORNA PLOŠČA (spodnji panel) - nastavitve simulacije in kontrola
        self.ctrl = ctk.CTkFrame(self, corner_radius=15)
        self.ctrl.grid(row=1, column=0, columnspan=2, padx=15, pady=15, sticky="nsew")
        for i in range(4): self.ctrl.grid_columnconfigure(i, weight=1)

        # 1. stolpec - nastavitve populacije in hrane ter scenarija
        self.p1 = ctk.CTkFrame(self.ctrl, fg_color="transparent")
        self.p1.grid(row=0, column=0, padx=10)
        self.inp_pop = self.add_entry(self.p1, "Št. bitij:", "30")
        self.inp_food = self.add_entry(self.p1, "Št. hrane:", "80")
        self.scen_var = ctk.StringVar(value="Konstantno")
        ctk.CTkOptionMenu(self.p1, variable=self.scen_var, values=["Konstantno", "Padajoče"]).pack(pady=10)

        # 2. stolpec - zacetna nastavitev hitrost in velikost
        self.p2 = ctk.CTkFrame(self.ctrl, fg_color="transparent")
        self.p2.grid(row=0, column=1, padx=10)
        self.sld_start_speed = self.add_slider(self.p2, "Zač. Hitrost:", 1, 15, 4.0)
        self.sld_start_size = self.add_slider(self.p2, "Zač. Velikost:", 2, 20, 7.0)

        # 3. stolpec - zacetna nastavitev zaznave in energije
        self.p3 = ctk.CTkFrame(self.ctrl, fg_color="transparent")
        self.p3.grid(row=0, column=2, padx=10)
        self.sld_start_perc = self.add_slider(self.p3, "Zač. Zaznava:", 10, 200, 50.0)
        self.sld_start_energy = self.add_slider(self.p3, "Zač. Energija:", 50, 500, 150.0)

        # 4. stolpec - kontrola simulacije (start/pause/reset) in hitrost simulacije
        self.p4 = ctk.CTkFrame(self.ctrl, fg_color="transparent")
        self.p4.grid(row=0, column=3, padx=10)
        self.btn_run = ctk.CTkButton(self.p4, text="START", fg_color="#2ecc71", command=self.toggle)
        self.btn_run.pack(pady=5, fill="x")
        ctk.CTkButton(self.p4, text="RESET", fg_color="#e74c3c", command=self.reset_all).pack(pady=5, fill="x")
        self.speed_label = ctk.CTkLabel(self.p4, text="Hitrost sim.: 1x")
        self.speed_label.pack()
        self.sld_sim_speed = ctk.CTkSlider(self.p4, from_=1, to=100, command=self.update_speed_label)
        self.sld_sim_speed.set(1)
        self.sld_sim_speed.pack()

    # funkcija za dodajanje vnosa (Entry)
    def add_entry(self, master, txt, default):
        f = ctk.CTkFrame(master, fg_color="transparent")
        f.pack(pady=2, fill="x")
        ctk.CTkLabel(f, text=txt, font=("Arial", 12)).pack(side="left")
        e = ctk.CTkEntry(f, width=60)
        e.insert(0, default)
        e.pack(side="right")
        return e

    # funkcija za drsnik z oznako
    def add_slider(self, master, txt, min_v, max_v, start_v):
        f = ctk.CTkFrame(master, fg_color="transparent")
        f.pack(pady=5, fill="x")
        lbl = ctk.CTkLabel(f, text=f"{txt} {start_v}", font=("Arial", 11))
        lbl.pack()
        s = ctk.CTkSlider(f, from_=min_v, to=max_v, number_of_steps=max_v - min_v)
        s.set(start_v)
        s.configure(command=lambda v: lbl.configure(text=f"{txt} {round(v, 1)}"))
        s.pack()
        return s

    def update_speed_label(self, v):
        self.sim_speed = int(v)
        self.speed_label.configure(text=f"Hitrost sim.: {self.sim_speed}x")

    # funkcija za zagon/pavzo simulacije
    def toggle(self):
        if not self.running:
            if not self.creatures: self.init_sim()
            if self.creatures:
                self.running = True
                self.btn_run.configure(text="PAVZA", fg_color="#f39c12")
                self.loop()
        else:
            self.running = False
            self.btn_run.configure(text="NADALJUJ", fg_color="#2ecc71")

    def reset_all(self):
        self.running = False
        self.gen_count = 0
        self.history = {k: [] for k in self.history}
        self.creatures, self.foods = [], []
        self.canvas.delete("all")
        self.btn_run.configure(text="START", fg_color="#2ecc71", state="normal")
        self.lbl_gen.configure(text="Generacija: 0")
        self.lbl_alive.configure(text="Živih bitij: 0")
        self.lbl_food.configure(text="Količina hrane: 0")
        self.update_plot()

    # incializacija simulacije - ustvarjanje začetne populacije in hrane
    def init_sim(self):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()

        # Ustvarjanje bitji glede na vnos
        try:
            for _ in range(int(self.inp_pop.get())):
                x, y = random.choice([20, w - 20]), random.uniform(20, h - 20) # naključna pozicija na levi ali desni strani

                # creature(x, y, hitrost, velikost, zaznava, energija)
                self.creatures.append(Creature(x, y,
                                               self.sld_start_speed.get(),
                                               self.sld_start_size.get(),
                                               self.sld_start_perc.get(),
                                               self.sld_start_energy.get()))
            self.spawn_food()
        except:
            messagebox.showerror("Napaka", "Preveri vnos števila bitij!")

    def spawn_food(self):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        n = int(self.inp_food.get()) # vpisano stevilo hrane

        # Padajoči scenarij do 10 pa za 1 manj vsakic
        if self.scen_var.get() == "Padajoče": n = max(10, n - self.gen_count)

        self.current_food_n = n
        self.lbl_food.configure(text=f"Količina hrane: {n}")

        # Ustvari seznam kooridnat [x, y] za kos hrane vstran od varne cone
        self.foods = [[random.uniform(SAFE_ZONE + 20, w - SAFE_ZONE - 20),
                       random.uniform(SAFE_ZONE + 20, h - SAFE_ZONE - 20)] for _ in range(n)]

    def loop(self):
        if not self.running: return

        # Pospesitev simulacije
        for _ in range(self.sim_speed):
            active = [c for c in self.creatures if not c.is_dead and not c.has_returned] # seznam zivih bitji
            alive_count = len([c for c in self.creatures if not c.is_dead]) # stevilo zivih bitij

            # Posodobita statusa generacije in stevila zivih bitij
            self.lbl_gen.configure(text=f"Generacija: {self.gen_count + 1}")
            self.lbl_alive.configure(text=f"Živih bitij: {alive_count}")

            # Ali so vsa bitja izumrla
            if not self.creatures or alive_count == 0:
                self.running = False
                self.canvas.create_text(self.canvas.winfo_width() / 2,
                                        self.canvas.winfo_height() / 2,
                                        text="POPULACIJA JE IZUMRLA",
                                        fill="red", font=("Arial", 30, "bold"))
                return

            # Ni aktivnith (ali jedli, vrnili ali umrli) - nova generacija
            if not active: self.next_gen(); break

            # Posodobi vsako bitje: premikanje, hranjenje in boj
            for c in active:
                c.move(self.canvas.winfo_width(), self.canvas.winfo_height(), self.foods, self.creatures) # premikanje bitja glede na okolico

                # Hranjenje rastlinsko
                for f in self.foods[:]:
                    if math.hypot(c.x - f[0], c.y - f[1]) < (c.size * 2.5) + 5: # ce je hrana v dosegu
                        c.food_eaten += 1
                        self.foods.remove(f)
                        self.lbl_food.configure(text=f"Količina hrane: {len(self.foods)}")

                # Hranjenje plenilsko - boj z manjšimi bitji
                for o in active:
                    # Bitje c vsaj 20% večje od o in v dosegu, potem c poje o
                    if o != c and c.size > o.size * 1.2 and math.hypot(c.x - o.x, c.y - o.y) < c.size:
                        c.food_eaten += 1
                        o.is_dead = True

        self.draw()
        self.after(15, self.loop)

    def next_gen(self):
        # Prezivijo samo bitja, ki so pojedla vsaj 1 kos hrane in se vrnila v varno cono
        survivors = [c for c in self.creatures if not c.is_dead and c.has_returned]

        # STATISTIKA povprecje njihovih lasnosti
        if survivors:
            self.history["speed"].append(sum(c.speed for c in survivors) / len(survivors))
            self.history["size"].append(sum(c.size for c in survivors) / len(survivors))
            self.history["perc"].append(sum(c.perception for c in survivors) / len(survivors))
            self.history["creatures"].append(len(survivors))
        else: # noben ni prezivel - zabeleži 0 in nadaljuj
            self.history["creatures"].append(0)

        # zacetna kolicina hrane
        self.history["food_start"].append(self.current_food_n)

        new_gen = []
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()

        # Razmnozevanje in mutacija
        for c in survivors:
            for _ in range(2 if c.food_eaten >= 2 else 1): # 2 kosa hrane ali vec dajejo 2 potomca, sicer 1
                m = 0.2 # faktor mutacije - 20% sprememba lastnosti

                # Potomec dobi lasnosti starša (hitrost velikost, zaznava) z naključno mutacijo do +/- 20%
                ns, nz, np = (max(0.5, c.speed + random.uniform(-m, m) * 1.5),
                              max(2, c.size + random.uniform(-m, m) * 2),
                              max(10, c.perception + random.uniform(-m, m) * 10))

                # Novo bitje na random poziciji z lasnostnimi potomca in polno energijo
                new_gen.append(
                    Creature(random.choice([20, w - 20]),
                             random.uniform(20, h - 20),
                             ns, nz, np,
                             c.max_energy))

        # Posodobitev sveta
        self.creatures = new_gen
        self.gen_count += 1
        self.spawn_food()
        self.update_plot()

    def update_plot(self):
        self.ax.clear()
        self.ax.set_facecolor('#0d0d0d')
        self.ax.grid(True, color="#333", linestyle="--", linewidth=0.5, alpha=0.4)

        for spine in self.ax.spines.values(): # barva robov grafa
            spine.set_color('#222')

        # Preveri zgodovino
        if self.history["speed"]:
            x = range(1, len(self.history["speed"]) + 1) # osi x - številke generacij

            # RISANJE črt za povprečno hitrost, velikost, zaznavo, število preživelih bitij in začetno količino hrane
            self.ax.plot(x, self.history["speed"], color="#00f2ff", label="Hitrost", linewidth=3.0)
            self.ax.plot(x, self.history["size"], color="#ff00ff", label="Velikost", linewidth=3.0)
            self.ax.plot(x, self.history["perc"], color="#ffff00", label="Zaznava", linewidth=3.0)
            self.ax.plot(x, self.history["creatures"], color="white", label="Populacija", linewidth=2.0, linestyle=":",alpha=1.0)
            self.ax.plot(x, self.history["food_start"], color="#2ecc71", label="Hrana", linewidth=1.5, alpha=0.6)

            # Legenda pod grafom
            self.ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3,
                           frameon=False, labelcolor='white',
                           fontsize=11, columnspacing=2.0, handlelength=2.5)

        self.ax.set_title("EVOLUCIJSKA ANALITIKA", color="white", fontname="Arial", weight="bold", pad=30) # naslov
        self.ax.tick_params(labelsize=9, colors='gray')
        self.fig.subplots_adjust(bottom=0.2, top=0.85)
        self.canvas_graph.draw() # osveži graf

    def draw(self):
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()

        # VARNA CONA izris
        self.canvas.create_rectangle(0, 0, w, SAFE_ZONE, fill="#1a1a1a", outline="")
        self.canvas.create_rectangle(0, h - SAFE_ZONE, w, h, fill="#1a1a1a", outline="")
        self.canvas.create_rectangle(0, 0, SAFE_ZONE, h, fill="#1a1a1a", outline="")
        self.canvas.create_rectangle(w - SAFE_ZONE, 0, w, h, fill="#1a1a1a", outline="")

        # IZRIS BITJI IN HRANE
        for f in self.foods: self.canvas.create_oval(f[0] - 4, f[1] - 4, f[0] + 4, f[1] + 4, fill="#2ecc71", outline="")
        for c in self.creatures:
            if not c.is_dead:
                # MODRA: isce hrano,
                # RDECA : gre v naslednjo generacijo
                col, v_sz = ("#3498db" if not c.has_returned else "#e91e63"), c.size * 2.5

                # ZAZNAVNA OBMOČJA - svetlejši krog okoli bitja, ki prikazuje njegovo zaznavo
                self.canvas.create_oval(c.x - c.perception, c.y - c.perception, c.x + c.perception, c.y + c.perception,outline="#333", width=1)

                # TELO BITJE
                self.canvas.create_oval(c.x - v_sz, c.y - v_sz, c.x + v_sz, c.y + v_sz, fill=col, outline="white",width=2)

                # ENERGIJSKA CRTA (koliko energije se ima)
                if not c.has_returned:
                    r = max(0, c.energy / c.max_energy) # razmerje preostale energije
                    self.canvas.create_line(c.x - v_sz, c.y - v_sz - 8, c.x - v_sz + (v_sz * 2 * r), c.y - v_sz - 8, fill="#e74c3c", width=4)

if __name__ == "__main__":
    app = EvolutionApp()
    app.mainloop()