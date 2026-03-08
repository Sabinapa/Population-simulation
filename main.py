import tkinter as tk
from tkinter import ttk
import random


class Creature:
    def __init__(self, x, y, color, r_rate, s_rate, k_factor):
        self.x, self.y = x, y
        self.color = color
        self.r_rate = r_rate  # Reproduction probability
        self.s_rate = s_rate  # Death probability
        self.k_factor = k_factor  # Crowding constraint factor

    def move(self, width, height):
        self.x += random.uniform(-4, 4)
        self.y += random.uniform(-4, 4)
        self.x = max(5, min(width - 5, self.x))
        self.y = max(5, min(height - 5, self.y))


class SimulationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Population Control Panel")
        self.root.geometry("1100x800")
        self.root.configure(bg="white")

        self.is_running = False
        self.current_cycle = 0
        self.max_cycles = 600
        self.history = [[], [], []]
        self.colors = ["#007AFF", "#FF3B30", "#34C759"]  # Apple Blue, Red, Green

        self.setup_ui()

    def create_card(self, parent, title, title_color=None):
        """Helper function to create a white card with a shadow effect."""
        shadow = tk.Frame(parent, bg="#e1e1e1", bd=0)

        container = tk.Frame(shadow, bg="white", highlightthickness=1, highlightbackground="#d2d2d7", bd=0)
        container.pack(fill=tk.BOTH, expand=True, padx=(0, 2), pady=(0, 2))

        if title:
            fg_col = title_color if title_color else "#86868b"
            tk.Label(container, text=title, font=("Segoe UI Bold", 9), bg="white", fg=fg_col).pack(pady=5)

        return shadow, container

    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg="white", padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        header = tk.Label(main_frame, text="Nadzorna plošča populacij",
                          font=("Segoe UI Semibold", 20), bg="white", fg="#1d1d1f")
        header.pack(anchor="w", pady=(0, 25))

        center_frame = tk.Frame(main_frame, bg="white")
        center_frame.pack(fill=tk.BOTH, expand=True)

        # Simulation Card (Left)
        sim_shadow, self.sim_container = self.create_card(center_frame, "ŽIVI PRIKAZ")
        sim_shadow.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.BOTH)
        self.canvas_sim = tk.Canvas(self.sim_container, bg="white", highlightthickness=0, bd=0)
        self.canvas_sim.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Graph Card (Right)
        graph_shadow, self.graph_container = self.create_card(center_frame, "ANALITIKA CIKLOV")
        graph_shadow.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.BOTH)
        self.canvas_graph = tk.Canvas(self.graph_container, bg="white", highlightthickness=0, bd=0)
        self.canvas_graph.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Dynamic population counts under graph
        self.stats_frame = tk.Frame(self.graph_container, bg="white")
        self.stats_frame.pack(fill=tk.X, pady=(0, 10))
        self.pop_count_labels = []
        for i in range(3):
            lbl = tk.Label(self.stats_frame, text=f"Pop {i + 1}: 0", font=("Segoe UI Bold", 9), bg="white",
                           fg=self.colors[i])
            lbl.pack(side=tk.LEFT, expand=True)
            self.pop_count_labels.append(lbl)

        # Bottom section: Parameters
        param_container = tk.Frame(main_frame, bg="white", pady=25)
        param_container.pack(fill=tk.X)

        self.input_entries = []
        param_labels = ["st", "R", "S", "K"]
        defaults = [["20", "0.10", "0.05", "0.0005"],
                    ["20", "0.08", "0.04", "0.0006"],
                    ["20", "0.12", "0.06", "0.0004"]]

        for i in range(3):
            card_shadow, card_container = self.create_card(param_container, f"POPULACIJA {i + 1}", self.colors[i])
            card_shadow.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

            grid_frame = tk.Frame(card_container, bg="white")
            grid_frame.pack(pady=10)

            pop_inputs = {}
            for row_idx, label_text in enumerate(param_labels):
                tk.Label(grid_frame, text=label_text, bg="white", font=("Segoe UI", 8), fg="#424245").grid(row=0,
                                                                                                           column=row_idx * 2,
                                                                                                           padx=2)
                entry = tk.Entry(grid_frame, width=6, bg="#f5f5f7", relief="flat", justify="center")
                entry.insert(0, defaults[i][row_idx])
                entry.grid(row=0, column=row_idx * 2 + 1, padx=5)
                pop_inputs[label_text] = entry
            self.input_entries.append(pop_inputs)

        # Control Buttons
        ctrl_frame = tk.Frame(main_frame, bg="white")
        ctrl_frame.pack(fill=tk.X)

        self.btn_start = tk.Button(ctrl_frame, text="ZAŽENI", command=self.start_simulation,
                                   bg="#007AFF", fg="white", relief="flat", font=("Segoe UI Bold", 10),
                                   padx=30, pady=10, cursor="hand2")
        self.btn_start.pack(side=tk.LEFT, padx=10)

        self.btn_stop = tk.Button(ctrl_frame, text="USTAVI", command=self.stop_simulation,
                                  bg="#ff3b30", fg="white", relief="flat", font=("Segoe UI Bold", 10),
                                  padx=30, pady=10, cursor="hand2", state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT)

        self.lbl_info = tk.Label(ctrl_frame, text="Sistem pripravljen", font=("Segoe UI", 11), bg="white", fg="#86868b")
        self.lbl_info.pack(side=tk.RIGHT, padx=10)

    def draw_axes_and_legend(self):
        self.canvas_graph.delete("all")
        w, h = 480, 260
        ox, oy = 50, 220

        # Axes lines
        self.canvas_graph.create_line(ox, 20, ox, oy, fill="#d2d2d7")  # Y
        self.canvas_graph.create_line(ox, oy, w - 20, oy, fill="#d2d2d7")  # X

        # Y Ticks (Creature count)
        for i in range(0, 401, 100):
            y_pos = oy - (i * 0.5)
            self.canvas_graph.create_text(30, y_pos, text=str(i), fill="#86868b", font=("Segoe UI", 7))
            self.canvas_graph.create_line(ox - 3, y_pos, ox, y_pos, fill="#d2d2d7")

        # X Ticks (Cycles)
        for i in range(0, 601, 200):
            x_pos = ox + (i * (380 / 600))
            self.canvas_graph.create_text(x_pos, oy + 15, text=str(i), fill="#86868b", font=("Segoe UI", 7))
            self.canvas_graph.create_line(x_pos, oy, x_pos, oy + 3, fill="#d2d2d7")

    def start_simulation(self):
        self.is_running = True
        self.current_cycle = 0
        self.history = [[], [], []]
        self.populations = [[], [], []]
        self.btn_start.config(state=tk.DISABLED, bg="#d2d2d7")
        self.btn_stop.config(state=tk.NORMAL)

        for i in range(3):
            try:
                count = int(self.input_entries[i]["st"].get())
                r, s, k = float(self.input_entries[i]["R"].get()), float(self.input_entries[i]["S"].get()), float(
                    self.input_entries[i]["K"].get())
                for _ in range(count):
                    self.populations[i].append(
                        Creature(random.randint(10, 450), random.randint(10, 300), self.colors[i], r, s, k))
            except ValueError:
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
        total_count = 0

        for i in range(3):
            n = len(self.populations[i])
            total_count += n
            self.pop_count_labels[i].config(text=f"Pop {i + 1}: {n}")

            next_generation = []
            for c in self.populations[i]:
                c.move(480, 320)
                self.canvas_sim.create_oval(c.x - 2, c.y - 2, c.x + 2, c.y + 2, fill=c.color, outline="",
                                            tags="creatures")

                # Equation: Δ = R - S - K * N * N
                death_prob = c.s_rate + (c.k_factor * n)
                if random.random() > death_prob:
                    next_generation.append(c)
                    if random.random() < c.r_rate:
                        next_generation.append(Creature(c.x, c.y, c.color, c.r_rate, c.s_rate, c.k_factor))

            self.populations[i] = next_generation
            self.history[i].append(len(next_generation))

        self.draw_graph()
        self.lbl_info.config(text=f"Cikel: {self.current_cycle} | Skupaj: {total_count}")
        self.current_cycle += 1
        self.root.after(30, self.refresh)

    def draw_graph(self):
        self.draw_axes_and_legend()
        ox, oy = 50, 220
        step_x = 380 / self.max_cycles
        for i in range(3):
            if len(self.history[i]) < 2: continue
            points = []
            for cycle_idx, val in enumerate(self.history[i]):
                points.extend([ox + (cycle_idx * step_x), oy - (val * 0.5)])
            if len(points) >= 4:
                self.canvas_graph.create_line(points, fill=self.colors[i], width=2, smooth=True)


if __name__ == "__main__":
    root = tk.Tk()
    app = SimulationApp(root)
    root.mainloop()