import Queue
import threading
import time

class scraperThread (threading.Thread):
    def __init__(self, t_id, name, queue):
        threading.Thread.__init__(self)
        self.t_id = t_id
        self.name = name
        self.queue = queue
    def run(self):
        print "Starting " + self.name + " ..\n"
        process_queue(self.name, self.queue)
        print "Finishing " + self.name + " ..\n"

def process_queue(name, queue):
    while not exitFlag:
        queueLock.acquire()
        if not urlQueue.empty():
            url = queue.get()
            queueLock.release()
            print "Thread " + name + " beginning scraping on " + url + " ..\n"
            scrape(url)
            print "Thread " + name + " finished scraping on " + url + "\n"
        else:
            queueLock.release()
        time.sleep(1)