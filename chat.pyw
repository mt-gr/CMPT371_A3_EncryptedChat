import socket
import threading
import rsa
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
from concurrent.futures import ThreadPoolExecutor
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os

class Chat:
    def __init__(self):

        # Prepare GUI
        self.root = tk.Tk()
        self.root.title("RSA Secure Chat")
        self.root.geometry("400x500")

        # Set shutdown function to run on window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Generate RSA Keys
        self.public_key, self.private_key = rsa.newkeys(1024)
        self.peer_public_key = None
        
        # Set Networking fields
        self.socket = None
        self.conn = None
        self.nickname = ""

        # Prepare executor for threading
        self.executor = ThreadPoolExecutor(max_workers=5)

        # Run landing page
        self.setup_launcher()

    def setup_launcher(self):
        # Prepare initial landing window to Host or Connect
        self.launcher_frame = tk.Frame(self.root)
        self.launcher_frame.pack(pady=50)

        # Create entry fields for landing page
        tk.Label(self.launcher_frame, text="Nickname:").pack()
        self.nick_entry = tk.Entry(self.launcher_frame)
        self.nick_entry.pack(pady=5)

        tk.Label(self.launcher_frame, text="IP Address:").pack()
        self.ip_entry = tk.Entry(self.launcher_frame)
        self.ip_entry.pack(pady=5)

        tk.Label(self.launcher_frame, text="Port:").pack()
        self.port_entry = tk.Entry(self.launcher_frame)
        self.port_entry.insert(0, "9999") # Set default port
        self.port_entry.pack(pady=5)

        tk.Button(self.launcher_frame, text="Host Server", width=20, 
                  command=self.start_as_host).pack(pady=10)
        tk.Button(self.launcher_frame, text="Connect to Host", width=20, 
                  command=self.start_as_client).pack(pady=5)

    def start_as_host(self):
        self.is_host = True
        self.nickname = self.nick_entry.get() or "Host"
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            port_text = self.port_entry.get()
            port = int(port_text)
        
            if not (1 <= port <= 65535):
                raise ValueError("Port must be between 1 and 65535")
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid port number (e.g., 9999)")
            return
        
        try: 
            self.socket.bind(('0.0.0.0', port))
            self.socket.listen(1)
            self.update_ui_for_chat("Waiting for connection...")
            self.executor.submit(self.accept_connection)
        except Exception as e:
            messagebox.showerror("Error", f"Could not bind to port {port}: {e}")

    def start_as_client(self):
        self.is_host = False
        self.nickname = self.nick_entry.get() or "Client"
        ip = self.ip_entry.get()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            port_text = self.port_entry.get()
            port = int(port_text)
        
            if not (1 <= port <= 65535):
                raise ValueError("Port must be between 1 and 65535")
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid port number (e.g., 9999)")
            return
        
        try:
            self.socket.connect((ip, port))
            self.conn = self.socket
            self.update_ui_for_chat(f"Connected to {ip}")
            self.perform_handshake()
            self.executor.submit(self.receive_messages)
        except Exception as e:
            messagebox.showerror("Error", f"Could not connect: {e}")

    def accept_connection(self):
      while True:
            try:
                new_conn, addr = self.socket.accept()
                
                if self.conn is not None:
                    try:
                        # Send rejection and shut down properly
                        new_conn.send(b"System: Server Full.")
                        new_conn.shutdown(socket.SHUT_RDWR)
                        new_conn.close()
                    except:
                        pass
                    continue 
                
                self.conn = new_conn
                self.write_to_chat(f"System: Connected to {addr}")
                
                # Use executor to avoid blocking the 'bouncer' loop
                self.executor.submit(self.handle_peer)
                
            except Exception:
                break
            
    def handle_peer(self):
        #Dedicated thread to manage the lifecycle of a single peer
        try:
            self.perform_handshake()
            self.receive_messages()
        except Exception as e:
            print(f"Error handling peer: {e}")

    def perform_handshake(self):
        #Exchange RSA Keys, then use RSA to securely share a 256-bit AES Key
        try:
            # RSA Key Exchange
            self.conn.send(self.public_key.save_pkcs1())
            peer_key_data = self.conn.recv(1024)
            self.peer_public_key = rsa.PublicKey.load_pkcs1(peer_key_data)

            #   Determine who generates the AES secret
            if self.is_host:
                # Host generates the master AES key
                self.aes_key = os.urandom(32) 
                # Encrypt AES key with Client's RSA Public Key
                encrypted_aes = rsa.encrypt(self.aes_key, self.peer_public_key)
                self.conn.send(encrypted_aes)
            else:
                # Client receives the encrypted AES key
                encrypted_aes = self.conn.recv(1024)
                # Decrypt AES key with My RSA Private Key
                self.aes_key = rsa.decrypt(encrypted_aes, self.private_key)

            self.write_to_chat("System: Hybrid RSA-AES Handshake Complete.")
        except Exception as e:
            self.write_to_chat(f"System: Handshake Failed - {e}")
            self.on_closing()

    def update_ui_for_chat(self, status):
        self.launcher_frame.destroy()
        
        self.chat_area = scrolledtext.ScrolledText(self.root, state='disabled')
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        self.msg_entry = tk.Entry(self.root)
        self.msg_entry.pack(padx=10, pady=5, fill=tk.X)
        self.msg_entry.bind("<Return>", lambda e: self.send_message())
        
        self.send_btn = tk.Button(self.root, text="Send", command=self.send_message)
        self.send_btn.pack(pady=5)
        self.write_to_chat(status)

    def send_message(self):
        msg_text = self.msg_entry.get()
        if msg_text and hasattr(self, 'aes_key'):
            try:
                full_msg = f"{self.nickname}: {msg_text}"
                msg_bytes = full_msg.encode()

                # Create a fresh initialization vector for this specific message
                iv = os.urandom(16)
                cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)

                # Encrypt the data (AES requires padding to 16-byte blocks)
                encrypted_data = cipher.encrypt(pad(msg_bytes, AES.block_size))

                # Send: [IV (16 bytes)] + [Encrypted Data]
                self.conn.send(iv + encrypted_data)

                self.write_to_chat(full_msg)
                self.msg_entry.delete(0, tk.END)
            except Exception as e:
                self.write_to_chat(f"System: Send Error - {e}")
                self.disable_ui()

    def receive_messages(self):
        while True:
                try:
                    # AES messages can be larger than RSA, so 2048 is a safe buffer
                    data = self.conn.recv(2048)
                    if not data:
                        break

                    # Extract the IV (first 16 bytes) and the ciphertext (the rest)
                    iv = data[:16]
                    ciphertext = data[16:]

                    # Reconstruct the cipher using the shared key and the received IV
                    cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)

                    # Decrypt and remove the padding
                    decrypted_bytes = unpad(cipher.decrypt(ciphertext), AES.block_size)
                    message = decrypted_bytes.decode()

                    self.root.after(0, self.write_to_chat, message)
                except Exception:
                    self.root.after(0, self.write_to_chat, "System: Connection lost.")
                    self.root.after(0, self.disable_ui)
                    break

    def write_to_chat(self, message):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, message + "\n")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

    def run(self):
        self.root.mainloop()

    def disable_ui(self):
        # Disable the text entry box and send button
        self.msg_entry.delete(0, tk.END)
        self.msg_entry.insert(0, "Disconnected...")
        self.msg_entry.config(state='disabled')
        self.send_btn.config(state='disabled')

    def on_closing(self):
        # Terminate running threads and fully shutdown
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            # Shutdown the executor (terminate running threads)
            self.executor.shutdown(wait=False, cancel_futures=True)
        
            # Close the connection/socket to break the 'recv' loops
            try:
                if self.conn and self.peer_public_key:
                    exit_msg = f"System: {self.nickname} has left the chat."
                    enc_exit = rsa.encrypt(exit_msg.encode(), self.peer_public_key)
                    self.conn.send(enc_exit)
            except:
                pass # Peer might have already disconnected
            try:
                if self.conn:
                    self.conn.shutdown(socket.SHUT_RDWR)
                    self.conn.close()
                if self.socket:
                    self.socket.close()
            except:
                pass # Socket might already be closed
            
            self.root.destroy()
            import os
            os._exit(0) # Forcefully kill the process and all threads

if __name__ == "__main__":
    app = Chat()
    app.run()
