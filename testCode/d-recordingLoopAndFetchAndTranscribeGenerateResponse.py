# python2

import time, sys, shutil, subprocess
sys.path.append("../")
from multiprocessing import Queue
from threading import Thread

from lib.recordingManagers import RecordingHandler, RecordingManager
from lib.states import RobotState, RecordingState, HumanState
from testConfig import recordingTestConfig
from config import whisperConfig, realtimeConfig
from lib.serverClient import Client

def startRecording(filename, extension, bitrate, microphoneArray):
    time.sleep(0.2)
    print("recording started")
def stopRecording():
    time.sleep(0.1)
    print("recording stopped")

def fetchRecording(sourceFile, destinationFile):
    return shutil.copyfile(sourceFile, destinationFile)
    # shutil.copyfile(source+filename, destination+defaultAudioName)
    # newFile = fixNameConflicts(destination+defaultAudioName, '.'+filename.split('.')[-1])
    # # os.rename(destination+filename,destination+newFilename)
    # time.sleep(0.2)
    # print("recording copied", source)
    # # return destination+newFilename
    # return newFile

if __name__ == "__main__":
    '''
    ready to test if the recording loop can recording loop.
    currently it should:
    - make 5 second idle recordings and discard them if nothing
    - if speech detected, record until speech is over + padding seconds and put the filename into
    a queue for processing.
    '''
    queue_recordingsWithSpeech = Queue(maxsize=100)
    queue_recordingFilenameBuffer = Queue(maxsize=100)
    queue_transcriptions = Queue(maxsize=100)
    recordingState = RecordingState()
    robotState = RobotState()
    humanState = HumanState()

    # Server setup for local Whisper model ################################################################
    try:
        # logFileName = fixNameConflicts(DEFAULT_LOCAL_WHISPER_CONFIG.whisper_server_logs_path[:-4]+"_"+args.logID,".log")
        # whisper_server_logs = open(logFileName, "w")
        whisperProcess = subprocess.Popen(
            [whisperConfig.WHISPER_ENV,
            "../lib/whisperLocal.py",],
            # "../lib/"+whisperConfig.WHISPER_MODEL_FILE],
            # stdout=whisper_server_logs,       
            # stderr=whisper_server_logs   
            )
    except Exception as e:
        print("cannot start whisper sub process", e)
        sys.exit(1)
    whisperClient = Client(host="localhost", port=whisperConfig.TCP_PORT, size=whisperConfig.TCP_DATA_SIZE)
    #####################################################################################################

    # Server setup for local realtime model ################################################################
    try:
        # logFileName = fixNameConflicts(DEFAULT_LOCAL_WHISPER_CONFIG.whisper_server_logs_path[:-4]+"_"+args.logID,".log")
        # whisper_server_logs = open(logFileName, "w")
        realtimeProcess = subprocess.Popen(
            ["python", "../lib/realtimeWebsocket.py",],
            # "../lib/"+realtimeConfig.WHISPER_MODEL_FILE],
            # stdout=whisper_server_logs,       
            # stderr=whisper_server_logs   
            )
    except Exception as e:
        print("cannot start realtime sub process", e)
        sys.exit(1)
    realtimeClient = Client(host="localhost", port=realtimeConfig.TCP_PORT, size=realtimeConfig.TCP_DATA_SIZE)
    #####################################################################################################

    recordingManager = RecordingManager(
        method_startRecording=startRecording,
        method_stopRecording=stopRecording,
        config = recordingTestConfig,
        )
    recordingHandler = RecordingHandler(
        method_fetchRecording=fetchRecording,
        config=recordingTestConfig,
        noiseSuppressionHeader='./testAudio/hello-46355.mp3',
        transcriptionClient=whisperClient,
        )

    thread_recordingManager = Thread(
        target = recordingManager.start,
        args = (recordingState,
                robotState,
                humanState,
                queue_recordingsWithSpeech,
                queue_recordingFilenameBuffer,),)
    thread_recordingManager.start()

    thread_recordingHandler = Thread(
        target = recordingHandler.start,
        args = (recordingState,
                queue_recordingsWithSpeech,
                queue_recordingFilenameBuffer,
                queue_transcriptions,),)
    thread_recordingHandler.start()

    try:
        # TEST1: MULTIPLE SPEECH OVER ALL FILES TEST ##########################################
        # person speaks briefly for half a second, then stops briefly then speaks again for a second for 10 times.
        # the recording handler and managers should
        # - get the files as they appear in queue_recordingsWithSpeech
        # - release the recording filenames as they are copied and renamed
        # - denoise the recordings in the local directory, 
        # - transcribe them (transcription is just a placeholder for this test)
        # - and put the transcriptions in the queue_transcriptions
        print("MULTIPLE SPEECH OVER ALL FILES TEST STARTING")
        input("enter to continue")
        time.sleep(2.0)
        # speech detected
        for i in range(5):
            # print(recordingState.getAttribute("currentFile"))
            print("speaking")
            humanState.setAttributes({
                "speaking": True,
                "lastSpoke": time.time(),
            })
            recordingState.setAttributes({
                "containsSpeech": True,
                "pipelineClear": False,
            })
            time.sleep(0.5)
            print("pause")
            humanState.setAttributes({
                "speaking": False,
                "lastSpoke": time.time(),
            })
            time.sleep(1.5)
        # end of speech
        time.sleep(3.0)

        if queue_transcriptions.empty():
            print("queue_recordingsWithSpeech is empty")
        else:
            while not queue_transcriptions.empty():
                transcriptions = queue_transcriptions.get()
                print("new transcription: ", transcriptions)
                for key in transcriptions.keys():
                    transcription = transcriptions[key]
                    print(f"requesting response for transcription: {transcription}")
                    realtimeClient.send({"message":transcription})
                    response = realtimeClient.receive()
                    print("response received: ", response["message"])
                time.sleep(0.2)
        time.sleep(2)
        print("MULTIPLE SPEECH OVER ALL FILES TEST OVER\n\n")
        #######################################################################################

    except KeyboardInterrupt:
        recordingManager.stop = True
        recordingHandler.stop = True
        thread_recordingManager.join()
        thread_recordingHandler.join()
        print("Exiting main loop.")