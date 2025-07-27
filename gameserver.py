import socket
import threading
import tkinter as tk
from tkinter import ttk
import random
import time

class GameServer:
    def __init__(self):
        self.clients = []
        self.drawer_client = None
        self.current_word = None
        self.current_blank_word = None
        self.time_left = 180
        self.timer_id = None
        self.root = tk.Tk()
        self.root.title("Server")
        self.initialize_gui()
        self.root.mainloop()

    def initialize_gui(self):
        self.port_label = ttk.Label(self.root, text="Port:")
        self.port_label.pack(pady=5)
        self.port_entry = ttk.Entry(self.root)
        self.port_entry.pack(pady=5)
        self.port_entry.bind("<Return>", self.start_server)
        self.start_server_button = ttk.Button(self.root, text="Start Server", command=self.start_server)
        self.start_server_button.pack(pady=5)
        self.client_list_box = tk.Listbox(self.root)
        self.start_game_button = ttk.Button(self.root, text="Start Game", command=self.start_game)

    def timer(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.timer_id = self.root.after(1000, self.timer)
        else:
            if self.timer_id is not None:
                self.root.after_cancel(self.timer_id)
            self.broadcast("NEW_ROUND;", None)
            self.broadcast(f"Time's up! The word was {self.current_word}\n", None)
            self.start_game()

    def reset_timer(self):
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
        self.time_left = 180
        self.timer()
    
    def choose_next_word(self):
        self.current_blank_word = ""
        with open('words.txt', 'r') as f:
            for i, line in enumerate(f, 1):
                if random.random() < 1 / i:
                    self.current_word = line.strip().lower()
        for letter in self.current_word:
            self.current_blank_word += "_ "
    
    def choose_next_drawer(self):
        if not self.clients:
            return
        if self.drawer_client is None:
            self.drawer_client = self.clients[0]
        else:
            index = (self.clients.index(self.drawer_client) + 1) % len(self.clients)
            self.drawer_client = self.clients[index]
        self.choose_next_word()

    def start_game(self):
        self.choose_next_drawer()
        self.time_left = 180
        self.reset_timer()
        if not self.clients:
            return
        self.start_game_button.pack_forget()
        for client in self.clients:
            if client == self.drawer_client:
                client.send("ROLE:drawer\n".encode('utf-8'))
                client.send(f"You are drawing: {self.current_word}".encode('utf-8'))
            else:
                client.send("ROLE:guesser\n".encode('utf-8'))
                client.send(f"Guess the word: {self.current_blank_word}".encode('utf-8'))

    def handle_client(self, client_socket):
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8').strip()
                if message.startswith("DRAW:"):
                    if client_socket == self.drawer_client:
                        self.broadcast(message, None)
                elif message.lower().strip(";") == self.current_word and client_socket != self.drawer_client:
                    self.broadcast("NEW_ROUND;", None)
                    self.broadcast(f"Correct guess! The word was {self.current_word}\n", None)
                    self.start_game()
                else:
                    self.broadcast(message, client_socket)
            except:
                self.clients.remove(client_socket)
                client_socket.close()
                break

    def broadcast(self, message, client_socket):
        for client in self.clients:
            try:
                client.send(message.encode('utf-8'))
            except:
                self.clients.remove(client)
                client.close()

    def accept_clients(self, server):
        while True:
            client_socket, address = server.accept()
            self.clients.append(client_socket)
            self.client_list_box.insert(tk.END, str(address))
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    def start_server(self, event=None):
        port = int(self.port_entry.get())
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("0.0.0.0", port))
        server.listen(5)
        
        self.port_label.pack_forget()
        self.port_entry.pack_forget()
        self.start_server_button.pack_forget()
        
        server_label = ttk.Label(self.root, text=f"Server started at IP: {socket.gethostbyname(socket.gethostname())} and Port: {port}")
        server_label.pack(pady=5)
        self.client_list_box.pack(pady=5)
        self.start_game_button.pack(pady=5)
        
        accept_thread = threading.Thread(target=self.accept_clients, args=(server,))
        accept_thread.start()

if __name__ == "__main__":
    GameServer()
