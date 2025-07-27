import socket
import threading
import tkinter as tk
from tkinter import ttk, Scrollbar

class GameClient:
    def __init__(self):
        self.host = None
        self.port = None
        self.is_drawer = False
        self.username = ""
        self.enter_server_info()
        self.root = tk.Tk()
        self.root.title("Draw and Guess")
        self.initialize_gui()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        threading.Thread(target=self.receive_messages).start()
        self.root.mainloop()
        self.countdown_task = None
    
    def initialize_gui(self):
        style = ttk.Style()
        style.configure("TButton", padding=(0, 5), font=('calibri', 12, 'bold'))
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=3)  # Canvas should take more space
        frame.grid_columnconfigure(1, weight=1)  # Chat should be of fixed size
    
        # Canvas for drawing
        self.canvas = tk.Canvas(frame, bg="white", width=700, height=700, highlightthickness=1, highlightbackground="gray")
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.add_point)
        self.canvas.bind("<B1-Motion>", self.add_point)
    
        # Chat components on the right side
        chat_frame = ttk.Frame(frame)
        chat_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10)
    
        self.chat_text = tk.Text(chat_frame, wrap=tk.WORD, width=30, height=20, bg="#f2f2f2")
        self.chat_text.pack(pady=(10, 0), padx=10, fill=tk.BOTH, expand=True)
    
        # Entry for typing chat and send button
        self.chat_entry = ttk.Entry(chat_frame, width=25)
        self.chat_entry.pack(pady=(5, 10), padx=5, side=tk.LEFT, fill=tk.X, expand=True)  # Setting side to LEFT
        self.chat_entry.bind("<Return>", self.send_chat_message)
    
        send_button = ttk.Button(chat_frame, text="Send", command=self.send_chat_message)
        send_button.pack(pady=10, padx=(5, 20), side=tk.RIGHT)  # Adjusting the padding on the right

    
        clear_canvas_button = ttk.Button(frame, text="Clear canvas", command=self.clear_canvas, style="TButton")
        clear_canvas_button.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
    
        # Timer
        timer_frame = ttk.Frame(frame, relief=tk.RIDGE, padding="10")
        timer_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10)
        self.timer_label = tk.Label(timer_frame, text="3:00", font=("Helvetica", 36), bg="#e0e0e0")
        self.timer_label.pack(fill=tk.BOTH)


    def start_countdown(self, time_remaining=180):
        minutes = time_remaining // 60
        seconds = time_remaining % 60
        self.timer_label.config(text=f"{minutes}:{seconds:02d}")
        if time_remaining > 0:
            self.countdown_task = self.root.after(1000, self.start_countdown, time_remaining - 1)

    def stop_countdown(self):
        if self.countdown_task:
            self.root.after_cancel(self.countdown_task)
            self.countdown_task = None
            self.timer_label.config(text="3:00")

    def clear_canvas(self):
        self.canvas.delete("all")
        self.client_socket.send("CLEAR_CANVAS;".encode("utf-8"))

    def enter_server_info(self):
        root = tk.Tk()
        root.title("Enter Server Info")
        frame = ttk.Frame(root, padding="3")
        frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        host_label = ttk.Label(frame, text="Host IP:")
        host_label.grid(row=0, column=0, sticky=(tk.W))
        
        host_entry = ttk.Entry(frame, width=20)
        host_entry.grid(row=0, column=1, sticky=(tk.E))
        
        port_label = ttk.Label(frame, text="Port:")
        port_label.grid(row=1, column=0, sticky=(tk.W))
        
        port_entry = ttk.Entry(frame, width=20)
        port_entry.grid(row=1, column=1, sticky=(tk.E))
        
        def on_enter(event=None):
            self.set_server_info(host_entry.get(), port_entry.get(), root)

        enter_button = ttk.Button(frame, text="Enter", command=on_enter)
        enter_button.grid(row=2, columnspan=2)

        # Bind the Enter key to the function
        root.bind("<Return>", on_enter)

        # Put the focus on the host_entry to begin with
        host_entry.focus_set()
        
        root.mainloop()

    
    def set_server_info(self, host, port, root):
        self.host = host
        self.port = int(port)
        root.destroy()

    def add_point(self, event):
        if self.is_drawer:
            x, y = event.x, event.y
            self.canvas.create_oval(x, y, x + 1, y + 1, fill="black", width=5)
            message = f"DRAW:{x},{y}" + ";"
            self.client_socket.send(message.encode('utf-8'))
    
    def send_chat_message(self, event=None):
        message = self.chat_entry.get()+";"
        self.chat_entry.delete(0, tk.END)
        self.client_socket.send(message.encode('utf-8'))
    
    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                for msg in message.split(";"):
                    if msg:
                        if msg == "CLEAR_CANVAS":
                            self.canvas.delete("all")
                            continue
                        if msg == "NEW_ROUND":
                            self.stop_countdown()  # Stop the countdown and reset counter
                            self.canvas.delete("all")  # Clear the canvas
                            self.chat_text.delete('1.0', tk.END)  # Clear the chat text
                            continue
                        if not msg.startswith("DRAW:"):
                            self.chat_text.insert(tk.END, f"{msg}\n")
                        if msg.startswith("DRAW:"):
                            x, y = map(int, msg[5:].split(","))
                            self.canvas.create_oval(x, y, x + 1, y + 1, fill="black", width=5)
                        elif "ROLE:drawer" in msg:
                            self.is_drawer = True
                            self.start_countdown()
                        elif "ROLE:guesser" in msg:
                            self.is_drawer = False
                            self.start_countdown()
            except:
                print("Server closed the connection.")
                break
    
    
if __name__ == "__main__":
    GameClient()
