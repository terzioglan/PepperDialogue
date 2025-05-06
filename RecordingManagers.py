# python2
import time, ffmpeg, os

import config
from utils import fixNameConflicts

class RecordingManager(object):
    '''
    this class is responsible for starting/stopping recordings,
    managing available filenames for the recording file buffer,
    and managing recording state object.
    '''
    def __init__(self, method_startRecording, method_stopRecording, config=config):
        self.stop = False
        self.configuration = config
        self.method_startRecording = method_startRecording
        self.method_stopRecording = method_stopRecording
    
    # def startRecording(self,filename, microphoneArray = [1,1,1,1], bitrate = 16000):
    def startRecording(self,filename,):
        try:
            # print("Recording started...")
            # self.recordingService.startMicrophonesRecording(SOURCE_AUDIO_FILE_PATH + filename, "wav", bitrate, microphoneArray)
            self.method_startRecording(self.configuration.SOURCE_AUDIO_FILE_PATH + filename, "wav", bitrate = 16000, microphoneArray = [1,1,1,1])
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
        for filename in self.configuration.BUFFERED_RECORDING_FILENAMES:
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
                        ((((time.time() - startTime) < self.configuration.IDLE_MICROPHONE_RECORDING_DURATION) and robotState.getAttribute('canListen')) or
                            humanState.getAttribute('speaking')) and
                          not padding):
                        if recordingState.getAttribute('containsSpeech'):
                            if not humanState.getAttribute('speaking'):
                                paddingStartTime = time.time()
                                padding = True
                                while (time.time() - paddingStartTime) < self.configuration.LISTENING_PADDING_DURATION:
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
                 noiseSuppressionHeader = "./noiseSuppressionHeader.wav", 
                 noiseSuppressionCharSet =  r'f\W*f\W*m\W*[pb]\W*g\W*',
                 config = config,
                 ):
        if noiseSuppressionHeader is not None and noiseSuppressionCharSet is None:
            raise ValueError("You must provide a character set to be removed from transcriptions to use noise supperssion headers.")
        self.stop = False
        self.configuration = config
        self.denoising = denoising
        self.noiseSuppressionHeader = noiseSuppressionHeader
        self.noiseSuppressionHeaderCharacters = noiseSuppressionCharSet
        self.method_fetchRecording = method_fetchRecording
    
    def fetch(self, remotePath, localPath, filename):
        extension = filename.split('.')[-1]
        copiedFile = self.method_fetchRecording(
            remotePath+filename, 
            localPath+self.configuration.DEFAULT_NEW_AUDIO_FILE_NAME+extension)
        newFile = fixNameConflicts(localPath+filename)
        os.rename(copiedFile,
                  newFile)
        # print("here")
        # os.rename(localPath+filename, newFile)
        # print("but not here")
        return newFile
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
    
    def appendSuppressionHeader(self, recordingFile):
        extension = '.' + recordingFile.split(".")[-1]
        outputFile = recordingFile.replace(extension,'') + "_header" + extension
        try:
            # Create a temporary file and write the list of audio files to concatenate
            audioFilesList = 'audioFiles.txt'
            with open(audioFilesList, 'w') as f:
                f.write("file '{0}'\n".format(self.noiseSuppressionHeader))
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

    def requestTranscription(self, filename):
        filename += '_transcribed'
        time.sleep(2.0)
        return filename
    
    def start(self, recordingState, queue_recordingsWithSpeech, queue_recordingFilenameBuffer, queue_transcriptions,):
        while not self.stop:
            try:
                while not queue_recordingsWithSpeech.empty():
                    filename = queue_recordingsWithSpeech.get()
                    targetFile = self.fetch(self.configuration.SOURCE_AUDIO_FILE_PATH, self.configuration.LOCAL_AUDIO_FILE_PATH, filename)
                    queue_recordingFilenameBuffer.put(filename)
                    if self.noiseSuppressionHeader is not None:
                        targetFile = self.appendSuppressionHeader(targetFile)
                    if self.denoising:
                        targetFile = self.denoise(targetFile)
                    transcription = self.requestTranscription(targetFile)
                    queue_transcriptions.put({filename:transcription})
                    if queue_recordingsWithSpeech.empty():
                        recordingState.getSetAttributes(conditions={"containsSpeech": False}, setAttrDict={"pipelineClear": True})
                        print("pipeline clear")
                    else:
                        print("pipeline NOT clear")

            except Exception as e:
                print("Error: ", e)