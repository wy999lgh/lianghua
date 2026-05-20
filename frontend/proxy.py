#!/usr/bin/env python3
import socket
import threading
import sys

def handle_client(client_socket, target_host, target_port):
    try:
        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_socket.connect((target_host, target_port))
        
        def forward(source, destination):
            try:
                while True:
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.sendall(data)
            except:
                pass
            finally:
                try:
                    source.close()
                except:
                    pass
                try:
                    destination.close()
                except:
                    pass
        
        threading.Thread(target=forward, args=(client_socket, target_socket), daemon=True).start()
        threading.Thread(target=forward, args=(target_socket, client_socket), daemon=True).start()
    except Exception as e:
        print(f"Connection error: {e}")
        client_socket.close()

def start_proxy(listen_port, target_host, target_port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', listen_port))
    server.listen(100)
    print(f"Proxy listening on port {listen_port} -> {target_host}:{target_port}")
    
    try:
        while True:
            client_socket, addr = server.accept()
            print(f"Connection from {addr}")
            threading.Thread(
                target=handle_client,
                args=(client_socket, target_host, target_port),
                daemon=True
            ).start()
    except KeyboardInterrupt:
        print("\nProxy stopped")
    finally:
        server.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python proxy.py <listen_port> <target_host> <target_port>")
        sys.exit(1)
    
    listen_port = int(sys.argv[1])
    target_host = sys.argv[2]
    target_port = int(sys.argv[3])
    
    start_proxy(listen_port, target_host, target_port)
