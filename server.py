import socket
from threading import Thread, current_thread
from Memory import *
import shutil

"""
A basic socket server with a threaded client handler.
Accepts four commands (casse sensitive):

STORE <filename> <bytes>\n<file-contents>
-- add file <filename> to the storage server
-- if the file already exists, return an "ERROR: FILE EXISTS\n" error
-- return "ACK\n" if successful

READ <filename> <byte-offset> <length>\n
-- server returns <length> bytes of the contents of file <filename>, starting at <byte-offset>
-- note that this does NOT remove the file on the server
-- if the file does not exist, return an "ERROR: NO SUCH FILE\n" error
-- if the file byte range is invalid, return an "ERROR: INVALID BYTE RANGE\n" error
-- return "ACK" if successful, following it with the length and data, as follows: ACK <bytes>\n<file-excerpt>

DELETE <filename>\n
-- delete file <filename> from the storage server
-- if the file does not exist, return an "ERROR: NO SUCH FILE\n" error
-- return "ACK\n" if successful

DIR\n
-- server returns the list of files currently stored on the server in alphabetical order
---- in the format: <number-of-files>\n<filename1>\n<filename2>\n...\n
-- if no files are stored, "0\n" is returned
"""

def clientHandler(conn, addr):
    while True:

        pid = current_thread().ident

        try:
            data = conn.recv(4096)
        except socket.error:
            print "[thread %d] Client {} closed its socket...terminating".format(addr) % pid
            break

        splitData = data.split()

        command = splitData[0]
        if len(splitData) > 1:
            filename = splitData[1]

        print "[thread %d] Rcvd: %s" % (pid , data),

        if command == "STORE":
            if len(splitData) < 3:
                conn.send("ERROR: Invalid number of arguments\n")
            elif os.path.exists(storageDirectory + "\%s" % splitData[1]):
                conn.send("ERROR: File '%s' already exists\n" % filename)
            else:
                memory.addFile(splitData, conn, pid)

        elif splitData[0] == "READ":
            if len(splitData) < 4:
                conn.send("ERROR: Invalid number of arguments\n")
            elif not os.path.isfile(storageDirectory + "\%s" % filename):
                conn.send("ERROR: File '%s' does not exist\n" % filename)
            else:
                mutex.acquire()
                f = open(storageDirectory + "\%s" % filename)
                readData = f.read()
                byteOffset =int(splitData[2])
                length = int(splitData[3])

                if 0 > byteOffset or byteOffset > len(readData):
                    conn.send("ERROR: Invalid byte offset '%d'\n" % byteOffset)
                elif (byteOffset + length) > len(readData):
                    conn.send("ERROR: Read past EOF (byteOffset + length is too large)\n")
                else:
                    conn.send("ACK %d\n" % length)
                    conn.send( readData[byteOffset:byteOffset + length] + '\n\n' )
                print "[thread %d] Sent %d bytes (from %d '%s' blocks) from offset %d" % (pid, length, memory.getReadInfo(filename)[0],  memory.getReadInfo(filename)[1], byteOffset)
                print "[thread %d] Sent: ACK" % pid
                f.close()
                mutex.release()

        elif command == "DELETE":
            if len(splitData) < 2:
                conn.send("ERROR: Invalid number of arguments\n")
            elif not os.path.isfile(storageDirectory + "\%s" % filename):
                conn.send("ERROR: File '%s' does not exist\n" % filename)
            else:
                os.remove(storageDirectory + "\%s" % filename)
                memory.deleteFile(splitData, conn, pid)

        elif command == "DIR":
            files = os.listdir(storageDirectory)
            if not files:
                conn.send("0\n\n")
            else:
                files.sort()
                conn.send( "%d\n" % len(files) )
                for f in files:
                    conn.send("%s\n" % f)
                print "\n"
        else:
            conn.send("ERROR: Invalid command '%s'\n" % command)

    conn.close()

if __name__ == "__main__":

    mutex = Lock()

    memory = Memory(128, 4096)

    HOST = '127.0.0.1'
    PORT = 8765
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(10)

    storageDirectory = os.getcwd() + "\.storage"
    if os.path.exists(storageDirectory):
        shutil.rmtree(storageDirectory)
    os.makedirs(storageDirectory)

    while True:
        print("Waiting for a connection...")
        conn, addr = sock.accept()
        print("...Connected from {}".format(addr))
        newClient = Thread( target = clientHandler, args = (conn, addr) )
        newClient.start()

    sock.close()