import almath 
import numpy as np

class PepperProxy(object):
    '''
    This class is a wrapper for the Pepper robot's services.
    It provides methods to control the robot's behavior, such as speaking.
    '''
    def __init__(
            self,
            qiSession,
            ):
        self.memoryService               = qiSession.service("ALMemory")
        self.basicAwarenessService       = qiSession.service("ALBasicAwareness")
        self.speechRecognitionService    = qiSession.service("ALSpeechRecognition")
        self.audioRecorderService        = qiSession.service("ALAudioRecorder")
        self.ledService                  = qiSession.service("ALLeds")
        self.animatedSpeechService       = qiSession.service("ALAnimatedSpeech")
        self.postureService              = qiSession.service("ALRobotPosture")
        self.motionService               = qiSession.service("ALMotion")

        self.speechRecognitionService.pause(True)                            # Stop the Speech Recognition system before setting the parameters.
        self.speechRecognitionService.removeAllContext()                     # Remove all context present if any.
        self.speechRecognitionService.setLanguage('English')                 # Set Language to English
        self.speechRecognitionService.setVocabulary(['Pepper'], False)       # Set vocab sets ALSpeechRecognition/ActiveListening to process speech.
        self.speechRecognitionService.setParameter('Sensitivity', 1.0)       # Sensitivity [0.0, 1.0].
        self.speechRecognitionService.pause(False)                           # Restart the Speech Recognition system for settings to take effect.

        self.basicAwarenessService.setEnabled(True)
        self.basicAwarenessService.setEngagementMode("FullyEngaged")

        self.audioRecorderService.stopMicrophonesRecording()                  # Stop all microphones if any.
   

    def cueSpeechDetected(self,):
        self.ledService.fadeRGB("FaceLeds", 0, 1, 0, 0) # R G B Duration
    
    def cueIdle(self,):
        self.ledService.reset("FaceLeds")

    def cueBusy(self,):
        self.ledService.fadeRGB("FaceLeds", 0, 0, 0, 0) # Dark
    
    def speak(self, sentence,):
        # self.speechStyle="\\style=didactic\\\\vct=75\\"
        self.animatedSpeechService.say(sentence)
    
    def headNod(self,n=2):
        self.postureService.goToPosture("StandInit", 0.5)
        names = ["HeadPitch"]
        angleHigh = -10.0
        angleLow = 0.0
        tToHigh = 0.2
        tToLow = 0.2
        decay = 0.8

        anglesList = [[(angleHigh + (np.random.random()-0.5)*2)*almath.TO_RAD, (angleLow + (np.random.random()-0.5)*2)*almath.TO_RAD]]
        timesList = [[tToHigh, tToHigh+tToLow]]

        for i in range(n):
            anglesList[0].append((((angleHigh-angleLow)*decay)+angleLow+2*(np.random.random()-0.5))*almath.TO_RAD)
            anglesList[0].append((((0.0-angleLow)*decay)+0.0+3*(np.random.random()-0.5))*almath.TO_RAD)
            timesList[0].append(timesList[0][-1]+tToHigh)
            timesList[0].append(timesList[0][-1]+tToLow)
            decay = decay*decay

        anglesList[0].append(((angleHigh-angleLow)/2)*almath.TO_RAD)
        timesList[0].append(timesList[0][-1]+tToHigh)

        self.motionService.angleInterpolationBezier(names, timesList, anglesList, _async=True)
    
    def exit(self,):
        self.audioRecorderService.stopMicrophonesRecording()
        self.eyesReset()