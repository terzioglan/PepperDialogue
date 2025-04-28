import os, torch, whisper

class WhisperAPI(object):
    def __init__(self, whisperModelPath):
        try:
            if not os.path.exists(whisperModelPath) or not os.path.isfile(whisperModelPath):   # If model not present, load model.
                print("Whisper model doesn't exist locally. Downloading.")
                self.modelName = whisperModelPath.split("/")[-1].split("_")[1]
                self.model = whisper.load_model(self.modelName)   # turbo, tiny, base, etc.
                torch.save(self.model, whisperModelPath)
            self.model = torch.load(whisperModelPath, weights_only=False)
            print("Whisper model loaded successfully!", flush=True)
        except Exception as e:
            print("Error loading whisper model: ", e, flush=True)
    
    def transcribeAudio(self, audioFilePath): 
        return self.model.transcribe(audioFilePath)["text"]
