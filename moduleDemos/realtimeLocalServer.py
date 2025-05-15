import threading, time, sys
sys.path.append("../")
from lib.realtimeWebsocket import RealtimeAPI
from config import realtimeConfig as configuration
from lib.serverClient import Server

if __name__ == "__main__":
    realtimeWebsocket = RealtimeAPI(
        model=configuration.MODEL,
        apiKey=configuration.API_KEY,
        instructions=configuration.INSTRUCTIONS,
        temperature=configuration.TEMPERATURE,
        )
    websocketThread = threading.Thread(target=realtimeWebsocket.runWebsocket)
    websocketThread.start()

    realtimeLocalServer = Server(
        host="localhost",
        port=configuration.TCP_PORT,
        size=configuration.TCP_DATA_SIZE
        )

    while(not (realtimeWebsocket.sessionCreated and realtimeWebsocket.sessionUpdated)):
        print("Waiting to initialize session.")
        time.sleep(1.0)

    while True:
        try:
            data = realtimeLocalServer.receive(configuration.TCP_DATA_SIZE)
            realtimeWebsocket.requestResponse(data["message"])
            while(realtimeWebsocket.serverResponseQueue.empty()):
                pass
            realtimeLocalServer.send({"message":realtimeWebsocket.serverResponseQueue.get()})
        except KeyboardInterrupt:
            break

    realtimeWebsocket.stopWebsocket()
    websocketThread.join()
    print("Websocket stopped.")
    realtimeLocalServer.exit()
    sys.exit(0)
