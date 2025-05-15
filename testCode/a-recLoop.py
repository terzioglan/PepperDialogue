# python 2 or 3
import time, sys
sys.path.append("../")
from multiprocessing import Queue
from threading import Thread

from lib.recordingManagers import RecordingManager
from lib.states import RobotState, RecordingState, HumanState
from testConfig import recordingTestConfig

def startRecording(filename, extension, bitrate, microphoneArray):
    time.sleep(0.2)
    print("recording started")

def stopRecording():
    time.sleep(0.1)
    print("recording stopped")

if __name__ == "__main__":
    '''
    ready to test if the recording loop can recording loop.
    currently it should:
    - make 5-second idle recordings and discard them if there is no speech in it.
    - if speech detected, record until speech is over + padding seconds and put the filename into
    a queue for processing.
    '''
    queue_recordingsWithSpeech = Queue(maxsize=100)
    queue_recordingFilenameBuffer = Queue(maxsize=100)
    recordingState = RecordingState()
    robotState = RobotState()
    humanState = HumanState()

    recordingManager = RecordingManager(
        method_startRecording=startRecording,
        method_stopRecording=stopRecording,
        config=recordingTestConfig)
    

    thread_recordingManager = Thread(
        target = recordingManager.start,
        args = (recordingState,
                robotState,
                humanState,
                queue_recordingsWithSpeech,
                queue_recordingFilenameBuffer,),)
    thread_recordingManager.start()

    try:
        audioFileList = []
        # TEST1: NO SPEECH TEXT ###############################################################
        # recording buffer file names should be infinitely recycled without any of them being
        # put into the queue_recordingsWithSpeech
        print("NO SPEECH TEST STARTING")
        # input("enter to continue")
        time.sleep(4.0)
        start = time.time()
        while time.time() - start < 30:
            if queue_recordingsWithSpeech.empty():
                print("queue_recordingsWithSpeech is empty")
            print("current file: ", recordingState.getAttribute("currentFile"))
            time.sleep(2)
        print("NO SPEECH TEST OVER\\n\n")
        #######################################################################################

        # TEST2: ONCE SPEECH TEST #############################################################
        # person speaks briefly for a second, then stops.
        # 1 recording file should be added to queue_recordingsWithSpeech,
        # rest of the recording files should be indefinitely recycled.
        print("ONCE SPEECH TEST STARTING")
        # input("enter to continue")
        time.sleep(4.0)
        print("speaking")
        humanState.setAttributes({
            "speaking": True,
            "lastSpoke": time.time(),
        })
        recordingState.setAttributes({
            "containsSpeech": True,
            "pipelineClear": False,
        })
        time.sleep(2.0)
        print("pause")
        humanState.setAttributes({
            "speaking": False,
            "lastSpoke": time.time(),
        })

        start = time.time()
        while time.time() - start < 30:
            if queue_recordingsWithSpeech.empty():
                print("queue_recordingsWithSpeech is empty")
            else:
                audioFilename = queue_recordingsWithSpeech.get()
                audioFileList.append(audioFilename)
                print("recordingWithSpeehQueue has item!: ", audioFilename)
            print("current file: ", recordingState.getAttribute("currentFile"))
            time.sleep(2)
        for item in audioFileList:
            queue_recordingFilenameBuffer.put(item)
        print("ONCE SPEECH TEST OVER\n\n")
        #######################################################################################

    
        # TEST 3: MULTIPLE SPEECH TEST ########################################################
        # person speaks briefly for a second, then stops briefly then speaks again for a second for 10 times.
        # 1 recording file should be added to queue_recordingsWithSpeech,
        # rest recording files should be indefinitely recycled.
        print("MULTIPLE SPEECH TEST OVER ONE FILE TEST STARTING")
        # input("enter to continue")
        time.sleep(4.0)
        # speech detected
        for i in range(10):
            print("speaking")
            humanState.setAttributes({
                "speaking": True,
                "lastSpoke": time.time(),
            })
            recordingState.setAttributes({
                "containsSpeech": True,
                "pipelineClear": False,
            })
            time.sleep(1.0)
            print("pause")
            humanState.setAttributes({
                "speaking": False,
                "lastSpoke": time.time(),
            })
            time.sleep(0.2)
        # end of speech

        start = time.time()
        while time.time() - start < 30:
            if queue_recordingsWithSpeech.empty():
                print("queue_recordingsWithSpeech is empty")
            else:
                audioFilename = queue_recordingsWithSpeech.get()
                audioFileList.append(audioFilename)
                print("recordingWithSpeehQueue has item!: ", audioFilename)
                start = time.time()
            print("current file: ", recordingState.getAttribute("currentFile"))
            time.sleep(2)
        for item in audioFileList:
            queue_recordingFilenameBuffer.put(item)
        print("MULTIPLE SPEECH TEST OVER ONE FILE TEST OVER\n\n")
        #######################################################################################

        # TEST4: MULTIPLE SPEECH OVER ALL FILES TEST ##########################################
        # person speaks briefly for a second, then stops briefly then speaks again for a second for 10 times.
        # all recording files should be added to queue_recordingsWithSpeech,
        # and the recording manager should complain there are no available filenames.
        print("MULTIPLE SPEECH OVER ALL FILES TEST STARTING")
        # input("enter to continue")
        time.sleep(4.0)
        # speech detected
        while not queue_recordingFilenameBuffer.empty():
            print(recordingState.getAttribute("currentFile"))
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
            time.sleep(3.0)
        print(recordingState.getAttribute("currentFile"))
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
        time.sleep(3.0)
        # end of speech
        start = time.time()
        while time.time() - start < 10:
            if queue_recordingsWithSpeech.empty():
                print("queue_recordingsWithSpeech is empty")
            else:
                audioFilename = queue_recordingsWithSpeech.get()
                audioFileList.append(audioFilename)
                print("recordingWithSpeehQueue has item!: ", audioFilename)
                start = time.time()
            print("current file: ", recordingState.getAttribute("currentFile"))
            time.sleep(2)
        for item in audioFileList:
            queue_recordingFilenameBuffer.put(item)
        print("MULTIPLE SPEECH OVER ALL FILES TEST OVER\n\n")
        #######################################################################################
        
        # # TEST5: SHORT SPEECH OVER ONE FILE TEST ##############################################
        # person speaks briefly for a second, then stops. recording should take less than the full idle duration
        print("SHORT SPEECH OVER ONE FILE TEST STARTING")
        # input("enter to continue")
        time.sleep(4.0)
        # speech detected
        print(recordingState.getAttribute("currentFile"))
        print("speaking")
        humanState.setAttributes({
            "speaking": True,
            "lastSpoke": time.time(),
        })
        recordingState.setAttributes({
            "containsSpeech": True,
            "pipelineClear": False,
        })
        time.sleep(0.2)
        print("pause")
        humanState.setAttributes({
            "speaking": False,
            "lastSpoke": time.time(),
        })
        time.sleep(3.0)
        # end of speech

        start = time.time()
        while time.time() - start < 30:
            if queue_recordingsWithSpeech.empty():
                print("queue_recordingsWithSpeech is empty")
            else:
                audioFilename = queue_recordingsWithSpeech.get()
                audioFileList.append(audioFilename)
                print("recordingWithSpeehQueue has item!: ", audioFilename)
                start = time.time()
            print("current file: ", recordingState.getAttribute("currentFile"))
            time.sleep(2)
        for item in audioFileList:
            queue_recordingFilenameBuffer.put(item)
        print("SHORT SPEECH OVER ONE FILE TEST OVER\n\n")
        # #######################################################################################

    except KeyboardInterrupt:
        pass
    finally:
        print("Exiting main loop.")
        recordingManager.stop = True
        thread_recordingManager.join()
        sys.exit(0)