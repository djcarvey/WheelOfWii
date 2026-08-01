import os
import shutil
from pathlib import Path
import gspread

import tkinter as tk
import math
import random

destination = Path(os.getenv('APPDATA')) / "gspread" 
destination.mkdir(parents=True, exist_ok=True)

content = None
shutil.copy("zaxorawiistreaming-cc4826a0f530.json",destination / "service_account.json") 

with open("sheetID.txt", "r") as file:
    content = file.read()
gc = gspread.service_account()
gamesSheet = gc.open_by_key(content).sheet1 #the real sheet
data = gamesSheet.get_all_records(expected_headers = ["Game","Have It?","Streamed It?","Count","1","Style","Language","Disc","Cover","Contents","Extra","#"])
filteredData = [f"#{row["#"]}: {row["Game"]}" for row in data if (row["Game"] != "") and (row["Have It?"] != "") and (row["Streamed It?"] == "")]
random.shuffle(filteredData)

def alternate_ends(lst):
    left = 0
    right = len(lst) - 1
    result = []
    while left <= right:
        result.append(lst[left])
        if left != right:
            result.append(lst[right])
        left += 1
        right -= 1
    return result

class SpinningWheel:
    def __init__(self, root):
        self.root = root
        self.root.title('The Great Wheel of Wii (The "Wiil" if you will)')
        
        # Configuration options
        self.prizes = filteredData
        self.num_segments = len(self.prizes)
        self.colors = ["#B9B9D9" if i % 2 == 0 else "#CFAFBF" for i in range(len(self.prizes))]
        self.angle_per_segment = 360 / self.num_segments
        
        # Physics / Animation variables
        self.current_angle = 0
        self.speed = 0
        self.friction = 0.97  # Determines how quickly the wheel slows down
        self.is_spinning = False
        self.current_winner = None
        
        # Create GUI elements
        self.setup_ui()
        self.draw_wheel()

    def setup_ui(self):
        # Canvas for drawing the wheel
        self.canvas = tk.Canvas(self.root, width=1000, height=800, bg="white", highlightthickness=0)
        self.canvas.pack(pady=20)
        
        # Action button to trigger the spin
        self.spin_button = tk.Button(self.root, text="SPIN THE WHEEL", font=("Arial", 14, "bold"), 
                                     bg="#4CAF50", fg="white", command=self.start_spin)
        self.spin_button.pack(pady=10)
        
        # Text label to showcase results
        self.result_label = tk.Label(self.root, text="Click to Decide What to Play!", font=("Arial", 16, "bold"))
        self.result_label.pack(pady=10)

    def draw_wheel(self):
        self.canvas.delete("all")
        cx, cy, r = 500, 400, 400  # Center points and radius
        
        # Draw the multi-colored pie slices
        winning_angle = (0 - self.current_angle) % 360
        current_winner = int(winning_angle / self.angle_per_segment)
        angle_overflow = ((0 - self.current_angle) % self.angle_per_segment)/self.angle_per_segment
        center = None
        the_list = list(range(self.num_segments))
        alt_list = alternate_ends(the_list[current_winner:]+the_list[:current_winner])
        
        #Scale wedge size when drawing so that items closer to the winner indicator will be {scale}-degrees
        #Wedges will get smaller the farther away from the indicator they get
        #implementation: draw the winning wedge, then alternate drawing above and below until things get too small to draw.
        scale = 10
        arc_start = None
        for i in range(self.num_segments):
            if arc_start is None:
                center = (scale*(.5-angle_overflow)) %360
                wedge_width = scale*max(0,abs(180-center)/180)
                lower_start = (360-wedge_width*angle_overflow)
                upper_start = (wedge_width*(1-angle_overflow))
                arc_start = lower_start %360
            elif i%2==1:
                wedge_width = scale*max(0,abs(180-lower_start)/180)
                lower_start = max(180,lower_start-wedge_width %360)
                arc_start = lower_start %360
            else:
                wedge_width = scale*max(0,abs(180-upper_start)/180)
                arc_start = upper_start%360
                upper_start = min(180,upper_start + wedge_width %360)
                
            if wedge_width > .25:
                self.canvas.create_arc(cx - r, cy - r, cx + r, cy + r, 
                                   start=arc_start, extent=wedge_width, 
                                   fill=self.colors[alt_list[i] % len(self.colors)])
            
            if i<75:
                # Calculate positions for the text labels inside slices
                text_angle = math.radians(arc_start + wedge_width / 2)
                text_x = cx + (r * 0.6) * math.cos(text_angle)
                text_y = cy - (r * 0.6) * math.sin(text_angle)  # Subtract because canvas y-axis goes down
                self.canvas.create_text(text_x, text_y, text=f"{self.prizes[alt_list[i]]}", fill="black", 
                                    font=("Arial", 10, "bold"), angle=int(arc_start + wedge_width / 2))
            
        # Draw the stationary indicator arrow pointer at the right (0 degrees position)
        self.canvas.create_polygon(cx + r - 5, cy, cx + r + 20, cy - 15, cx + r + 20, cy + 15, fill="red", outline="black")
        self.canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=175, extent=10, fill="#000000" )
        self.canvas.create_circle = self.canvas.create_oval(cx - 10, cy - 10, cx + 10, cy + 10, fill="white", outline="black", width=3)

    def start_spin(self):
        if not self.is_spinning:
            self.is_spinning = True
            self.spin_button.config(state="disabled")
            self.result_label.config(text="Spinning...")
            self.speed = random.uniform(15, 60)  # Assign a random initial rotational velocity
            self.animate_spin()

    def animate_spin(self):
        if self.speed > 0.1/math.log(self.num_segments):
            self.current_angle = (self.current_angle + self.speed) % 360
            self.speed *= self.friction  # Slowly decrease velocity over time
            self.draw_wheel()
            self.root.after(15, self.animate_spin)  # Schedule next frame update
        else:
            self.stop_spin()

    def stop_spin(self):
        self.is_spinning = False
        self.spin_button.config(state="normal")
        
        # Calculate winning item based on final rotation angle relative to pointer 
        # Canvas angles go counter-clockwise, pointer is at 0 degrees
        winning_angle = (0 - self.current_angle) % 360
        winning_index = int(winning_angle / self.angle_per_segment)
        winning_game = self.prizes[winning_index]
        
        self.result_label.config(text=f"🎉 Time to play: {winning_game}! 🎉")
        
    

if __name__ == "__main__":
    window = tk.Tk()
    app = SpinningWheel(window)
    window.mainloop()
