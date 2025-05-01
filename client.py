# client_peer.py
import socket
import threading
import time

RENDEZVOUS = ('your.vps.ip', 5000)
CLIENT_ID = input("Enter your client ID: ")
TARGET_HOST_ID = input("Enter target host ID: ")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 0))

# Register with rendezvous
sock.sendto(f"CLIENT:{CLIENT_ID}:{TARGET_HOST_ID}".encode(), RENDEZVOUS)

# Receive host address
data, _ = sock.recvfrom(1024)
host_ip, host_port = data.decode().split(":")
host = (host_ip, int(host_port))

print(f"[Client] Connecting to host at {host}...")

def punch():
    while True:
        sock.sendto(b"hello", host)
        time.sleep(1)

threading.Thread(target=punch, daemon=True).start()

while True:
    data, addr = sock.recvfrom(1024)
    print(f"[Client] Received from {addr}: {data.decode()}")
