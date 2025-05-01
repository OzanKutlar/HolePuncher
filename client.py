import socket
import threading
import time
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--vps_ip', required=True, help='IP of the rendezvous server')
parser.add_argument('--vps_port', type=int, default=5000, help='Port of the rendezvous server')
parser.add_argument('--heartbeat_interval', type=int, default=5, help='Heartbeat interval in seconds')
args = parser.parse_args()

RENDEZVOUS_SERVER = (args.vps_ip, args.vps_port)
MY_ID = input("Enter your client ID: ")

# Connection state
host_addr = None
host_connected = False
server_last_heartbeat = time.time()
host_last_heartbeat = None

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 0))
print(f"[PEER] Bound to local port {sock.getsockname()[1]}")

# Register with the server
sock.sendto(MY_ID.encode(), RENDEZVOUS_SERVER)

# Function to send heartbeats to the server (before P2P connection)
def server_heartbeat():
    global server_last_heartbeat
    
    while not host_connected:
        try:
            sock.sendto(f"HEARTBEAT:{MY_ID}".encode(), RENDEZVOUS_SERVER)
            server_last_heartbeat = time.time()
            time.sleep(args.heartbeat_interval)
        except Exception as e:
            print(f"[ERROR] Server heartbeat error: {e}")
            time.sleep(1)

# Function to send heartbeats to the host (after P2P connection)
def host_heartbeat():
    global host_last_heartbeat, host_connected
    
    while True:
        if host_addr and host_connected:
            try:
                sock.sendto(b"PEER_HEARTBEAT", host_addr)
                time.sleep(args.heartbeat_interval)
            except Exception as e:
                print(f"[ERROR] Host heartbeat error: {e}")
                time.sleep(1)
        else:
            # If host connection is lost, check if we should try to reconnect through server
            if host_last_heartbeat and time.time() - host_last_heartbeat > args.heartbeat_interval * 3:
                print("[WARN] Host connection lost. Trying to reconnect through server...")
                host_connected = False
                # Re-register with server
                sock.sendto(MY_ID.encode(), RENDEZVOUS_SERVER)
            time.sleep(1)

# Function to monitor server and host connection status
def connection_monitor():
    global server_last_heartbeat, host_last_heartbeat, host_connected
    
    while True:
        current_time = time.time()
        
        # Check server connection (important before P2P is established)
        if not host_connected and current_time - server_last_heartbeat > args.heartbeat_interval * 3:
            print("[WARN] Lost connection to rendezvous server. Attempting to reconnect...")
            sock.sendto(MY_ID.encode(), RENDEZVOUS_SERVER)
        
        # Check host connection (after P2P is established)
        if host_connected and host_last_heartbeat:
            if current_time - host_last_heartbeat > args.heartbeat_interval * 3:
                print("[WARN] Host connection lost. Falling back to server...")
                host_connected = False
                # Re-register with server
                sock.sendto(MY_ID.encode(), RENDEZVOUS_SERVER)
        
        time.sleep(args.heartbeat_interval)

# Function to punch a hole and establish P2P with host
def punch():
    global host_connected, host_last_heartbeat
    
    if not host_addr:
        print("[ERROR] No host address available yet")
        return
    
    print(f"[PEER] Punching hole to host at {host_addr}")
    
    # Send several punch packets to establish connection
    for _ in range(10):
        sock.sendto(b"PUNCH", host_addr)
        time.sleep(0.5)
    
    host_connected = True
    host_last_heartbeat = time.time()
    print("[PEER] P2P connection established with host")

# Function to listen for incoming messages
def listen():
    global host_addr, host_connected, server_last_heartbeat, host_last_heartbeat
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            message = data.decode()
            
            # Handle server messages
            if addr == RENDEZVOUS_SERVER:
                server_last_heartbeat = time.time()
                
                if message == "HEARTBEAT_ACK":
                    # Just a heartbeat acknowledgment
                    continue
                elif message == "WAITING_FOR_HOST":
                    print("[PEER] Waiting for host to come online")
                elif message == "HOST_DOWN":
                    print("[WARN] Host is down according to server")
                    host_connected = False
                    host_last_heartbeat = None
                elif message.startswith("REGISTERED:"):
                    print(f"[PEER] Successfully registered with server as {MY_ID}")
                elif message.startswith("HOST_INFO:"):
                    # Format: HOST_INFO:ip:port
                    parts = message.split(':')
                    if len(parts) >= 3:
                        host_ip = parts[1]
                        host_port = int(parts[2])
                        host_addr = (host_ip, host_port)
                        print(f"[PEER] Got host address: {host_addr}")
                        
                        # Start the hole punching process
                        threading.Thread(target=punch, daemon=True).start()
                else:
                    print(f"[SERVER] {message}")
            
            # Handle host messages
            elif host_addr and addr == host_addr:
                host_last_heartbeat = time.time()
                host_connected = True
                
                if message == "PEER_HEARTBEAT":
                    # Just a heartbeat, already updated timestamp
                    continue
                elif message.startswith("PUNCH") or message == "WAITING_FOR_SERVER_INTRO":
                    # Hole punching packet, just acknowledge
                    continue
                else:
                    print(f"[HOST] {message}")
            
            # Message from unknown source
            else:
                print(f"[INFO] Message from unknown source {addr}: {message}")
                
        except Exception as e:
            print(f"[ERROR] in listen thread: {e}")

# Start all the necessary threads
server_heartbeat_thread = threading.Thread(target=server_heartbeat, daemon=True)
server_heartbeat_thread.start()

host_heartbeat_thread = threading.Thread(target=host_heartbeat, daemon=True)
host_heartbeat_thread.start()

monitor_thread = threading.Thread(target=connection_monitor, daemon=True)
monitor_thread.start()

listen_thread = threading.Thread(target=listen, daemon=True)
listen_thread.start()

try:
    # Wait for host information
    while not host_addr:
        print("[PEER] Waiting for host information...")
        time.sleep(2)
    
    # Main loop for user input
    while True:
        msg = input("You: ")
        if not msg:
            continue
            
        if host_connected and host_addr:
            sock.sendto(msg.encode(), host_addr)
        else:
            print("[WARN] Not connected to host yet. Message not sent.")
            
except KeyboardInterrupt:
    print("[PEER] Shutting down...")
    sys.exit(0)