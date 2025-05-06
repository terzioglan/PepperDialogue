import time

# ###############################################################################################################
# For Python2. Lock in python2 does not support timeout as an argument for acquire. 
# getAttribute and setAttribute are modified to implement a timeout manually.
# this is intended to be inherited by a container class, which will be used to handle the robot and human state.
# ###############################################################################################################

class MutexHandler(object):
    def __init__(self):
        pass

    def acquireLock(self,
                    blocking,
                    timeout,):
        if blocking == False and timeout != None:
            raise ValueError("nonblocking and timeout cannot be used together")
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
        return acquired
    
    def releaseLock(self):
        self.lock.release()

    def getAttribute(self,
                     attrName,
                     blocking=True,
                     timeout=None):
        # print("Getting attributes for :", self.__class__.__name__)
        assert type(attrName) == str, "attrName must be a string"
        if hasattr(self, attrName) == False:
            print("Attribute ", attrName, " not found in ", self.__class__.__name__)
            return None
        acquired = self.acquireLock(blocking=blocking, timeout=timeout)
        if acquired:
            value = getattr(self, attrName)
            self.releaseLock()
            return value
        return None
    
    def getAttributes(self,
                     attrNames,
                     blocking=True,
                     timeout=None):
        # print("Getting attributes for :", self.__class__.__name__)
        assert type(attrNames) == list, "attrNames must be a list"
        acquired = self.acquireLock(blocking=blocking, timeout=timeout)
        values =  {}
        if acquired:
            for attrName in attrNames:
                if hasattr(self, attrName) == False:
                    print("Attribute ", attrName, " not found in ", self.__class__.__name__)
                else:
                    values[attrName] = getattr(self, attrName)
            self.releaseLock()
        return values
        
    def setAttributes(self,
                     attrDict,
                     blocking=True,
                     timeout=None):
        # print("Setting attributes for :", self.__class__.__name__)
        assert type(attrDict) == dict, "attrDict must be a dictionary"
        acquired = self.acquireLock(blocking=blocking, timeout=timeout)
        if not acquired:
            return False
        else:
            for attrName in attrDict.keys():
                if hasattr(self, attrName) == False:
                    print("Attribute ", attrName, " not found in ", self.__class__.__name__)
                else:
                    setattr(self, attrName, attrDict[attrName])
            self.releaseLock()
            return True
    
    def getSetAttributes(self,
                     conditions,
                     setAttrDict,
                     blocking=True,
                     timeout=None):
        '''
        sets the attributes to specified in setAttrDict only if
        current attribute values match with the ones in conditions.
        '''
        # print("Setting attributes for :", self.__class__.__name__)
        assert type(conditions) == dict and type(setAttrDict) == dict, "attrDicts must be dictionaries"

        for attrName in conditions.keys():
            if hasattr(self, attrName) == False:
                print("Attribute ", attrName, " not found in ", self.__class__.__name__)
                return False
        acquired = self.acquireLock(blocking=blocking, timeout=timeout)
        if not acquired:
            return False
        else:
            attrValueCheck = True
            for attrName in conditions.keys():
                attrValueCheck = attrValueCheck and (conditions[attrName] == getattr(self, attrName))
            if attrValueCheck:
                for attrName in setAttrDict.keys():
                    if hasattr(self, attrName) == False:
                        print("Attribute ", attrName, " not found in ", self.__class__.__name__)
                    else:
                        setattr(self, attrName, setAttrDict[attrName])
            else:
                print("attribute value check failed. Not setting new attributes.")
            self.releaseLock()
            return attrValueCheck