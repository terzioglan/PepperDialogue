import json, queue, websocket, threading, time, sys
from lib.utils import GptCostTracker
from lib.serverClient import Server

from configuration import configuration

class RealtimeAPI(object):
    def __init__(self, model, apiKey, instructions, temperature):
        self.url = "wss://api.openai.com/v1/realtime?model="+model
        self.headers = [
            "Authorization: " + apiKey,
            "OpenAI-Beta: realtime=v1"
        ]
        self.instructions = instructions
        self.temperature = temperature
        self.costTracker = GptCostTracker(model = model)
        self.webSocket = None
        self.serverResponseQueue = queue.Queue()
        self.stopEvent = threading.Event()
        self.sessionCreated = False
        self.sessionUpdated = False

    def onOpen(self, webSocket):
        ''' This function is called once the websocket is opened. '''
        session_event = {
            "type": "session.update",
            "session": {
                "modalities": [ "text" ],
                "instructions": self.instructions,
                "temperature": self.temperature
            }
        }
        self.webSocket.send(json.dumps(session_event))  # Send session event to realtime server

    def onMessage(self, webSocket, message):
        ''' This function is triggered when realtime server sends a response back. '''
        data = json.loads(message)
        if data['type'] == "response.done":
            realtime_server_response = data['response']['output'][0]['content'][0]['text']
            self.serverResponseQueue.put(realtime_server_response)
            self.costTracker.computeCost(response=data['response'])
            # print("Last requests cost: $%2.7f, session total cost: $%2.7f" %(self.costTracker.latestRequestCost, self.costTracker.totalCost))
        elif data['type'] == "session.created":
            self.sessionCreated = True
        elif data['type'] == "session.updated":
            print(data)
            self.sessionUpdated = True
            
    def runWebsocket(self):
        ''' Establish the websocket communication. '''
        self.webSocket = websocket.WebSocketApp(
                self.url,
                header=self.headers,
                on_open=self.onOpen,
                on_message=self.onMessage,
            )
        self.webSocket.run_forever()
    
    def stopWebsocket(self):
        if self.webSocket:
            self.webSocket.close()
        self.stopEvent.set()

    def requestUserResponse(self, userInput):
        ''' userInput text is sent to Realtime server, and the server is asked for a response'''                
        # Create the conversation item
        conversation_event = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": userInput # Audio transcription by local whisper
                    }
                ]
            }
        }
        # Trigger a response
        response_event = {
            "type": "response.create",
            "response": {
                "modalities": [ "text" ],
            }
        }
        
        self.webSocket.send(json.dumps(conversation_event))
        self.webSocket.send(json.dumps(response_event))

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
        