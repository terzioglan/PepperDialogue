import sys
from lib.localWhisperAPI import WhisperAPI
from configuration import configuration
from lib.serverClient import Server

if __name__ == "__main__":
    whisperApi = WhisperAPI(whisperModelPath=configuration.whisperModelPath,)

    whisperLocalServer = Server(host="localhost", port=configuration.tcp_port_whisper)

    while True:
        try:
            audioFilePath = whisperLocalServer.receive(configuration.tcp_data_size)["message"]
            transcription = whisperApi.transcribeAudio(audioFilePath)
            whisperLocalServer.send({"message":transcription})
        except KeyboardInterrupt:
            whisperLocalServer.exit()
            sys.exit(0)
