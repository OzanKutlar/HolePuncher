# multi_client_rendezvous_server.py
import socket
import threading

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 5000))

hosts = {}  # host_id -> address
clients = {}  # client_id -> target_host_id and address

def server_loop():
    while True:
        data, addr = sock.recvfrom(1024)
        msg = data.decode().strip()

        if msg.startswith("HOST:"):
            host_id = msg[5:]
            hosts[host_id] = addr
            print(f"Registered host {host_id} at {addr}")

        elif msg.startswith("CLIENT:"):
            _, client_id, target_host_id = msg.split(":")
            if target_host_id in hosts:
                host_addr = hosts[target_host_id]
                clients[client_id] = (target_host_id, addr)
                print(f"Client {client_id} wants to connect to host {target_host_id}")

                # Notify host and client about each other
                sock.sendto(f"{addr[0]}:{addr[1]}".encode(), host_addr)
                sock.sendto(f"{host_addr[0]}:{host_addr[1]}".encode(), addr)
            else:
                sock.sendto(b"ERROR: Host not found", addr)

threading.Thread(target=server_loop).start()
