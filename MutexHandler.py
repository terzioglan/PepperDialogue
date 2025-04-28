import time

# ###############################################################################################################
# For Python2. Lock in python2 does not support timeout as an argument for acquire. 
# getAttribute and setAttribute are modified to implement a timeout manually.
# this is intended to be inherited by a container class, which will be used to handle the robot and human state.
# ###############################################################################################################

class MutexHandler(object):
    def __init__(self):
        pass

    def getAttributes(self,
                     attrNames,
                     blocking=True,
                     timeout=None):
        print("Getting attributes for :", self.__class__.__name__)
        if blocking == False and timeout != None:
            raise ValueError("nonblocking and timeout cannot be used together")
        assert type(attrNames) == list, "attrNames must be a list"
        acquired = False
        if timeout == None:
            acquired = self.lock.acquire(blocking)
        else:
            onset = time.time()
            while time.time()-onset < timeout:
                acquired = self.lock.acquire(False)
                if acquired == True:
                    break
                pass
        values =  {}
        if acquired:
            for attrName in attrNames:
                if hasattr(self, attrName) == False:
                    print("Attribute ", attrName, " not found in ", self.__class__.__name__)
                else:
                    values[attrName] = getattr(self, attrName)
            self.lock.release()
        return values
    
    def setAttributes(self,
                     attrDict,
                     blocking=True,
                     timeout=None):
        print("Setting attributes for :", self.__class__.__name__)
        if blocking == False and timeout != None:
            raise ValueError("nonblocking and timeout cannot be used together")
        assert type(attrDict) == dict, "attrDict must be a dictionary"
        if timeout == None:
            acquired = self.lock.acquire(blocking)
        else:
            onset = time.time()
            while time.time()-onset < timeout:
                acquired = self.lock.acquire(False)
                if acquired == True:
                    break
                time.sleep(0.01)
        if not acquired:
            return False
        else:
            for attrName in attrDict.keys():
                if hasattr(self, attrName) == False:
                    print("Attribute ", attrName, " not found in ", self.__class__.__name__)
                else:
                    setattr(self, attrName, attrDict[attrName])
            self.lock.release()
            return True
    
    def getSetAttributes(self,
                     attrDict,
                     blocking=True,
                     timeout=None):
        print("Setting attributes for :", self.__class__.__name__)
        if blocking == False and timeout != None:
            raise ValueError("nonblocking and timeout cannot be used together")
        assert type(attrDict) == dict, "attrDict must be a dictionary"
        if timeout == None:
            acquired = self.lock.acquire(blocking)
        else:
            onset = time.time()
            while time.time()-onset < timeout:
                acquired = self.lock.acquire(False)
                if acquired == True:
                    break
                time.sleep(0.01)
        if not acquired:
            return False
        else:
            attrValueCheck = True
            for attrName in attrDict.keys():
                if hasattr(self, attrName) == False:
                    attrValueCheck = False
                    print("Attribute ", attrName, " not found in ", self.__class__.__name__)
                    break
                else:
                    attrValueCheck = attrValueCheck and (attrDict[attrName] == getattr(self, attrName))
            if attrValueCheck:
                for attrName in attrDict.keys():
                    setattr(self, attrName, attrDict[attrName])
            self.lock.release()
            return True