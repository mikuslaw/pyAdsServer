
import socketserver,struct,array,time, socket
import collections

class AdsSocketTest:
    def run(self):
        # Define host to be any interface, and port to be beckhoff 48898
        hostAddressToListenOn = ""
        portNumberToListenOn = 48898
        
        self.processImage = {}
        self.buildProcessImage()
        

        #print(self.processImage)
        
        # Open a socket
        socketListen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow reuse
        socketListen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to the host address and port
        socketListen.bind((hostAddressToListenOn, portNumberToListenOn))
        # Start listening on incomming connections
        socketListen.listen(1)
        
        while(1):
            # Let's wait for the first incomming connection
            socketRequest, socketPeerAddress = socketListen.accept()

            print("Received a connection from: ", socketPeerAddress)

            while(1):
                # Receive a packet
                self.data = socketRequest.recv(2048)
                if not self.data: 
                    self.printAds("No data was received")
                    socketRequest.close()
                    break
                    
                # Process header
                self.parsedRequest = self.parseRequest(self.data)
                self.connectionInfo = self.getConnectionInfo(self.parsedRequest)
                
                ##self.printAds("Decoding of header failed")
                  
                if self.parsedRequest['ams_commandId'] == 9:
                    responseData = self.processAdsWriteRead(self.parsedRequest['ams_data'])
                    #self.printAds("Response data: ", responseData)
                    
                    responseData = self.addAdsWriteReadResponseHeader(responseData, 0x0) # Error code 0
                    #self.printAds("Response data with command header: ", responseData)
                    
                    responseData = self.addAmsResponseHeader(responseData, 0x0) # Error ok
                    #self.printAds("Response data with ams header: ", responseData)
                    
                    responseData = self.addAmsTcpResponseHeader(responseData, 0x0) # Error ok
                    #self.printAds("Response data with ams/tcp header: ", responseData)
                    
                    socketRequest.sendall(responseData)
                elif self.parsedRequest['ams_commandId'] == 2:
                    responseData = self.processAdsRead(self.parsedRequest['ams_data'])
                    #self.printAds("Response data: ", responseData)
                    
                    responseData = self.addAdsWriteReadResponseHeader(responseData, 0x0) # Error code 0
                    #self.printAds("Response data with command header: ", responseData)
                    
                    responseData = self.addAmsResponseHeader(responseData, 0x0) # Error ok
                    #self.printAds("Response data with ams header: ", responseData)
                    
                    responseData = self.addAmsTcpResponseHeader(responseData, 0x0) # Error ok
                    #self.printAds("Response data with ams/tcp header: ", responseData)
                    
                    socketRequest.sendall(responseData)
                else:
                    pass
                    print("Unsupported command", self.parsedRequest['ams_commandId'])
                
            
        socketListen.close()
            
    def parseRequest(self, requestBytes):
        requestData = bytes(requestBytes)
        #self.printAds("Request data", requestData)
                
        ams_tcp_reserved = struct.unpack('<H', requestData[0:2])
        ams_tcp_length = struct.unpack('<L', requestData[2:6])[0]
        
        ams_targetId = struct.unpack('<6B', requestData[6:12])
        ams_targetIdStr = '%d.%d.%d.%d.%d.%d' %(ams_targetId[0], ams_targetId[1], ams_targetId[2], ams_targetId[3], ams_targetId[4], ams_targetId[5])
        ams_targetPort = struct.unpack('<H', requestData[12:14])[0]
        
        ams_sourceId = struct.unpack('<6B', requestData[14:20])
        ams_sourceIdStr = '%d.%d.%d.%d.%d.%d' %(ams_sourceId[0], ams_sourceId[1], ams_sourceId[2], ams_sourceId[3], ams_sourceId[4], ams_sourceId[5])
        ams_sourcePort = struct.unpack('<H', requestData[20:22])[0]
        
        ams_commandId = struct.unpack('<H', requestData[22:24])[0]
        ams_stateFlags = struct.unpack('<H', requestData[24:26])[0]
        ams_length = struct.unpack('<L', requestData[26:30])[0]
        ams_errorCode = struct.unpack('<L', requestData[30:34])[0]
        ams_invokeId = struct.unpack('<L', requestData[34:38])[0]
        
        
        ams_data = requestData [38:38+ams_length]

        ams_result = collections.OrderedDict()
        ams_result['ams_tcp_reserved']  = ams_tcp_reserved
        ams_result['ams_tcp_length']    = ams_tcp_length
        ams_result['ams_targetId']      = ams_targetId
        ams_result['ams_targetPort']    = ams_targetPort
        ams_result['ams_sourceId']      = ams_sourceId
        ams_result['ams_sourcePort']    = ams_sourcePort
        ams_result['ams_commandId']     = ams_commandId
        ams_result['ams_stateFlags']    = ams_stateFlags
        ams_result['ams_length']        = ams_length
        ams_result['ams_errorCode']     = ams_errorCode
        ams_result['ams_invokeId']      = ams_invokeId
        ams_result['ams_data']          = ams_data

        #self.printAds(ams_result)
        
        return ams_result
        
    def getConnectionInfo(self, parsedRequest):
        connectionInfo = {}
        connectionInfo['targetId'] = parsedRequest['ams_targetId']
        connectionInfo['targetPort'] = parsedRequest['ams_targetPort']
        connectionInfo['sourceId'] = parsedRequest['ams_sourceId']
        connectionInfo['sourcePort'] = parsedRequest['ams_sourcePort']
        
        connectionInfo['commandId'] = parsedRequest['ams_commandId']
        connectionInfo['stateFlags'] = parsedRequest['ams_stateFlags']
        connectionInfo['invokeId'] = parsedRequest['ams_invokeId']
        return connectionInfo
        
    def processAdsWriteRead(self, amsData):
        #self.printAds("Processing command Ads Write Read")
        indexGroup  = struct.unpack('<L', amsData[0:4])[0]
        indexOffset = struct.unpack('<L', amsData[4:8])[0]
        readLength  = struct.unpack('<L', amsData[8:12])[0]
        writeLength = struct.unpack('<L', amsData[12:16])[0]
        
        self.printAds("IndexGroup: %x, IndexOffset: %x" % (indexGroup, indexOffset))
        self.printAds("Write: %d, Read: %d" % (writeLength, readLength))
        self.writeData(indexGroup, indexOffset, writeLength, amsData[16:16+writeLength])
        readData = self.readData(indexGroup,indexOffset,readLength)
        
        return readData
        
    def processAdsRead(self, amsData):
        #self.printAds("Processing command Ads Write Read")
        indexGroup  = struct.unpack('<L', amsData[0:4])[0]
        indexOffset = struct.unpack('<L', amsData[4:8])[0]
        readLength  = struct.unpack('<L', amsData[8:12])[0]
                
        self.printAds("IndexGroup: %x, IndexOffset: %x" % (indexGroup, indexOffset))
        self.printAds("Read: %d" % (readLength))
        readData = self.readData(indexGroup,indexOffset,readLength)
        
        return readData
    
    def addAdsWriteReadResponseHeader(self, responseData, result):
        dataWithHeader = []
        
        if result != 0x0:
            pass
        else:
            dataWithHeader = struct.pack('<L', 0x0) # error code ok
            dataWithHeader += struct.pack('<L', len(responseData))
            dataWithHeader += responseData
        
        return dataWithHeader
        
    def addAmsResponseHeader(self, responseData, result):
        dataWithHeader = []
        
        if result != 0x0:
            pass
        else:          
            #self.printAds("Self connection info: ", list(self.connectionInfo['sourceId']))

            dataWithHeader =  struct.pack('<6B', self.connectionInfo['sourceId'][0], self.connectionInfo['sourceId'][1], self.connectionInfo['sourceId'][2], self.connectionInfo['sourceId'][3], self.connectionInfo['sourceId'][4], self.connectionInfo['sourceId'][5])
            dataWithHeader += struct.pack('<H' , self.connectionInfo['sourcePort'])
            dataWithHeader += struct.pack('<6B', self.connectionInfo['targetId'][0], self.connectionInfo['targetId'][1], self.connectionInfo['targetId'][2], self.connectionInfo['targetId'][3], self.connectionInfo['targetId'][4], self.connectionInfo['targetId'][5])
            dataWithHeader += struct.pack('<H' , self.connectionInfo['targetPort'])
            dataWithHeader += struct.pack('<H' , self.connectionInfo['commandId'])
            dataWithHeader += struct.pack('<H' , self.connectionInfo['stateFlags'] | 0x1)
            dataWithHeader += struct.pack('<L' , len(responseData))
            dataWithHeader += struct.pack('<L' , result)
            dataWithHeader += struct.pack('<L' , self.connectionInfo['invokeId'])
            dataWithHeader += responseData
        
        return dataWithHeader
      
    def addAmsTcpResponseHeader(self, responseData, result):
        dataWithHeader = []
        
        if result != 0x0:
            pass
        else:
            dataWithHeader = struct.pack('<H', 0x0) 
            dataWithHeader += struct.pack('<L', len(responseData))
            dataWithHeader += responseData 
        return dataWithHeader

    def writeData(self, indexGroup, indexOffset, length, data):
        for i in range(length):
            self.processImage[indexGroup][indexOffset+i] = data[i] 
            print("Wrote %x at %x:%x" %(data[i], indexGroup, indexOffset+i))
            
    def readData(self, indexGroup, indexOffset, length):
        dataList = []
        
        for i in range(length):
            print("Trying to read from %x:%x: " % (indexGroup, indexOffset+i))
            dataList.append(self.processImage[indexGroup][indexOffset+i])
            print("Read %x at %x:%x" %(self.processImage[indexGroup][indexOffset+i], indexGroup, indexOffset+i))
        return bytearray(dataList)
        
    def buildProcessImage(self):
        processGroups = { 0xF060, 0x0, 0x1, 124 }
        for group in processGroups:
            self.processImage[group] = bytearray(10240000)
        
        #self.processImage[0xF060][0] = 0x1
        #self.processImage[0xF060][1] = 0x2
        #self.processImage[0xF060][2] = 0x3 # Coupler state low
        #self.processImage[0xF060][3] = 0x4 # Coupler state high

    def printAds(self, data):
        print(data)
        
if __name__ == "__main__":
    test = AdsSocketTest()
    test.run()

