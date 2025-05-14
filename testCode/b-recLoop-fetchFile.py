# python2

import time, sys, shutil, os
sys.path.append("../")
from multiprocessing import Process, Queue
from functools import partial
from threading import Thread

from lib.recordingManagers import RecordingHandler, RecordingManager
from lib.states import RobotState, RecordingState, HumanState
from testConfig import recordingTestConfig

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

def requestTranscription(filename):
    filename += '_transcribed'
    time.sleep(2.0)
    return filename

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

    recordingManager = RecordingManager(
        method_startRecording=startRecording,
        method_stopRecording=stopRecording,
        config = recordingTestConfig,
        )
    recordingHandler = RecordingHandler(
        method_fetchRecording=fetchRecording,
        config=recordingTestConfig,
        noiseSuppressionHeader='./testAudio/hello-46355.mp3',
        )
    recordingHandler.requestTranscription = requestTranscription

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
        # input("enter to continue")
        time.sleep(4.0)
        # speech detected
        for i in range(10):
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
                transcription = queue_transcriptions.get()
                print("new transcription: ", transcription)
        time.sleep(2)
        print("MULTIPLE SPEECH OVER ALL FILES TEST OVER\n\n")
        #######################################################################################

    except KeyboardInterrupt:
        pass
    finally:
        print("Exiting main loop.")
        recordingManager.stop = True
        recordingHandler.stop = True
        thread_recordingManager.join()
        thread_recordingHandler.join()
        sys.exit(0)