import threading
import os
import time


st_time = time.time()

def logger(logargs):
    flog = open('log.txt', 'a')
    flog.write(logargs)
    flog.close()

def copyfile(src, dst):

    logargs = '{:<6.2f}'.format(time.time()-st_time) + 'Start copying ' + src +' to ' + dst + '\n'
    logger(logargs)
    fsrc = open(src, 'rb')
    fdst = open(dst, 'wb')
    copyfileobj(fsrc, fdst)
    fsrc.close()
    fdst.close()
    logargs = '{:<6.2f}'.format(time.time()-st_time) + dst + ' is copied completely\n'
    logger(logargs)


def copyfileobj(fsrc, fdst, length=1024):
    
    while True:
        buffer = fsrc.read(length)
        if not buffer:
            break
        fdst.write(buffer)


if __name__ == '__main__':
    
    flog = open('log.txt', 'w')
    flog.close()
    st_time = time.time()

    while True:
        src = input("input the file name: ")
        dst = input("input the new name: ")
        my_thread = threading.Thread(
            target=copyfile, args=(src, dst))
        my_thread.start()