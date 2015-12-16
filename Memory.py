import math
import os
from threading import Lock

class Memory(object):
    def __init__(self, iBlocks, iBlocksize):
        self.blocks = iBlocks
        self.blockSize = iBlocksize
        self.memory = ['.'] * iBlocks
        self.fids = ['A','B','C','D','E','F','G','H','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
        self.fileDirectory = {}
        self.mutex = Lock()

    def printMemory(self, pid, conn):
        print "[thread %d] Simulated Clustered Disk Allocation:" % pid
        print ('=' * 32)
        for i in range(len(self.memory)/32+1):
            if i == len(self.memory) / 32:
                print "".join(self.memory[i*32:(i+1)*32]) + '=' * 32
            else:
                print "".join(self.memory[i*32:(i+1)*32])

    def setClusters(self, numBlocks, fid):
        itr, clusterCount = 0, 0
        trigger = False
        while numBlocks > 0:
            if itr == self.blocks:
                return -1
            if self.memory[itr] == '.':
                if not trigger:
                    trigger = True
                    clusterCount += 1
                self.memory[itr] = "swap"
                numBlocks -= 1
            elif trigger:
                trigger = False
            itr += 1

        self.memory = [fid if byte == 'swap' else byte for byte in self.memory]
        return clusterCount


    def addFile(self, data, conn, pid):
        self.mutex.acquire()

        filename = data[1]
        filesize = data[2]

        fid = self.fids.pop(0)
        self.fileDirectory[filename] = fid

        numBlocks = math.ceil( float(filesize) / self.blockSize )
        numClusters = self.setClusters(numBlocks, fid)

        if numClusters == -1:
             print "ERROR: Insufficient disk space"
             conn.send("ERROR: Insufficient disk space\n")
        else:
            bytesLeft = int(filesize)
            path =  os.getcwd() + "\.storage\%s" % filename
            f = open(path, 'w+')
            while bytesLeft > 0:
                data = conn.recv(4096)
                bytesLeft -= len( data.strip() )
                f.write(data)
            print "[thread %d] Stored file %s (%d bytes; %d blocks; %d cluster)" % (pid, filename, int(filesize), numBlocks, numClusters)
            self.printMemory(pid, conn)
            conn.send("[thread %d] ACK\n\n" % pid)
            print "[thread %d] Sent: ACK" % pid
            f.close()

        self.mutex.release()

    def deleteFile(self, data, conn, pid):
        self.mutex.acquire()
        fid = self.fileDirectory[ data[1] ]
        numBlocks = self.memory.count(fid)
        self.fids.append(fid)
        self.fids.sort()
        self.memory = ['.' if byte == fid else byte for byte in self.memory]
        print "[thread %d] Deleted %s file '%s' (deallocated %d blocks)" % (pid, data[1], fid, numBlocks)
        conn.send("ACK\n\n")
        print "[thread %d] Sent: ACK" % pid
        self.mutex.release()

    def getReadInfo(self, filename):
        return self.memory.count( self.fileDirectory[filename] ), self.fileDirectory[filename]