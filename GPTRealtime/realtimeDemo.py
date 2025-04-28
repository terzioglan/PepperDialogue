import threading, time, sys
from lib.realtimeWebsocketAPI import RealtimeAPI
from configuration import configuration

if __name__ == "__main__":
    realtimeWebsocket = RealtimeAPI(
        model=configuration.realtimeModel,
        apiKey=configuration.api_key,
        instructions=configuration.instructions,
        temperature=configuration.temperature,
        )
    websocketThread = threading.Thread(target=realtimeWebsocket.runWebsocket)
    websocketThread.start()
    while(not (realtimeWebsocket.sessionCreated and realtimeWebsocket.sessionUpdated)):
        print("Waiting to initialize session.")
        time.sleep(1.0)

    while True:
        try:
            inputText = input("User:")

            tic = time.time()
            realtimeWebsocket.requestUserResponse(inputText)
            while(realtimeWebsocket.serverResponseQueue.empty()):
                pass
            toc = time.time()
            
            print("Processing time: %.2fs" %(toc-tic))
            print(f"Response: {realtimeWebsocket.serverResponseQueue.get()}\n")
        except KeyboardInterrupt:
            realtimeWebsocket.stopWebsocket()
            websocketThread.join()
            print("Websocket stopped.")
            sys.exit(0)
        