# host.py
import socket
import threading
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--vps_ip', required=True, help='IP of the rendezvous server')
parser.add_argument('--vps_port', type=int, default=5000, help='Port of the rendezvous server')
args = parser.parse_args()

RENDEZVOUS_SERVER = (args.vps_ip, args.vps_port)
MY_ID = 'host'

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 0))
print(f"[HOST] Bound to local port {sock.getsockname()[1]}")

sock.sendto(MY_ID.encode(), RENDEZVOUS_SERVER)

def handle_peer(peer_addr):
    print(f"[+] Handling new peer: {peer_addr}")
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if addr == peer_addr:
                print(f"[{addr}] {data.decode()}")
                sock.sendto(f"Echo: {data.decode()}".encode(), peer_addr)
        except:
            break

while True:
    data, _ = sock.recvfrom(1024)
    peer_ip, peer_port = data.decode().split(':')
    peer_addr = (peer_ip, int(peer_port))
    print(f"[HOST] Got new peer: {peer_addr}")

    for _ in range(5):
        sock.sendto(b"punch", peer_addr)

    threading.Thread(target=handle_peer, args=(peer_addr,), daemon=True).start()
