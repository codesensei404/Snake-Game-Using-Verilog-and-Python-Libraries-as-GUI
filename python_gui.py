import tkinter as tk
from tkinter import messagebox
import random
import os
import subprocess
import json

BOARD_SIZE = 20  
CELL_SIZE = 30
GAME_SPEED_MS = 100  


VERILOG_SOURCE = "snake_logic.v"
VERILOG_TESTBENCH = "snake_tb.v"
VERILOG_OUTPUT_FILE = "verilog_output.txt"
VERILOG_EXEC_FILE = "snake_logic_compiled"
VCD_FILE = "snake_waves.vcd"

DIR_VERILOG_MAP = {
    "North": 0b00,
    "East": 0b01,
    "South": 0b10,
    "West": 0b11
}

class GameState:
    def __init__(self):
        self.snake1 = []
        self.direction1 = "East"
        self.score1 = 0

        self.snake2 = []
        self.direction2 = "West"
        self.score2 = 0
        
        self.food = None
        self.is_running = False
        self.high_score = self._load_high_score()
        self.last_score = 0
        self.game_mode = "Single Player" 
        self.game_timer = None 
        self.root = None 

    def _generate_food(self):
        active_snakes = self.snake1
        if self.game_mode == "Two Player":
            active_snakes.extend(self.snake2)

        while True:
            x = random.randint(0, BOARD_SIZE - 1)
            y = random.randint(0, BOARD_SIZE - 1)
            if (x, y) not in active_snakes:
                return (x, y)

    def _load_high_score(self):
        try:
            with open("snake_scores.json", "r") as f:
                data = json.load(f)
                return data.get("high_score", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            return 0

    def _save_high_score(self):
        with open("snake_scores.json", "w") as f:
            json.dump({"high_score": self.high_score}, f)

    def reset_game(self):
        combined_score = self.score1 + self.score2
        self.last_score = combined_score
        
        if combined_score > self.high_score:
            self.high_score = combined_score
            self._save_high_score()

        self.snake1 = [(3, 5)] 
        self.direction1 = "East"
        self.score1 = 0

        if self.game_mode == "Two Player":
            self.snake2 = [(BOARD_SIZE - 4, BOARD_SIZE - 6)]
            self.direction2 = "West"
            self.score2 = 0
        else:
            self.snake2 = []
            self.direction2 = "West"
            self.score2 = 0 
        
        self.food = self._generate_food()
        self.is_running = False
        
        if self.game_timer:
            self.root.after_cancel(self.game_timer)

class SnakeGame(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Verilog Snake (Mode Selector)")
        self.state = GameState()
        self.state.root = self
        self.mode_var = tk.StringVar(value=self.state.game_mode) 
        self.mode_var.trace_add("write", self._on_mode_change)
        self._configure_styles()
        self._create_widgets()
        self._bind_keys()
        self.state.reset_game() 
        self._compile_verilog() 

    def _configure_styles(self):
        self.configure(bg="#2d2d2d")
        self.option_add('*Font', 'Inter 10')
        self.option_add('*Button.activeBackground', '#5c5c5c')
        self.option_add('*Button.activeForeground', 'white')
        self.option_add('*Radiobutton.background', '#2d2d2d')
        self.option_add('*Radiobutton.foreground', 'white')

    def _on_mode_change(self, *args):
        new_mode = self.mode_var.get()
        if self.state.game_mode != new_mode:
            self.stop_game()
            self.state.game_mode = new_mode
            self.state.reset_game()
            self._draw_game()
            self._update_dashboard()
            self._bind_keys() 

    def _create_widgets(self):

        main_frame = tk.Frame(self, bg="#2d2d2d", padx=10, pady=10)
        main_frame.pack(expand=True, fill='both')
        
        dashboard_frame = tk.Frame(main_frame, bg="#3c3c3c", pady=5, padx=10, relief=tk.RAISED, bd=3)
        dashboard_frame.pack(fill='x', pady=(0, 10))

        self.score1_label = tk.Label(dashboard_frame, text="P1 Score: 0", fg="#4CAF50", bg="#3c3c3c", font="Inter 14 bold")
        self.score1_label.pack(side=tk.LEFT, padx=10)

        self.score2_label = tk.Label(dashboard_frame, text="P2 Score: 0", fg="#2196F3", bg="#3c3c3c", font="Inter 14 bold")
        self.score2_label.pack(side=tk.LEFT, padx=30)

        self.high_score_label = tk.Label(dashboard_frame, text=f"High: {self.state.high_score}", fg="#E91E63", bg="#3c3c3c", font="Inter 10")
        self.high_score_label.pack(side=tk.RIGHT, padx=10)

        self.last_score_label = tk.Label(dashboard_frame, text=f"Last: {self.state.last_score}", fg="#FFEB3B", bg="#3c3c3c", font="Inter 10")
        self.last_score_label.pack(side=tk.RIGHT, padx=10)
        
        mode_frame = tk.Frame(main_frame, bg="#2d2d2d", pady=5)
        mode_frame.pack(fill='x')
        
        tk.Label(mode_frame, text="Game Mode:", bg="#2d2d2d", fg="white", font="Inter 10 bold").pack(side=tk.LEFT, padx=(5, 10))

        tk.Radiobutton(mode_frame, text="Single Player (P1 Only)", variable=self.mode_var, value="Single Player").pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(mode_frame, text="Two Player (Co-op/Vs)", variable=self.mode_var, value="Two Player").pack(side=tk.LEFT, padx=5)


        canvas_width = BOARD_SIZE * CELL_SIZE
        canvas_height = BOARD_SIZE * CELL_SIZE
        self.canvas = tk.Canvas(main_frame, width=canvas_width, height=canvas_height, bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack()


        control_frame = tk.Frame(main_frame, bg="#2d2d2d", pady=10)
        control_frame.pack(fill='x')


        btn_style = {'bg': '#007BFF', 'fg': 'white', 'font': 'Inter 10 bold', 'width': 12, 'relief': tk.RAISED, 'bd': 2}
        
        self.start_btn = tk.Button(control_frame, text="Start Game", command=self.start_game, **btn_style)
        self.start_btn.pack(side=tk.LEFT, padx=5, expand=True)

        stop_btn_style = btn_style.copy()
        stop_btn_style['bg'] = '#dc3545'

        self.stop_btn = tk.Button(control_frame, text="Stop Game", command=self.stop_game, **stop_btn_style)
        self.stop_btn.pack(side=tk.LEFT, padx=5, expand=True)

        waves_btn_style = btn_style.copy()
        waves_btn_style['bg'] = '#6c757d'

        self.waves_btn = tk.Button(control_frame, text="Show EPWaves", command=self.show_gtkwave, **waves_btn_style)
        self.waves_btn.pack(side=tk.LEFT, padx=5, expand=True)

        self._draw_game()
        self._update_dashboard()

    def _bind_keys(self):
        for key in ['<Up>', '<Down>', '<Left>', '<Right>', 'w', 's', 'a', 'd']:
            self.unbind(key)
        
        self.bind('<Up>', lambda e: self.change_direction("snake1", "North"))
        self.bind('<Down>', lambda e: self.change_direction("snake1", "South"))
        self.bind('<Left>', lambda e: self.change_direction("snake1", "West"))
        self.bind('<Right>', lambda e: self.change_direction("snake1", "East"))
        
        if self.state.game_mode == "Two Player":
            self.bind('w', lambda e: self.change_direction("snake2", "North"))
            self.bind('s', lambda e: self.change_direction("snake2", "South"))
            self.bind('a', lambda e: self.change_direction("snake2", "West"))
            self.bind('d', lambda e: self.change_direction("snake2", "East"))
        
        self.bind('<space>', lambda e: self.start_game()) 

    def _compile_verilog(self):
        """Compiles the Verilog module using iverilog."""
        try:
            compile_cmd = ['iverilog', '-o', VERILOG_EXEC_FILE, VERILOG_SOURCE]
            subprocess.run(compile_cmd, check=True, capture_output=True)
            print(f"Verilog compiled successfully to {VERILOG_EXEC_FILE}")
        except FileNotFoundError:
            print("Error: 'iverilog' not found. Please ensure Icarus Verilog is installed and in your PATH.")
        except subprocess.CalledProcessError as e:
            print(f"Verilog compilation failed. STDOUT: {e.stdout.decode()}, STDERR: {e.stderr.decode()}")
        except Exception as e:
            print(f"An unexpected error occurred during Verilog compilation: {e}")


    def run_verilog_logic(self, current_x, current_y, direction_str):
        
        head_x, head_y = current_x, current_y
        
        if direction_str == "North":
            head_y = (head_y - 1) % BOARD_SIZE
        elif direction_str == "South":
            head_y = (head_y + 1) % BOARD_SIZE
        elif direction_str == "West":
            head_x = (head_x - 1) % BOARD_SIZE
        elif direction_str == "East":
            head_x = (head_x + 1) % BOARD_SIZE
            
        return head_x, head_y

    def _process_snake_turn(self, current_snake, current_direction, opponent_snake_body):

        if not current_snake: 
            return (0, 0), [], False, False
            
        head_x, head_y = current_snake[0]
        
        next_x, next_y = self.run_verilog_logic(head_x, head_y, current_direction) 

        crashed = False
        next_head = (next_x, next_y)

        if next_head in current_snake[1:]:
            crashed = True

        if next_head in opponent_snake_body:
            crashed = True
        
        if crashed:
            
            return next_head, current_snake, True, False 
        

        new_snake = [next_head] + current_snake
        ate_food = False
        
        if next_head == self.state.food:
            ate_food = True

            self.state.food = self.state._generate_food() 
        else:
            new_snake.pop() 

        return next_head, new_snake, crashed, ate_food

    def start_game(self):
        if not self.state.is_running:
            self.state.is_running = True
            self.game_loop()
            self.start_btn.config(text="Game Running...", state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)

    def stop_game(self):
        if self.state.is_running:
            self.state.is_running = False
            if self.state.game_timer:
                self.after_cancel(self.state.game_timer)
            self.start_btn.config(text="Start Game", state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            
    def game_loop(self):
        if not self.state.is_running:
            return

        is_two_player = (self.state.game_mode == "Two Player")

        p1_opponent_body = self.state.snake2 if is_two_player else [] 
        
        p1_result = self._process_snake_turn(
            self.state.snake1, self.state.direction1, p1_opponent_body
        )
        p1_next_head, p1_new_snake, p1_crashed, p1_ate_food = p1_result
        
        p2_crashed = False
        p2_ate_food = False
        p2_new_snake = self.state.snake2 
        
        if is_two_player:
            p2_result = self._process_snake_turn(
                self.state.snake2, self.state.direction2, self.state.snake1
            )
            p2_next_head, p2_new_snake, p2_crashed, p2_ate_food = p2_result

        if p1_crashed or p2_crashed:
            self.game_over(p1_crashed, p2_crashed)
            return
            
        self.state.snake1 = p1_new_snake
        self.state.snake2 = p2_new_snake
        
        if p1_ate_food:
            self.state.score1 += 10
        if p2_ate_food:
            self.state.score2 += 10
        
        self._draw_game()
        self._update_dashboard()
        
        self.state.game_timer = self.after(GAME_SPEED_MS, self.game_loop)

    def change_direction(self, snake_id, new_dir):
        if not self.state.is_running:
            return
        
        if snake_id == "snake2" and self.state.game_mode != "Two Player":
            return
            
        if snake_id == "snake1":
            current = self.state.direction1
        else: 
            current = self.state.direction2

        is_reverse = (current == "North" and new_dir == "South") or \
                     (current == "South" and new_dir == "North") or \
                     (current == "East" and new_dir == "West") or \
                     (current == "West" and new_dir == "East")
        
        if not is_reverse:
            if snake_id == "snake1":
                self.state.direction1 = new_dir
            else:
                self.state.direction2 = new_dir


    def game_over(self, p1_crashed, p2_crashed):
        self.stop_game()
        
        if self.state.game_mode == "Single Player":
            message = f"Game Over! Your score: {self.state.score1}"
        else: 
            if p1_crashed and p2_crashed:
                message = f"It's a Draw! Both players crashed at the same time.\nP1 Score: {self.state.score1}, P2 Score: {self.state.score2}"
            elif p1_crashed:
                message = f"Player 1 crashed! Player 2 Wins!\nP1 Score: {self.state.score1}, P2 Score: {self.state.score2}"
            else: 
                message = f"Player 2 crashed! Player 1 Wins!\nP1 Score: {self.state.score1}, P2 Score: {self.state.score2}"
        
        self.state.reset_game()
        self._update_dashboard()
        
        self.show_message("Game Over", message + "\n\nPress 'Start Game' to play again!")


    def _draw_snake(self, snake, head_color, body_color):
        for i, (x, y) in enumerate(snake):
            x1, y1 = x * CELL_SIZE, y * CELL_SIZE
            x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
            
            if i == 0:
                self.canvas.create_rectangle(x1, y1, x2, y2, 
                                             fill=head_color, outline=head_color, width=1, tags="snake")
            else:
                self.canvas.create_rectangle(x1 + 1, y1 + 1, x2 - 1, y2 - 1, 
                                             fill=body_color, outline=body_color, tags="snake")


    def _draw_game(self):
        
        self.canvas.delete("all")
        
        if self.state.food:
            fx, fy = self.state.food
            x1, y1 = fx * CELL_SIZE, fy * CELL_SIZE
            x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
            self.canvas.create_oval(x1 + 5, y1 + 5, x2 - 5, y2 - 5, 
                                    fill="#E91E63", outline="#C2185B", width=2, tags="food")

        if self.state.snake1:
            self._draw_snake(self.state.snake1, "#4CAF50", "#81C784")
        
        if self.state.game_mode == "Two Player" and self.state.snake2:
            self._draw_snake(self.state.snake2, "#2196F3", "#64B5F6")


    def _update_dashboard(self):
        self.score1_label.config(text=f"P1 Score: {self.state.score1}")
        
        combined_score = self.state.score1
        if self.state.game_mode == "Two Player":
            self.score2_label.config(text=f"P2 Score: {self.state.score2}")
            self.score2_label.pack(side=tk.LEFT, padx=30)
            combined_score += self.state.score2
        else:
            self.score2_label.pack_forget()

        self.last_score_label.config(text=f"Last: {self.state.last_score}")
        self.high_score_label.config(text=f"High: {self.state.high_score}")


    def show_message(self, title, message):
        """Custom messagebox replacement."""
        msg_box = tk.Toplevel(self)
        msg_box.title(title)
        msg_box.configure(bg="#444444")
        tk.Label(msg_box, text=message, bg="#444444", fg="white", padx=20, pady=20, font="Inter 12").pack()
        tk.Button(msg_box, text="OK", command=msg_box.destroy, bg="#007BFF", fg="white", font="Inter 10 bold", width=10).pack(pady=10)
        
        self.update_idletasks()
        width = msg_box.winfo_width()
        height = msg_box.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        msg_box.geometry(f'+{x}+{y}')
        msg_box.transient(self) 
        msg_box.grab_set()

    def show_gtkwave(self):
        
        self.show_message("EPWaves Viewer", "Running Verilog Testbench to generate VCD... Check your console for messages.")
        
        try:
            compile_tb_cmd = ['iverilog', '-o', 'snake_tb_compiled', VERILOG_TESTBENCH, VERILOG_SOURCE]
            subprocess.run(compile_tb_cmd, check=True, capture_output=True)
            print("Testbench compiled successfully.")
        except Exception as e:
            print(f"Testbench compilation failed. Ensure iverilog is installed. Error: {e}")
            self.show_message("Error", "Verilog Testbench compilation failed.")
            return
        
        try:
            run_tb_cmd = ['vvp', 'snake_tb_compiled']
            subprocess.run(run_tb_cmd, check=True, capture_output=True)
            print(f"Simulation run successful. VCD file '{VCD_FILE}' generated.")
        except Exception as e:
            print(f"Simulation failed. Ensure vvp is available. Error: {e}")
            self.show_message("Error", "Verilog simulation failed.")
            return
        
        try:
            gtkwave_cmd = ['gtkwave', VCD_FILE]
            subprocess.Popen(gtkwave_cmd) 
            print(f"Attempting to open GTKWave with {VCD_FILE}")
            self.show_message("EPWaves Success", f"GTKWave launched with '{VCD_FILE}'. If it does not appear, check your console for errors.")
        except FileNotFoundError:
            print("Error: 'gtkwave' not found. Please ensure GTKWave is installed and in your PATH.")
            self.show_message("Error", "GTKWave not found. Please ensure it is installed and in your system PATH.")

if __name__ == "__main__":
    game = SnakeGame()
    game.mainloop()