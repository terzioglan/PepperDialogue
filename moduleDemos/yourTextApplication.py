import time, sys
sys.path.append("../")
from config import realtimeConfig as configuration
from lib.serverClient import Client

if __name__ == "__main__":
    realtimeLocalClient = Client(
        host='localhost',
        port=configuration.TCP_PORT,
        size=configuration.TCP_DATA_SIZE
        )
    while True:
        try:
            inputText = input("User:")
            if inputText == "exit":
                break
            tic = time.time()
            realtimeLocalClient.send({"message":inputText})
            response = realtimeLocalClient.receive()["message"]
            toc = time.time()
            
            print("Processing time: %.2fs" %(toc-tic))
            print(f"Response: {response}\n")
        except KeyboardInterrupt:
            break
    sys.exit(0)
        