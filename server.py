import socket
import threading
import argparse
import time
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--vps_ip', required=True, help='IP of the rendezvous server')
parser.add_argument('--vps_port', type=int, default=5000, help='Port of the rendezvous server')
parser.add_argument('--heartbeat_interval', type=int, default=5, help='Heartbeat interval in seconds')
args = parser.parse_args()

RENDEZVOUS_SERVER = (args.vps_ip, args.vps_port)
MY_ID = 'host'

# Keep track of connected peers
peers = {}  # {peer_addr: (last_heartbeat_time, peer_id)}
server_last_heartbeat = time.time()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 0))
print(f"[HOST] Bound to local port {sock.getsockname()[1]}")

# Send initial registration
sock.sendto(MY_ID.encode(), RENDEZVOUS_SERVER)

# Function to send heartbeats to the server
def server_heartbeat():
    global server_last_heartbeat
    while True:
        try:
            sock.sendto(f"HEARTBEAT:{MY_ID}".encode(), RENDEZVOUS_SERVER)
            server_last_heartbeat = time.time()
            time.sleep(args.heartbeat_interval)
        except Exception as e:
            print(f"[ERROR] Server heartbeat error: {e}")
            time.sleep(1)

# Function to send heartbeats to all peers
def peer_heartbeats():
    while True:
        current_time = time.time()
        dead_peers = []
        
        # Check for dead peers
        for peer_addr, (last_time, peer_id) in peers.items():
            if current_time - last_time > args.heartbeat_interval * 3:
                dead_peers.append((peer_addr, peer_id))
            else:
                # Send heartbeat to live peers
                try:
                    sock.sendto(b"PEER_HEARTBEAT", peer_addr)
                except:
                    pass
        
        # Remove dead peers
        for peer_addr, peer_id in dead_peers:
            print(f"[INFO] Peer lost: {peer_id} at {peer_addr}")
            del peers[peer_addr]
        
        time.sleep(args.heartbeat_interval)

# Function to handle peer connections
def handle_peer(peer_addr, peer_id):
    print(f"[+] Handling new peer: {peer_id} at {peer_addr}")
    # Add peer to our list with current timestamp
    peers[peer_addr] = (time.time(), peer_id)
    
    # Send welcome message
    sock.sendto(f"Welcome {peer_id}! You're connected to the host.".encode(), peer_addr)

# Start the heartbeat threads
server_heartbeat_thread = threading.Thread(target=server_heartbeat, daemon=True)
server_heartbeat_thread.start()

peer_heartbeat_thread = threading.Thread(target=peer_heartbeats, daemon=True)
peer_heartbeat_thread.start()

try:
    # Main loop to listen for messages
    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode()
        
        # Handle server communication
        if addr == RENDEZVOUS_SERVER:
            if message == "HEARTBEAT_ACK":
                server_last_heartbeat = time.time()
                continue
                
            if message.startswith("NEW_PEER:"):
                # Format: NEW_PEER:ip:port:peer_id
                peer_info = message.split(':')
                if len(peer_info) >= 4:
                    peer_ip = peer_info[1]
                    peer_port = int(peer_info[2])
                    peer_id = peer_info[3]
                    peer_addr = (peer_ip, peer_port)
                    
                    print(f"[HOST] Got new peer: {peer_id} at {peer_addr}")
                    
                    # Punch a hole
                    for _ in range(5):
                        sock.sendto(b"PUNCH", peer_addr)
                    
                    # Start handling this peer
                    threading.Thread(target=handle_peer, args=(peer_addr, peer_id), daemon=True).start()
            elif message == "REGISTERED:host":
                print("[HOST] Successfully registered with rendezvous server")
            else:
                print(f"[INFO] Message from server: {message}")
        
        # Handle peer communication
        elif addr in peers:
            peers[addr] = (time.time(), peers[addr][1])  # Update heartbeat time
            
            if message == "PEER_HEARTBEAT":
                # Just update the timestamp, already done above
                continue
            elif message.startswith("PUNCH"):
                # Just a hole punch packet, ignore
                continue
            else:
                print(f"[{peers[addr][1]}] {message}")
                # Echo the message back
                sock.sendto(f"Echo: {message}".encode(), addr)
        
        # Handle message from unknown source - might be a new peer
        else:
            print(f"[INFO] Message from unknown source {addr}: {message}")
            if message == "PUNCH" or message.startswith("PEER_HEARTBEAT"):
                # This might be a new peer trying to establish connection
                # We'll respond but not add them to our list yet
                sock.sendto(b"WAITING_FOR_SERVER_INTRO", addr)
            
except KeyboardInterrupt:
    print("[HOST] Shutting down...")
    sys.exit(0)