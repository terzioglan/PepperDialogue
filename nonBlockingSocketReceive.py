import socket
import select

def handle_data(data):
    # Process the received data
    print(f"Received data: {data.decode()}")

def server_program():
    host = '127.0.0.1'
    port = 12345

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    server_socket.setblocking(0)  # Set socket to non-blocking mode

    inputs = [server_socket]

    print(f"Server listening on {host}:{port}")

    while True:
        readable, _, _ = select.select(inputs, [], [])

        for s in readable:
            if s is server_socket:
                client_socket, addr = server_socket.accept()
                inputs.append(client_socket)
                print(f"Connection from {addr}")
            else:
                try:
                    data = s.recv(1024)
                    if data:
                        handle_data(data)
                    else:
                        # Client disconnected
                        inputs.remove(s)
                        s.close()
                        print("Client disconnected")
                except ConnectionResetError:
                     # Handle the case where the client forcibly closed the connection
                    inputs.remove(s)
                    s.close()
                    print("Client forcibly disconnected")
                except Exception as e:
                    print(f"Error receiving data: {e}")
                    inputs.remove(s)
                    s.close()

if __name__ == "__main__":
    server_program()