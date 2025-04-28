import threading, time, sys
from lib.realtimeWebsocketAPI import RealtimeAPI
from configuration import configuration
from lib.serverClient import Server

if __name__ == "__main__":
    realtimeWebsocket = RealtimeAPI(
        model=configuration.realtimeModel,
        apiKey=configuration.api_key,
        instructions=configuration.instructions,
        temperature=configuration.temperature,
        )
    websocketThread = threading.Thread(target=realtimeWebsocket.runWebsocket)
    websocketThread.start()

    realtimeLocalServer = Server(host="localhost", port=configuration.tcp_port_realtime)

    while(not (realtimeWebsocket.sessionCreated and realtimeWebsocket.sessionUpdated)):
        print("Waiting to initialize session.")
        time.sleep(1.0)

    while True:
        try:
            data = realtimeLocalServer.receive(configuration.tcp_data_size)
            realtimeWebsocket.requestUserResponse(data["message"])
            while(realtimeWebsocket.serverResponseQueue.empty()):
                pass
            realtimeLocalServer.send({"message":realtimeWebsocket.serverResponseQueue.get()})
        except KeyboardInterrupt:
            realtimeWebsocket.stopWebsocket()
            websocketThread.join()
            print("Websocket stopped.")
            realtimeLocalServer.exit()
            sys.exit(0)
        