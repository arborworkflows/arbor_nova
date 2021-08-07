import pymongo
import pycuda.autoinit
import pycuda.driver as cuda
from pymongo import MongoClient




class GPUManager():
    
    # called once when the system is started up to discover computational devices and
    # setup the management datastructures.  If this class is initialized without arguments,
    # it defaults to using 1/2 of the available devices. This is a heuristic to try to avoid 
    # over subscribing system RAM.
    
     
    def  __init__(self,devices=None, maxDevices=None, initialize=True):
        client = MongoClient()
        self.db = client['device_allocation']
        self.avail = self.db['available']
        self.allocated = self.db['allocated']
        print('initializing devices')
        
        # for now, start with the system empty and all devices available. This will have to 
        # be removed before deployment, since we want the collections to spread across users.

        #self.allocated.drop()
        #self.avail.drop()
        
        # if a list of devices was provided by the user, insert these
        # devices into the available array.  Devices are expected to contain
        # at last a 'name' field.  (e.g. {'name':'cuda0'}).  If no explicit
        # device names were passed, then discover available devices automatically
        
        if (devices != None):
            # if user specified a devices list, use it. 
            for device in devices:
                self.avail.insert_one(device)
                print('inserting ',device)
        else:
            # if this is the first time this class has run, set up the mongo collections
            # to show available devices.  Devices that will reserve, can instantiate the 
            # class with initialize=False to leave the device allocation as is and continue
            # reservations/returns. 
            if initialize:
                # Otherwise discover devices automatically
                device_list = self.discoverDevices()
                for device in device_list:
                    self.avail.insert_one(device)
                    print('inserting ',device)

        
            
    # hueristic to only return True if enough devices are left.  this is True
    # for unallocated single GPU systems and lets 1/2 of the GPUs be used on a 
    # multi-gpu system.  If the allowAll flag is passed as True, then all GPUs can 
    # be reserved
    
    def usedMaxDevices(self, allowAll):
        avail_count = self.avail.count_documents({})
        allocated_count = self.allocated.count_documents({})
        sum = avail_count + allocated_count
        saveHalf= (((sum == 1) and (avail_count < 1)) or 
                    ((sum>1) and (avail_count <= (sum/2))))
        useAll= (((sum == 1) and (avail_count < 1)) or 
                    ((sum>1) and (avail_count ==0)))
        if allowAll:
            return useAll
        else:
            return saveHalf
                   
    # return list of available devices
    def availableDevices(self):
        dev_list = []
        for dev in self.avail.find({}):
            pprint.pprint(dev)
            dev_list.append(dev)
        return dev_list
 
    def returnNextDevice(self):
        newDevice = self.avail.find({})
        print('allocated device',newDevice[0])
        allocatedDevice = newDevice[0]
        # remove device from avail list
        self.allocated.insert_one(newDevice[0])
        self.avail.delete_one(newDevice[0])
        return allocatedDevice
        
    # allocate a device if it is available.  If we have used too many
    # devices, then an empty object is returned instead of allocating 
    # and returning a device
    
    def requestDevice(self, allowAll=False):
        if (self.usedMaxDevices(allowAll)):
            print('sorry, we are full right now')
            return ('Fail',None)
        else:
            print('we open for business')
            return ('Success',self.returnNextDevice())
        
    # Use pycuda to look for the number of devices and build a device list.
    # Return a list of device records, which have pytorch compatible names.
    # other attributes could be added to the returns if it is beneficial
    def discoverDevices(self):
        print('discovering devices')
        devicelist = []
        for devicenum in range(cuda.Device.count()):
            devicerecord = {'name':'cuda'+str(devicenum)}
            device=cuda.Device(devicenum)
            attrs=device.get_attributes()
            # these lines add many bits of info about the GPU capabilities, not currently needed
            #for key in attrs.keys():
                #devicerecord[key] = attrs[key]
            devicelist.append(devicerecord)
        print(devicelist)
        return devicelist
    
    # print out the contents of the available and allocated arrays
    # to show the status of the device lists for debugging or status inquiry
    
    def printStatus(self):
        print('available devices:')
        try:
            availDevs = self.avail.find({})
            for dev in availDevs:
                print(dev)
        except:
            print('no available devices')
        print('allocated devices:')
        try:
            allocDevs = self.allocated.find({})
            for dev in allocDevs:
                print(dev)
        except:
            print('no allocated devices')
    
    # if a user is finished with a device they have allocated, it can be
    # returned to the available queue if it matches the name of an allocated
    # device.  The record is moved from allocated back to available. 
    
    def returnDeviceByName(self,deviceName):
        try:
            searchedDevice = self.allocated.find({'name': deviceName})
            print('found matching device:',searchedDevice[0]['name'])
            localDeviceCopy = searchedDevice[0]
            self.allocated.delete_one(searchedDevice[0])
            self.avail.insert_one(localDeviceCopy)
            return 'Success'
        except:
            print('gpumanager: unable to return GPU')
            return 'Fail'
 
    def returnDevice(self,device):
        if 'name' in device:
            status = self.returnDeviceByName(device['name'])
            return status
        else:
            print('please pass a dictionary object containing a "name" field')
            return 'Fail'
         
    

