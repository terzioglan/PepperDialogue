import threading, time, sys
sys.path.append("../")
from lib.realtimeWebsocket import RealtimeAPI
from config import realtimeConfig as configuration

if __name__ == "__main__":
    realtimeWebsocket = RealtimeAPI(
        model=configuration.MODEL,
        apiKey=configuration.API_KEY,
        instructions=configuration.INSTRUCTIONS,
        temperature=configuration.TEMPERATURE,
        )
    websocketThread = threading.Thread(target=realtimeWebsocket.runWebsocket)
    websocketThread.start()
    
    while(not (realtimeWebsocket.sessionCreated and realtimeWebsocket.sessionUpdated)):
        print("Waiting to initialize session.")
        time.sleep(1.0)

    while True:
        try:
            inputText = input("User:")
            if inputText == "exit":
                break
            tic = time.time()
            realtimeWebsocket.requestResponse(inputText)
            while(realtimeWebsocket.serverResponseQueue.empty()):
                pass
            toc = time.time()
            
            print("Processing time: %.2fs" %(toc-tic))
            print(f"Response: {realtimeWebsocket.serverResponseQueue.get()}\n")
        except KeyboardInterrupt:
            break
    
    realtimeWebsocket.stopWebsocket()
    websocketThread.join()
    print("Websocket stopped.")
    sys.exit(0)
        