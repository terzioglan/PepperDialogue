import time, sys
from configuration import configuration
from lib.serverClient import Client

if __name__ == "__main__":
    realtimeLocalClient = Client(host='localhost', port=configuration.tcp_port_realtime)
    while True:
        try:
            inputText = input("User:")

            tic = time.time()
            realtimeLocalClient.send({"message":inputText})
            response = realtimeLocalClient.receive(configuration.tcp_data_size)["message"]
            toc = time.time()
            
            print("Processing time: %.2fs" %(toc-tic))
            print(f"Response: {response}\n")
        except KeyboardInterrupt:
            sys.exit(0)
        