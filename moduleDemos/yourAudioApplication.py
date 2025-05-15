import sys, time
sys.path.append("../")
from config import realtimeConfig as realtimeConfiguration
from config import whisperConfig as whisperConfiguration
from lib.serverClient import Client

RECORDINGS = [
    "../testCode/testAudio/goodbye-38072.mp3",
    "../testCode/testAudio/hello-46355.mp3",
    "../testCode/testAudio/thank-you-99932.mp3",
    "../testCode/testAudio/welcome-to-paradise-96902.mp3",
    "../testCode/testAudio/welcome-traveler-97167.mp3",
    ]

if __name__ == "__main__":
    realtimeLocalClient = Client(
        host='localhost',
        port=realtimeConfiguration.TCP_PORT,
        size=realtimeConfiguration.TCP_DATA_SIZE
        )
    whisperLocalClient = Client(
        host='localhost',
        port=whisperConfiguration.TCP_PORT,
        size=whisperConfiguration.TCP_DATA_SIZE
        )
    for recording in RECORDINGS:
        try:
            audioFilePath = recording
            tic = time.time()
            whisperLocalClient.send({"message":audioFilePath})
            transcription = whisperLocalClient.receive()["message"]
            print(f"Transcription: {transcription}\n")

            realtimeLocalClient.send({"message":transcription})
            response = realtimeLocalClient.receive()["message"]
            
            print(f"Response: {response}\n")
            toc = time.time()
            print("Processing time: %.2fs" %(toc-tic))
            time.sleep(1.0)
        except KeyboardInterrupt:
            break
    
    realtimeLocalClient.exit()
    whisperLocalClient.exit()
    sys.exit(0)
