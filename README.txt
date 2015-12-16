TO USE:
run server.py
use 'netcat localhost 8765' to connect

MAKE SURE YOU ARE NOT VIEWING THE STORAGE DIRECTORY WEHN STARTING THE PROGRAM;
   IT WILL GIVE YOU AN ACCESS DENIED / SOME OTHER ERROR.

The mutex locks WORK ON MY MACHINE, however, sometimes when dealing with Python's 
multiprocessing nonsense, they suddenly decide to not work and instead let the
clients work in arbitrary order. I have no idea why.

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
