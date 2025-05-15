import sys
sys.path.append("../")
from lib.whisperLocal import WhisperAPI
from config import whisperConfig as configuration
from lib.serverClient import Server

if __name__ == "__main__":
    whisperApi = WhisperAPI(whisperModelPath=configuration.WHISPER_MODEL_FILE,)

    whisperLocalServer = Server(
        host="localhost",
        port=configuration.TCP_PORT,
        size=configuration.TCP_DATA_SIZE
        )

    while True:
        try:
            audioFilePath = whisperLocalServer.receive(configuration.TCP_DATA_SIZE)["message"]
            transcription = whisperApi.transcribeAudio(audioFilePath)
            whisperLocalServer.send({"message":transcription})
        except KeyboardInterrupt:
            break
    
    whisperLocalServer.exit()
    sys.exit(0)
