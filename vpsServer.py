# rendezvous_server.py
import socket

clients = {}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 5000))  # Use a public-facing IP

print("Server is listening...")

while True:
    data, addr = sock.recvfrom(1024)
    peer_id = data.decode()

    print(f"Received connection from {peer_id}: {addr}")
    clients[peer_id] = addr

    if len(clients) == 2:
        ids = list(clients.keys())
        # Exchange addresses
        sock.sendto(f"{clients[ids[1]][0]}:{clients[ids[1]][1]}".encode(), clients[ids[0]])
        sock.sendto(f"{clients[ids[0]][0]}:{clients[ids[0]][1]}".encode(), clients[ids[1]])
        clients = {}  # Reset for next pair
