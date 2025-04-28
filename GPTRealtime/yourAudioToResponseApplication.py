import time, sys
from configuration import configuration
from lib.serverClient import Client

if __name__ == "__main__":
    realtimeLocalClient = Client(host='localhost', port=configuration.tcp_port_realtime)
    whisperLocalClient = Client(host='localhost', port=configuration.tcp_port_whisper)
    while True:
        try:
            audioFilePath = "./hello-278029.mp3"
            whisperLocalClient.send({"message":audioFilePath})
            transcription = whisperLocalClient.receive(configuration.tcp_data_size)["message"]
            print(f"Transcription: {transcription}\n")

            realtimeLocalClient.send({"message":transcription})
            response = realtimeLocalClient.receive(configuration.tcp_data_size)["message"]
            
            print(f"Response: {response}\n")
            input("Enter to repeat...")
        except KeyboardInterrupt:
            realtimeLocalClient.exit()
            whisperLocalClient.exit()
            sys.exit(0)
        