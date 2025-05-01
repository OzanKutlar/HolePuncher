# client.py
import socket
import threading
import time

RENDEZVOUS_SERVER = ('vps', 5000)
MY_ID = input("Enter your ID: ")  # Unique ID to identify yourself to server

# Setup UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 0))  # Let OS pick a random port

# Register with the server
sock.sendto(MY_ID.encode(), RENDEZVOUS_SERVER)

# Wait to receive peer info
data, _ = sock.recvfrom(1024)
peer_ip, peer_port = data.decode().split(':')
peer_addr = (peer_ip, int(peer_port))

print(f"Received peer address: {peer_addr}")

# Punch a hole by sending packets to peer
def punch():
    while True:
        sock.sendto(b"punch", peer_addr)
        time.sleep(1)

threading.Thread(target=punch, daemon=True).start()

# Listen for messages from peer
while True:
    msg, addr = sock.recvfrom(1024)
    print(f"Received from {addr}: {msg.decode()}")
