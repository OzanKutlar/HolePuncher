# host_peer.py
import socket
import threading
import time

RENDEZVOUS = ('your.vps.ip', 5000)
HOST_ID = "myhost"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 0))

# Register as host
sock.sendto(f"HOST:{HOST_ID}".encode(), RENDEZVOUS)

print(f"[Host] Registered as {HOST_ID}, listening for peers...")

def handle_client(peer_addr):
    def punch():
        while True:
            sock.sendto(b"ping", peer_addr)
            time.sleep(1)
    threading.Thread(target=punch, daemon=True).start()

    while True:
        data, addr = sock.recvfrom(1024)
        if addr == peer_addr:
            print(f"[Host] Received from {addr}: {data.decode()}")
            sock.sendto(b"ack", addr)

while True:
    # Each new client will be announced via the rendezvous server
    data, _ = sock.recvfrom(1024)
    ip, port = data.decode().split(":")
    peer = (ip, int(port))
    print(f"[Host] New peer: {peer}")
    threading.Thread(target=handle_client, args=(peer,), daemon=True).start()
