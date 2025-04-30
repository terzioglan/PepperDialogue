# python2

import time

from config import BUFFERED_RECORDING_FILENAMES, IDLE_MICROPHONE_RECORDING_DURATION, LISTENING_PADDING_DURATION, REMOTE_AUDIO_FILE_PATH
from config import LISTENING_PADDING_DURATION

class RecordingManager(object):
    '''
    this class is responsible for starting/stopping recordings,
    managing available filenames for the recording file buffer,
    and managing recording state object.
    '''
    def __init__(self, method_startRecording, method_stopRecording):
        self.stop = False
        self.method_startRecording = method_startRecording
        self.method_stopRecording = method_stopRecording
    
    # def startRecording(self,filename, microphoneArray = [1,1,1,1], bitrate = 16000):
    def startRecording(self,filename,):
        try:
            # print("Recording started...")
            # self.recordingService.startMicrophonesRecording(REMOTE_AUDIO_FILE_PATH + filename, "wav", bitrate, microphoneArray)
            self.method_startRecording(REMOTE_AUDIO_FILE_PATH + filename, "wav", bitrate = 16000, microphoneArray = [1,1,1,1])
        except Exception as e:
            print("couldn't start recording: ", e)
        else:
            return
    
    def stopRecording(self,):
        try:
            # self.recordingService.stopMicrophonesRecording()
            self.method_stopRecording()
            # print("Recording stopped...")
        except Exception as e:
            print("couldn't stop recording: ", e)

    
    def discardRecording(self,queue_recordingFilenameBuffer, currentFilename):
        queue_recordingFilenameBuffer.put(currentFilename)
    
    def acceptRecording(self, queue_recordingsWithSpeech, currentFilename):
        queue_recordingsWithSpeech.put(currentFilename)

    def start(self, recordingState, robotState, humanState, queue_recordingsWithSpeech, queue_recordingFilenameBuffer):
        for filename in BUFFERED_RECORDING_FILENAMES:
            queue_recordingFilenameBuffer.put(filename)

        while not self.stop:
            padding = False
            if not queue_recordingFilenameBuffer.empty():
                currentFilename = queue_recordingFilenameBuffer.get()
                recordingState.setAttributes({
                    "currentFile": currentFilename,
                    "containsSpeech": False,
                    })
                
                if robotState.getAttribute('canListen'):
                    recordingState.setAttributes({
                        "startTime": time.time(),
                        "recording": True,
                        })
                    self.startRecording(currentFilename)
                    startTime = time.time()
                    while(
                        ((((time.time() - startTime) < IDLE_MICROPHONE_RECORDING_DURATION) and robotState.getAttribute('canListen')) or
                            humanState.getAttribute('speaking')) and
                          not padding):
                        if recordingState.getAttribute('containsSpeech'):
                            if not humanState.getAttribute('speaking'):
                                paddingStartTime = time.time()
                                padding = True
                                while (time.time() - paddingStartTime) < LISTENING_PADDING_DURATION:
                                    if humanState.getAttribute('speaking'):
                                        paddingStartTime = time.time()
                                    # print("Padding recording...")
                                    pass
                    self.stopRecording()
                    if recordingState.getAttribute('containsSpeech'):
                        print("accepting recording")
                        self.acceptRecording(queue_recordingsWithSpeech, currentFilename)
                    else:
                        print("discarding recording")
                        self.discardRecording(queue_recordingFilenameBuffer, currentFilename)

                    recordingState.setAttributes({
                        "recording": False,
                        "startTime": -1.0,
                        "currentFile": '',
                        "containsSpeech": False,
                        })
            else:
                print("recording buffer filename queue empty!")
                time.sleep(0.5)

class RecordingHandler(object):
    '''
    this class is responsible for copying recording files from pepper,
    denoising them, and transcribing them using the local whisper model,
    then finally returns the transcribed text as well as the filename so that 
    it can be made available for the recording file buffer.
    '''
    def __init__(self,denoising = True, noiseSuppressionHeader = None, noiseSuppressionCharSet = None):
        if noiseSuppressionHeader is not None and noiseSuppressionCharSet is None:
            raise ValueError("You must provide characters to be removed from transcriptions to use noise supperssion headers.")
        self.stop = False
        self.denoising = denoising
        self.noiseSuppressionHeader = noiseSuppressionHeader
        self.noiseSuppressionHeaderCharacters = noiseSuppressionCharSet
    
    def fetch(self, method_fetchFile, filename):
        pass
    
    def denoise(self, filename):
        pass

    def transcribe(self, filename):
        filename += '_transcribed'
        return filename
    
    def start(self, queue_recordingsWithSpeech, queue_transcriptions, queue_recordingFilenameBuffer, method_fetchFile):
        while not self.stop:
            try:
                while not queue_recordingsWithSpeech.empty():
                    filename = queue_recordingsWithSpeech.get()
                    file = self.fetch(method_fetchFile, filename)
                    queue_recordingFilenameBuffer.put(filename)
                    fileDenoised = self.denoise(file)
                    transcription = self.transcribe(fileDenoised)
                    queue_transcriptions.put({filename:transcription})
            except Exception as e:
                print("Error: ", e)