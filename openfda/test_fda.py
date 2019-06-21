import os
import subprocess
import sys
import threading
import time
import unittest

import requests

from html.parser import HTMLParser

PYTHON_CMD = os.path.abspath(sys.executable)

class OpenFDAHTMLParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.actions_list = []
        self.forms_number = 0
        self.items_number = 0

    def handle_starttag(self, tag, attrs):
        if tag == "form":
            self.forms_number += 1
            for attr in attrs:
                if attr[0] == 'action':
                    self.actions_list.append(attr[1])
        elif tag == "li":
            self.items_number += 1


    def handle_endtag(self, tag):
        pass


    def handle_data(self, data):
        pass


class WebServer(threading.Thread):
    def run(self):
        cmd = [PYTHON_CMD, 'server.py']
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE)
        TestOpenFDA.WEBSERVER_PROC = proc
        outs, errs = proc.communicate()
        errs_str = errs.decode("utf8")
        if 'Address already in use' in errs_str:
            TestOpenFDA.PORT_BUSY = True
            return

class TestOpenFDA(unittest.TestCase):
    WEBSERVER_PROC = None
    PORT_BUSY = False
    TEST_PORT = 8000
    TEST_DRUG = 'Aspirin'
    TEST_COMPANY = 'Bayer'
    TEST_ACTIONS = ['listDrugs', 'buscarDrug', 'listCompanies', 'buscarCompany', 'listWarnings']

    @classmethod
    def setUpClass(cls):
        WebServer().start()
        time.sleep(1)
        if cls.PORT_BUSY:
            raise RuntimeError("PORT BUSY")

    @classmethod
    def tearDownClass(cls):
        cls.WEBSERVER_PROC.kill()

    def test_web_server_init(self):
        resp = requests.get('http://localhost:' + str(self.TEST_PORT))
        parser = OpenFDAHTMLParser()
        parser.feed(resp.text)
        self.TEST_ACTIONS.remove('listWarnings')
        try:
            parser.actions_list.remove('listWarnings')
        except ValueError:
            pass
        self.assertEqual(len(parser.actions_list), 4)
        self.assertEqual(set(self.TEST_ACTIONS), set(parser.actions_list))
        self.TEST_ACTIONS.append('listWarnings')

    def test_web_server_init_warnings(self):
        resp = requests.get('http://localhost:' + str(self.TEST_PORT))
        parser = OpenFDAHTMLParser()
        parser.feed(resp.text)
        self.assertEqual(parser.forms_number, 5)
        self.assertEqual(set(self.TEST_ACTIONS), set(parser.actions_list))

    def test_list_drugs(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/listDrugs?limit=10'
        resp = requests.get(url)
        parser = OpenFDAHTMLParser()
        parser.feed(resp.text)
        self.assertEqual(parser.items_number, 10)

    def test_list_drugs_limit(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/listDrugs?limit=22'
        resp = requests.get(url)
        parser = OpenFDAHTMLParser()
        parser.feed(resp.text)
        self.assertEqual(parser.items_number, 22)

    def test_buscar_drug(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/buscarDrug?active_ingredient="%s"' % self.TEST_DRUG
        resp = requests.get(url)
        parser = OpenFDAHTMLParser()
        parser.feed(resp.text)
        self.assertEqual(parser.items_number, 10)

    def test_list_companies(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/listCompanies?limit=10'
        resp = requests.get(url)
        parser = OpenFDAHTMLParser()
        parser.feed(resp.text)
        self.assertEqual(parser.items_number, 10)

    def test_list_warnings(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/listWarnings?limit=10'
        resp = requests.get(url)
        parser = OpenFDAHTMLParser()
        parser.feed(resp.text)
        self.assertEqual(parser.items_number, 10)

    def test_buscar_company(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/buscarCompany?company=' + self.TEST_COMPANY
        resp = requests.get(url)
        parser = OpenFDAHTMLParser()
        parser.feed(resp.text)
        self.assertEqual(parser.items_number, 10)

    def test_not_found(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/not_exists_resource'
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_redirect(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/redirect'
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_auth(self):
        url = 'http://localhost:' + str(self.TEST_PORT)
        url += '/secret'
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 401)


if __name__ == "__main__":
unittest.main(warnings='ignore')