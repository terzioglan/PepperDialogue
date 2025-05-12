# python2
import time, ffmpeg, os, re

from lib.utils import fixNameConflicts

class RecordingManager(object):
    '''
    this class is responsible for starting/stopping recordings,
    managing available filenames for the recording file buffer,
    and managing recording state object.
    '''
    def __init__(self, method_startRecording, method_stopRecording, config, verbose = False):
        self.stop = False
        self.configuration = config
        self.method_startRecording = method_startRecording
        self.method_stopRecording = method_stopRecording
        self.transcriptionClient = None
        self.verbose = verbose
    
    def startRecording(self,filename,):
        try:
            self.method_startRecording(self.configuration.SOURCE_AUDIO_FILE_PATH + filename, "wav",  16000, [1,1,1,1])
            # print("Recording started...")
        except Exception as e:
            print("couldn't start recording: ", e)
        else:
            return
    
    def stopRecording(self,):
        try:
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
                if robotState.getAttribute('canListen'):
                    currentFilename = queue_recordingFilenameBuffer.get()
                    recordingState.setAttributes({
                        "currentFile": currentFilename,
                        "containsSpeech": False,
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
                        if self.verbose: print("accepting recording", currentFilename)
                        self.acceptRecording(queue_recordingsWithSpeech, currentFilename)
                    else:
                        if self.verbose: print("discarding recording", currentFilename)
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
        print("Recording manager stopped.")

class RecordingHandler(object):
    '''
    this class is responsible for copying recording files from pepper,
    denoising them, and transcribing them using the local whisper model,
    then finally returns the transcribed text as well as the filename so that 
    it can be made available for the recording file buffer.
    '''
    def __init__(self, 
                 method_fetchRecording, 
                 config,
                 denoising = True, 
                 noiseSuppressionHeader = "./noiseSuppressionHeader.wav", 
                 noiseSuppressionCharSet =  r'f\W*f\W*m\W*[pb]\W*g\W*',
                 transcriptionClient = None,
                 verbose = True,
                 ):
        if noiseSuppressionHeader is not None and noiseSuppressionCharSet is None:
            raise ValueError("You must provide a character set to be removed from transcriptions to use noise supperssion headers.")
        self.stop = False
        self.configuration = config
        self.denoising = denoising
        self.noiseSuppressionHeader = noiseSuppressionHeader
        self.noiseSuppressionHeaderCharacters = noiseSuppressionCharSet
        self.method_fetchRecording = method_fetchRecording
        self.transcriptionClient = transcriptionClient
        self.verbose = verbose
    
    def fetch(self, remotePath, localPath, filename):
        extension = "."+filename.split('.')[-1]
        defaultNewFilename = self.configuration.DEFAULT_NEW_AUDIO_FILE_NAME+extension
        copied = self.method_fetchRecording(
            remotePath+filename, 
            localPath+defaultNewFilename)
        uniqueFilename = fixNameConflicts(localPath+filename)
        os.rename(localPath+defaultNewFilename,
                  uniqueFilename)
        return uniqueFilename
    
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
        if self.verbose: print("requesting transcription for: ", filename)
        self.transcriptionClient.send({"audioFile":filename})
        response = self.transcriptionClient.receive()
        return response["transcription"]
    
    def start(self, recordingState, queue_recordingsWithSpeech, queue_recordingFilenameBuffer, queue_transcriptions,):
        while not self.stop:
            try:
                while not queue_recordingsWithSpeech.empty():
                    filename = queue_recordingsWithSpeech.get()
                    if self.verbose: print("recording with speech detected", filename)
                    targetFile = self.fetch(self.configuration.SOURCE_AUDIO_FILE_PATH, self.configuration.LOCAL_AUDIO_FILE_PATH, filename)
                    print("releasing filename: ", filename)
                    queue_recordingFilenameBuffer.put(filename)
                    if self.noiseSuppressionHeader is not None:
                        if self.verbose: print("appending noise suppression header to: ", targetFile)
                        targetFile = self.appendSuppressionHeader(targetFile)
                    if self.denoising:
                        if self.verbose: print("denoising: ", targetFile)
                        targetFile = self.denoise(targetFile)
                    if self.verbose: print("transcribing: ", targetFile)
                    transcription = self.requestTranscription(targetFile)
                    if self.noiseSuppressionHeader is not None:
                        transcription = re.sub(self.noiseSuppressionHeaderCharacters, "", transcription.lower()).strip()
                    if self.verbose: print("transcription: ", transcription)
                    queue_transcriptions.put({targetFile:transcription})
                    if queue_recordingsWithSpeech.empty():
                        if recordingState.getSetAttributes(conditions={"containsSpeech": False}, setAttrDict={"pipelineClear": True}):
                            if self.verbose: print("pipeline clear")
                    else:
                        if self.verbose: print("pipeline NOT clear")

            except Exception as e:
                print("Exception in recording handler: ", e)
        print("Recording handler stopped.")
