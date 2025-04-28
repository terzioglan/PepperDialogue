import time
from threading import Thread, Lock, Queue
# TTS.say() is handled by a thread running in parallel looking for a shared queue to populate
# makes asynchronous animated speech calls. cancels the call if a higher priority call is received
# before the current call is finished
# --
# Recordings are started/stopped and copied by the recording handler.
# recordings are only copied if they contain speech.
# each time a recording is copied, a request is sent to the transcription server.
# --
# The transcription server is a separate process that listens for requests and returns transcriptions.
# This process is connected to the main process via a tcp socket.
# undecided yet: either this process directly populates the transcription field of the humanState, or
# the main process handles this somehow.
# need to check if it is possible to set an interrupt once there is something waiting in a certain TCP socket.
# --
# The OpenAI response is handled by a separate process that listens for requests and returns responses through another
# tcp socket.
# This process is connected to the server through WebSocket.
# -- 
# a refresh function is called every n seconds.
# this function sets the engagement states, and calls the responses to engagementState if necessary.
# note that this function does not manipulate humanState directly.
# --
# the main loop basically starts/stops recordings based on humanState and robotState,
# checks tcp ports for waiting responses
# ideally there are no blocking calls in the main loop or the main process. it just keeps running and running recordings
# updating human states, and occasionally sending requests to transcription server, speech server, and OpenAI server.
# --
# the whole benefit of this refactorization is:
# 1. do not spend excessive amounts of time inside the speechDetected callback
# 2. uses mutex locks to not risk reading invalid states from the variables
# 3. uses a queue to handle the speech requests and responses which should make it possible to extend to handle
# interruptions or higher/lower priority requests.





class RecordingHandler(object):
    def __init__(self, config):
        self.recordingFileBuffer = config.get('recordingFileBuffer')
        self.recording = False
        self.recording_start_time = None
        self.recording_end_time = None
        self.state = RecordingState()

    def start_recording(self):
        self.state.getSetAttributes(
            gets = {'recording': False},
            sets = {'recording': True, 
             'currentFile': filename,
             'startTime': time.time(),
             'containsSpeech': False},
             blocking = True,
             timeout = 2.0)
        print("Recording started.")

    def stop_recording(self):
        if self.recording:
            self.recording = False
            self.recording_end_time = time.time()
            print("Recording stopped.")
            print(f"Recording duration: {self.recording_end_time - self.recording_start_time} seconds")

class PepperSpeechCommander(object):
    def __init__(self):
        self.speechController = None

    def start(self, speechActionQueue):
        while True:
            try:
                action = speechActionQueue.get()
                if action == 'start_recording':
                    self.recordingHandler.start_recording()
                elif action == 'stop_recording':
                    self.recordingHandler.stop_recording()
                else:
                    print("Unknown action")
            except Exception as e:
                print(f"Error: {e}")

def main():
    pepperSpeechCommander = PepperSpeechCommander()
    speechActionQueue = Queue()
    speechCommanderThread = Thread(target=pepperSpeechCommander.start, args=(speechActionQueue,))
    speechCommanderThread.start()

    while True:
        try:
            # Simulate some processing
            time.sleep(1)
            print("Processing...")
        except KeyboardInterrupt:
            print("Exiting...")
            break