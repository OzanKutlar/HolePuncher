import socket
import argparse
import time
import threading
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=5000, help='Port to bind the rendezvous server on')
parser.add_argument('--heartbeat_interval', type=int, default=5, help='Heartbeat interval in seconds')
args = parser.parse_args()

clients = {}  # Stores client addresses and last heartbeat time
HOST_ID = "host"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', args.port))

print(f"Rendezvous server running on port {args.port}...")

# Function to monitor client heartbeats and remove dead clients
def monitor_heartbeats():
    while True:
        current_time = time.time()
        dead_clients = []
        
        for client_id, client_data in clients.items():
            addr, last_heartbeat = client_data
            if current_time - last_heartbeat > args.heartbeat_interval * 3:  # No heartbeat for 3 intervals
                dead_clients.append(client_id)
                print(f"Client {client_id} at {addr} timed out")
        
        # Remove dead clients
        for client_id in dead_clients:
            del clients[client_id]
            
            # If the host goes down, notify all other clients
            if client_id == HOST_ID:
                print("Host is down, notifying all clients")
                for cid, (caddr, _) in clients.items():
                    sock.sendto(b"HOST_DOWN", caddr)
        
        time.sleep(args.heartbeat_interval)

# Start the heartbeat monitor thread
heartbeat_thread = threading.Thread(target=monitor_heartbeats, daemon=True)
heartbeat_thread.start()

try:
    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode()
        
        # Handle heartbeat messages
        if message.startswith("HEARTBEAT:"):
            client_id = message.split(':')[1]
            if client_id in clients:
                clients[client_id] = (addr, time.time())  # Update last heartbeat time
                sock.sendto(b"HEARTBEAT_ACK", addr)
            continue
        
        # Handle registration messages
        client_id = message
        print(f"Received from {client_id}: {addr}")
        
        # Store client info with current timestamp
        clients[client_id] = (addr, time.time())
        
        # Send acknowledgment of registration
        sock.sendto(f"REGISTERED:{client_id}".encode(), addr)
        
        # If this is a host registration, nothing more to do
        if client_id == HOST_ID:
            print(f"Host registered at {addr}")
        else:
            # If host exists, facilitate the connection
            if HOST_ID in clients:
                host_addr, _ = clients[HOST_ID]
                # Send peer info to host
                sock.sendto(f"NEW_PEER:{addr[0]}:{addr[1]}:{client_id}".encode(), host_addr)
                # Send host info to peer
                sock.sendto(f"HOST_INFO:{host_addr[0]}:{host_addr[1]}".encode(), addr)
                print(f"Connected {client_id} with host")
            else:
                sock.sendto(b"WAITING_FOR_HOST", addr)
                print(f"Client {client_id} is waiting for host")

except KeyboardInterrupt:
    print("Server shutting down...")
    sys.exit(0)