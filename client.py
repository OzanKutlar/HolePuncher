# peer.py
import socket
import threading
import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--vps_ip', required=True, help='IP of the rendezvous server')
parser.add_argument('--vps_port', type=int, default=5000, help='Port of the rendezvous server')
args = parser.parse_args()

RENDEZVOUS_SERVER = (args.vps_ip, args.vps_port)
MY_ID = input("Enter your client ID: ")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 0))
sock.sendto(MY_ID.encode(), RENDEZVOUS_SERVER)

data, _ = sock.recvfrom(1024)
host_ip, host_port = data.decode().split(':')
host_addr = (host_ip, int(host_port))
print(f"[PEER] Host address: {host_addr}")

def punch():
    for _ in range(10):
        sock.sendto(b"punch", host_addr)
        time.sleep(1)

punch()

def listen():
    while True:
        data, addr = sock.recvfrom(1024)
        print(f"[HOST] {data.decode()}")

threading.Thread(target=listen, daemon=True).start()

while True:
    msg = input("You: ")
    sock.sendto(msg.encode(), host_addr)
