
import os
import time
import unittest
import random
import threading


try:
    # python 2
    from urllib2 import urlopen
except ImportError:
    # python 3
    from urllib.request import urlopen


import stackimpact
from stackimpact.runtime import min_version, runtime_info
from test_server import TestServer


class BlockReporterTestCase(unittest.TestCase):

    def test_record_block_profile(self):
        stackimpact._agent = None
        agent = stackimpact.start(
            dashboard_address = 'http://localhost:5001',
            agent_key = 'key1',
            app_name = 'TestPythonApp',
            debug = True
        )

        lock = threading.Lock()
        event = threading.Event()

        def lock_lock():
            lock.acquire()
            time.sleep(0.5)
            lock.release()

        def lock_wait():
            lock.acquire()
            lock.release()


        def event_lock():
            time.sleep(0.5)
            event.set()


        def event_wait():
            event.wait()


        def handler():
            time.sleep(0.4)

        def url_wait():
            server = TestServer(5010, 0.4, handler)
            server.start()
            urlopen('http://localhost:5010')
            server.join()


        result = {}
        def record():
            agent.frame_selector.add_http_frame_regexp(os.path.join('tests', 'test_server.py'))
            agent.block_reporter.record(2)

        record_t = threading.Thread(target=record)
        record_t.start()

        # simulate lock
        t = threading.Thread(target=lock_lock)
        t.start()

        t = threading.Thread(target=lock_wait)
        t.start()

        # simulate event
        t = threading.Thread(target=event_lock)
        t.start()

        t = threading.Thread(target=event_wait)
        t.start()

        # simulate network
        t = threading.Thread(target=url_wait)
        t.start()

        # make sure signals are delivered in python 2, when main thread is waiting
        if runtime_info.PYTHON_2:
            while record_t.is_alive():
                pass

        record_t.join()

        #print(agent.block_reporter.block_profile)
        #print(agent.block_reporter.http_profile)

        self.assertTrue('lock_wait' in str(agent.block_reporter.block_profile))
        self.assertTrue('event_wait' in str(agent.block_reporter.block_profile))
        self.assertTrue('url_wait' in str(agent.block_reporter.block_profile))
        self.assertTrue('handler' in str(agent.block_reporter.http_profile))

        agent.destroy()


if __name__ == '__main__':
    unittest.main()
