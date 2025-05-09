import almath
import numpy as np

class PepperProxy(object):
    '''
    This will be the main handler for the engagement state.
    It will be called periodically and take action if there is no active dialog or human is disengaging by any means.
    '''
    def __init__(
            self,
            # qiSession,
            animatedSpeechService,
            ledControllerService,
            postureService,
            motionService,
            ):
        self.animatedSpeechService = animatedSpeechService
        self.ledControllerService = ledControllerService
        self.postureService = postureService
        self.motionService = motionService

    def cueSpeechDetected(self,):
        self.ledControllerService.fadeRGB("FaceLeds", 0, 1, 0, 0) # R G B
    
    def cueIdle(self,):
        self.ledControllerService.reset("FaceLeds")

    def cueBusy(self,):
        self.ledControllerService.fadeRGB("FaceLeds", 0, 0, 0, 0) # Dark
    
    def speak(self, sentence,):
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