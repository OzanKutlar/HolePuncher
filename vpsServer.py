# rendezvous_server.py
import socket
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=5000, help='Port to bind the rendezvous server on')
args = parser.parse_args()

clients = {}
HOST_ID = "host"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', args.port))
print(f"Rendezvous server running on port {args.port}...")

while True:
    data, addr = sock.recvfrom(1024)
    client_id = data.decode()
    print(f"Received from {client_id}: {addr}")

    if client_id == HOST_ID:
        clients[HOST_ID] = addr
    else:
        if HOST_ID in clients:
            sock.sendto(f"{clients[HOST_ID][0]}:{clients[HOST_ID][1]}".encode(), addr)
            sock.sendto(f"{addr[0]}:{addr[1]}".encode(), clients[HOST_ID])
