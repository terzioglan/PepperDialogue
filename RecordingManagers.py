# python2

import time

from config import BUFFERED_RECORDING_FILENAMES, IDLE_MICROPHONE_RECORDING_DURATION, LISTENING_PADDING_DURATION, REMOTE_AUDIO_FILE_PATH
from config import LISTENING_PADDING_DURATION

class RecordingHandler(object):
    '''
    this class is responsible for starting/stopping recordings,
    managing available filenames for the recording file buffer,
    and managing recording state object.
    '''
    def __init__(self, recordingService):
        self.stop = False
        self.recordingService = recordingService
    
    def startRecording(self,filename, microphoneArray = [1,1,1,1], bitrate = 16000):
        try:
            print("Recording started...")
            self.recordingService.startMicrophonesRecording(REMOTE_AUDIO_FILE_PATH + filename, "wav", bitrate, microphoneArray)
        except Exception as e:
            print("couldn't start recording: ", e)
        else:
            return
    
    def stopRecording(self,):
        try:
            self.recordingService.stopMicrophonesRecording()
            print("Recording stopped...")
        except Exception as e:
            print("couldn't stop recording: ", e)

    
    def discardRecording(self,recordingFilenameBufferQueue, currentFilename):
        recordingFilenameBufferQueue.put(currentFilename)
    
    def acceptRecording(self, recordingFileQueue, currentFilename):
        recordingFileQueue.put(currentFilename)

    def start(self, recordingState, robotState, humanState, recordingFileQueue, recordingFilenameBufferQueue):
        for filename in BUFFERED_RECORDING_FILENAMES:
            recordingFilenameBufferQueue.put(filename)

        while not self.stop:
            if not recordingFilenameBufferQueue.empty():
                currentFilename = recordingFilenameBufferQueue.get()
                recordingState.setAttributes({
                    "currentFile": currentFilename,
                    "containsSpeech": False,
                    })
                
                if robotState.getAttributes(['canListen']):
                    recordingState.setAttributes({
                        "startTime": time.time(),
                        "recording": True,
                        })
                    self.startRecording(currentFilename)
                    startTime = time.time()
                    while((((time.time() - startTime) < IDLE_MICROPHONE_RECORDING_DURATION) and 
                          robotState.getAttributes(['canListen'])) or
                          humanState.getAttributes(['speaking'])):
                        if recordingState.getAttributes(['containsSpeech']):
                            if not humanState.getAttributes['speaking']:
                                paddingStartTime = time.time()
                                while not humanState.getAttributes(['speaking']) or (time.time() - paddingStartTime) < LISTENING_PADDING_DURATION:
                                    print("Padding recording...")
                                    pass
                    self.stopRecording()

                    if recordingState.getAttributes(['containsSpeech']):
                        self.acceptRecording(recordingFileQueue, currentFilename)
                    else:
                        self.discardRecording(recordingFilenameBufferQueue, currentFilename)

class RecordingFileHandler(object):
    '''
    this class is responsible for copying recording files from pepper,
    denoising them, and transcribing them using the local whisper model,
    then finally returns the transcribed text as well as the filename so that 
    it can be made available for the recording file buffer.
    '''
    def __init__(self,recordingFilenameBufferQueue):
        self.stop = False
    
    def fetch(self, filename):
        pass
    
    def denoise(self, filename):
        pass

    def transcribe(self, filename):
        filename += '_transcribed'
        return filename
    
    def start(self, recordingFileQueue, transcriptionQueue, recordingFilenameBufferQueue):
        while not self.stop:
            try:
                while not recordingFileQueue.empty():
                    filename = recordingFileQueue.get()
                    file = self.fetch(filename)
                    transcriptionQueue.put({filename:"available now"})
                    recordingFilenameBufferQueue.put(filename)
                    fileDenoised = self.denoise(file)
                    transcription = self.transcribe(filename)
                    transcriptionQueue.put({filename:transcription})
                time.sleep(2)
            except Exception as e:
                print("Error: ", e)