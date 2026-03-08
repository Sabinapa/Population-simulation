import tkinter as tk
from tkinter import ttk
import random


class Creature:
    def __init__(self, x, y, color, r_rate, s_rate, k_factor):
        self.x, self.y = x, y
        self.color = color
        self.r_rate = r_rate  # Verjetnost razmnoževanja
        self.s_rate = s_rate  # Verjetnost smrti
        self.k_factor = k_factor  # Koeficient omejitve

    def move(self, width, height):
        self.x += random.uniform(-5, 5)
        self.y += random.uniform(-5, 5)
        # Mehak odmik od robov, da bitja niso odrezana
        self.x = max(10, min(width - 10, self.x))
        self.y = max(10, min(height - 10, self.y))


class SimulationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Population Analytics Pro")
        self.root.geometry("1200x850")
        self.root.configure(bg="#F5F5F7")  # Apple-style siva

        self.is_running = False
        self.current_cycle = 0
        self.max_cycles = 600
        self.history = [[], [], []]
        self.colors = ["#007AFF", "#FF3B30", "#34C759"]  # Moderna modra, rdeča, zelena

        self.setup_ui()

    def create_card(self, parent, title, title_color=None):
        """Ustvari belo kartico z efektom sence in zaobljenim vtisom."""
        # Zunanji okvir za senco
        shadow = tk.Frame(parent, bg="#D1D1D6", bd=0)

        # Notranji beli vsebnik
        container = tk.Frame(shadow, bg="white", bd=0)
        container.pack(fill=tk.BOTH, expand=True, padx=(0, 1), pady=(0, 1))

        if title:
            fg_col = title_color if title_color else "#8E8E93"
            tk.Label(container, text=title, font=("Segoe UI Bold", 10),
                     bg="white", fg=fg_col).pack(pady=(10, 5))

        return shadow, container

    def setup_ui(self):
        # Glavni vsebnik z odmiki
        main_frame = tk.Frame(self.root, bg="#F5F5F7", padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        header = tk.Label(main_frame, text="Nadzorna plošča populacij",
                          font=("Segoe UI Semibold", 22), bg="#F5F5F7", fg="#1D1D1F")
        header.pack(anchor="w", pady=(0, 25))

        # Osrednji del s karticami
        center_frame = tk.Frame(main_frame, bg="#F5F5F7")
        center_frame.pack(fill=tk.BOTH, expand=True)

        # Kartica za Simulacijo (Levo)
        sim_shadow, self.sim_container = self.create_card(center_frame, "ŽIVI PRIKAZ")
        sim_shadow.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.BOTH)

        self.canvas_sim = tk.Canvas(self.sim_container, bg="white", highlightthickness=0, bd=0)
        self.canvas_sim.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Kartica za Graf (Desno)
        graph_shadow, self.graph_container = self.create_card(center_frame, "ANALITIKA CIKLOV")
        graph_shadow.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.BOTH)

        self.canvas_graph = tk.Canvas(self.graph_container, bg="white", highlightthickness=0, bd=0)
        self.canvas_graph.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Dinamični števci pod grafom
        self.stats_frame = tk.Frame(self.graph_container, bg="white")
        self.stats_frame.pack(fill=tk.X, pady=(0, 15))
        self.pop_count_labels = []
        for i in range(3):
            lbl = tk.Label(self.stats_frame, text=f"Pop {i + 1}: 0",
                           font=("Segoe UI Bold", 10), bg="white", fg=self.colors[i])
            lbl.pack(side=tk.LEFT, expand=True)
            self.pop_count_labels.append(lbl)

        # Spodnji del: Parametri
        param_container = tk.Frame(main_frame, bg="#F5F5F7", pady=20)
        param_container.pack(fill=tk.X)

        self.input_entries = []
        labels = ["st", "R", "S", "K"]
        defaults = [["25", "0.10", "0.05", "0.0005"],
                    ["25", "0.08", "0.04", "0.0006"],
                    ["25", "0.12", "0.06", "0.0004"]]

        for i in range(3):
            card_sh, card_cont = self.create_card(param_container, f"POPULACIJA {i + 1}", self.colors[i])
            card_sh.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

            grid_f = tk.Frame(card_cont, bg="white")
            grid_f.pack(pady=15, padx=10)

            pop_in = {}
            for idx, txt in enumerate(labels):
                tk.Label(grid_f, text=txt, bg="white", font=("Segoe UI", 9), fg="#424245").grid(row=0, column=idx * 2)
                e = tk.Entry(grid_f, width=6, bg="#F5F5F7", relief="flat", justify="center", font=("Segoe UI", 10))
                e.insert(0, defaults[i][idx])
                e.grid(row=0, column=idx * 2 + 1, padx=6)
                pop_in[txt] = e
            self.input_entries.append(pop_in)

        # Kontrole
        ctrl_frame = tk.Frame(main_frame, bg="#F5F5F7")
        ctrl_frame.pack(fill=tk.X, pady=(10, 0))

        self.btn_start = tk.Button(ctrl_frame, text="ZAŽENI", command=self.start_simulation,
                                   bg="#007AFF", fg="white", relief="flat", font=("Segoe UI Bold", 11),
                                   padx=40, pady=12, cursor="hand2")
        self.btn_start.pack(side=tk.LEFT, padx=10)

        self.btn_stop = tk.Button(ctrl_frame, text="USTAVI", command=self.stop_simulation,
                                  bg="#FF3B30", fg="white", relief="flat", font=("Segoe UI Bold", 11),
                                  padx=40, pady=12, cursor="hand2", state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT)

        self.lbl_info = tk.Label(ctrl_frame, text="Sistem pripravljen", font=("Segoe UI", 12),
                                 bg="#F5F5F7", fg="#86868B")
        self.lbl_info.pack(side=tk.RIGHT, padx=10)

    def draw_axes(self):
        """Izriše osi glede na trenutno velikost platna, da ni odrezano."""
        self.canvas_graph.delete("all")
        w = self.canvas_graph.winfo_width()
        h = self.canvas_graph.winfo_height()

        ox, oy = 50, h - 40  # Izvor osi

        # Osi
        self.canvas_graph.create_line(ox, 20, ox, oy, fill="#D1D1D6", width=1)  # Y
        self.canvas_graph.create_line(ox, oy, w - 20, oy, fill="#D1D1D6", width=1)  # X

        # Y Oznake (Populacija)
        max_pop = 400
        for i in range(0, max_pop + 1, 100):
            y_pos = oy - (i * (oy - 40) / max_pop)
            self.canvas_graph.create_text(30, y_pos, text=str(i), fill="#8E8E93", font=("Segoe UI", 8))
            self.canvas_graph.create_line(ox - 4, y_pos, ox, y_pos, fill="#D1D1D6")

        # X Oznake (Cikli)
        for i in range(0, self.max_cycles + 1, 200):
            x_pos = ox + (i * (w - ox - 40) / self.max_cycles)
            self.canvas_graph.create_text(x_pos, oy + 20, text=str(i), fill="#8E8E93", font=("Segoe UI", 8))
            self.canvas_graph.create_line(x_pos, oy, x_pos, oy + 4, fill="#D1D1D6")

    def start_simulation(self):
        self.is_running = True
        self.current_cycle = 0
        self.history = [[], [], []]
        self.populations = [[], [], []]
        self.btn_start.config(state=tk.DISABLED, bg="#D1D1D6")
        self.btn_stop.config(state=tk.NORMAL)

        for i in range(3):
            try:
                count = int(self.input_entries[i]["st"].get())
                r, s, k = float(self.input_entries[i]["R"].get()), float(self.input_entries[i]["S"].get()), float(
                    self.input_entries[i]["K"].get())
                w = self.canvas_sim.winfo_width()
                h = self.canvas_sim.winfo_height()
                for _ in range(count):
                    self.populations[i].append(
                        Creature(random.randint(20, w - 20), random.randint(20, h - 20), self.colors[i], r, s, k))
            except:
                self.stop_simulation()
                return
        self.refresh()

    def stop_simulation(self):
        self.is_running = False
        self.btn_start.config(state=tk.NORMAL, bg="#007AFF")
        self.btn_stop.config(state=tk.DISABLED)
        self.lbl_info.config(text="Simulacija ustavljena")

    def refresh(self):
        if not self.is_running or self.current_cycle >= self.max_cycles:
            self.stop_simulation()
            return

        self.canvas_sim.delete("creatures")
        width_sim = self.canvas_sim.winfo_width()
        height_sim = self.canvas_sim.winfo_height()
        total_count = 0

        for i in range(3):
            # n predstavlja N v enačbi (trenutno število bitij te populacije)
            n = len(self.populations[i])
            total_count += n
            self.pop_count_labels[i].config(text=f"Pop {i + 1}: {n}")

            next_generation = []

            # Implementacija enačbe: Delta = R - S - K * N * N
            # V simulaciji to pomeni, da se verjetnost smrti poveča za faktor K * N
            for c in self.populations[i]:
                c.move(width_sim, height_sim)
                self.canvas_sim.create_oval(c.x - 3, c.y - 3, c.x + 3, c.y + 3,
                                            fill=c.color, outline="", tags="creatures")

                # Pogoj smrti nadgradimo glede na količino bitij (N)
                # Verjetnost smrti = S + K * N
                death_probability = c.s_rate + (c.k_factor * n)

                if random.random() > death_probability:
                    # Bitje preživi cikel
                    next_generation.append(c)

                    # Verjetnost razmnoževanja ostane R
                    if random.random() < c.r_rate:
                        next_generation.append(Creature(c.x, c.y, c.color, c.r_rate, c.s_rate, c.k_factor))

            self.populations[i] = next_generation
            self.history[i].append(len(next_generation))

        self.draw_graph()
        self.lbl_info.config(text=f"Cikel: {self.current_cycle} | Skupaj: {total_count}")
        self.current_cycle += 1
        self.root.after(30, self.refresh)

    def draw_graph(self):
        self.draw_axes()
        w = self.canvas_graph.winfo_width()
        h = self.canvas_graph.winfo_height()
        ox, oy = 50, h - 40

        max_pop = 400
        step_x = (w - ox - 40) / self.max_cycles
        step_y = (oy - 40) / max_pop

        for i in range(3):
            if len(self.history[i]) < 2: continue
            points = []
            for cycle_idx, val in enumerate(self.history[i]):
                x = ox + (cycle_idx * step_x)
                y = oy - (val * step_y)
                points.extend([x, y])

            if len(points) >= 4:
                self.canvas_graph.create_line(points, fill=self.colors[i], width=2, smooth=True)


if __name__ == "__main__":
    root = tk.Tk()
    # Zagotovimo, da se okno najprej izriše, da dobimo pravilne dimenzije platna
    root.update()
    app = SimulationApp(root)
    root.mainloop()