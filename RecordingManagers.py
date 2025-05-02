# python2

import time, ffmpeg, os

from config import BUFFERED_RECORDING_FILENAMES, IDLE_MICROPHONE_RECORDING_DURATION, LISTENING_PADDING_DURATION, SOURCE_AUDIO_FILE_PATH, LOCAL_AUDIO_FILE_PATH
from config import LISTENING_PADDING_DURATION
from utils import fixNameConflicts

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
            # self.recordingService.startMicrophonesRecording(SOURCE_AUDIO_FILE_PATH + filename, "wav", bitrate, microphoneArray)
            self.method_startRecording(SOURCE_AUDIO_FILE_PATH + filename, "wav", bitrate = 16000, microphoneArray = [1,1,1,1])
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
    def __init__(self, 
                 method_fetchRecording, 
                 denoising = True, 
                 noiseSuppressionHeader = None, 
                 noiseSuppressionCharSet = None,
                 ):
        if noiseSuppressionHeader is not None and noiseSuppressionCharSet is None:
            raise ValueError("You must provide a character set to be removed from transcriptions to use noise supperssion headers.")
        self.stop = False
        self.denoising = denoising
        self.noiseSuppressionHeader = noiseSuppressionHeader
        self.noiseSuppressionHeaderCharacters = noiseSuppressionCharSet
        self.method_fetchRecording = method_fetchRecording
        self.defaultAudioName = "localRec"
    
    def fetch(self, remotePath, localPath, filename):
        self.method_fetchRecording(remotePath+filename, local_path=localPath)
        newFilename = fixNameConflicts(localPath+self.defaultAudioName, '.'+filename.split('.')[-1])
        os.rename(localPath+filename,localPath+newFilename)
        return localPath+newFilename
        # while not self.recordingsWaitingForCopy.empty():
        #     self.nRecordings += 1
        #     targetRecording = self.recordingsWaitingForCopy.get()
        #     print("retrieving audio file from pepper: " + str(targetRecording))
        #     self.secureCopyProtocolService.get(self.remoteFileStoragePath+targetRecording, local_path=self.localFileStoragePath)
        #     fixNameConflicts(self.defaultAudioName, targetRecording[-4:])
        #     self.newAudioFileName = str(self.nRecordings) + targetRecording
        #     os.rename(self.localFileStoragePath+targetRecording,self.localFileStoragePath+self.newAudioFileName)
        #     self.recordingQueue.put(self.newAudioFileName)
        #     self.recordingBufferFilenames.put(targetRecording)

        # self.secureCopyProtocolService.close()

    
    def denoise(self, inputFile):
        extension = '.' + inputFile.split(".")[-1]
        outputFile = inputFile.rstrip(extension) + "_denoised" + extension
        try:
            (
                ffmpeg
                .input(inputFile)                                                           # Takes 'microphoneTest.wav'
                .output(outputFile, af="highpass=f=200, lowpass=f=3000, afftdn=nf=-20")     # Gives 'microphoneTest_denoised.wav'
                .overwrite_output()                                                         # To automatically overwrite file incase prompted
                .global_args('-loglevel', 'quiet')                                          # Hide logs
                .run()
            )
            return outputFile
        except Exception as e:
            print("denoising error: ", e)
            return inputFile
    
    def appendSuppressionHeader(self, headerFile, recordingFile):
        extension = '.' + recordingFile.split(".")[-1]
        outputFile = recordingFile.rstrip(extension) + "_header" + extension
        try:
            # Create a temporary file and write the list of audio files to concatenate
            audioFilesList = 'audioFiles.txt'
            with open(audioFilesList, 'w') as f:
                f.write("file '{0}'\n".format(headerFile))
                f.write("file '{0}'\n".format(recordingFile))

            (
                ffmpeg
                .input(audioFilesList, format='concat', safe=0)     # Concat files
                .output(outputFile, acodec='copy')                  # Outputs 'microphoneTest_denoised_header.wav'
                .overwrite_output()                                 # To automatically overwrite file in case prompted
                .global_args('-loglevel', 'quiet')                  # Hide logs
                .run()
            )     
            os.remove(audioFilesList)                               # Remove the temporary file
            return outputFile
        except Exception as e:
            print("concatenating error: ", e)
            return recordingFile

    def transcribe(self, filename):
        filename += '_transcribed'
        return filename
    
    def start(self, recordingState, queue_recordingsWithSpeech, queue_recordingFilenameBuffer, queue_transcriptions,):
        while not self.stop:
            try:
                while not queue_recordingsWithSpeech.empty():
                    filename = queue_recordingsWithSpeech.get()
                    copiedFile = self.fetch(SOURCE_AUDIO_FILE_PATH, LOCAL_AUDIO_FILE_PATH, filename)
                    queue_recordingFilenameBuffer.put(filename)
                    if self.noiseSuppressionHeader is not None:
                        copiedFileWithHeader = self.appendSuppressionHeader(copiedFile)
                    if self.denoising:
                        copiedFileWithHeaderDenoised = self.denoise(copiedFileWithHeader)
                    transcription = self.transcribe(copiedFileWithHeaderDenoised)
                    queue_transcriptions.put({filename:transcription})
                    if queue_recordingsWithSpeech.empty():
                        recordingState.getSetAttributes({"containsSpeech": False}, {"pipelineClear": True})
                        print("pipeline clear")

            except Exception as e:
                print("Error: ", e)