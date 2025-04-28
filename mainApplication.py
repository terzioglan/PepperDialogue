import time
from multiprocessing import Process, Queue

class RecordingHandler(object):
    '''
    this class is responsible for starting/stopping recordings,
    managing available filenames for the recording file buffer,
    and managing recording state object.
    '''
    def __init__(self, config):
        pass

class RecordingFileHandler(object):
    '''
    this class is responsible for copying recording files from pepper,
    denoising them, and transcribing them using the local whisper model,
    then finally returns the transcribed text as well as the filename so that 
    it can be made available for the recording file buffer.
    '''
    def __init__(self,):
        self.running = True
    
    def fetch(self, filename):
        pass
    
    def denoise(self, filename):
        pass

    def transcribe(self, filename):
        filename += '_transcribed'
        return filename
    
    def start(self, recordigFileQueue, transcriptionQueue, recordingFilenameBuffer):
        while self.running:
            try:
                while not recordigFileQueue.empty():
                    filename = recordigFileQueue.get()
                    file = self.fetch(filename)
                    transcriptionQueue.put({filename:"available now"})
                    recordingFilenameBuffer.put(filename)
                    fileDenoised = self.denoise(file)
                    transcription = self.transcribe(filename)
                    transcriptionQueue.put({filename:transcription})
                time.sleep(2)
            except Exception as e:
                print("Error: ", e)

def main():
    transcriptionQueue = Queue(maxsize=100)
    recordingFileQueue = Queue(maxsize=100)
    recordingHandler = RecordingFileHandler()
    recordingHandlerProcess = Process(
        target = recordingHandler.start,
        args = (recordingFileQueue,transcriptionQueue,),)
    recordingHandlerProcess.start()

    filename = "recording"
    i = 0
    try:
        while True:
            recordingFileQueue.put(filename+'_'+str(i))
            while not transcriptionQueue.empty():
                transcription = transcriptionQueue.get()
                print("Got transcription: ", transcription)
            i += 1
            time.sleep(0.2)
    except KeyboardInterrupt:
        recordingHandler.running = False
        recordingHandlerProcess.join()
        print("Exiting main loop.")

if __name__ == "__main__":
    main()