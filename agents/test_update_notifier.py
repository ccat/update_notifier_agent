
import sys, os
sys.path = [os.path.abspath(os.path.dirname(__file__))] + sys.path

import update_notifier_agent
import library

import mock
import unittest
import datetime
import json

class MockFile():

    def __init__(self,content=""):
        self.content=content
        self.readable=True
        self.writable=True

    def read(self):
        return self.content

    def write(self,str):
        self.content=self.content+str

    def close(self):
        pass

def openMock(*args):
    if(args[0]=='/virtualenv/bin/activate'):
        return MockFile("aaa VIRTUAL_ENV='bb' bbb")
    if(args[0]=='/noauth/virtualenv/bin/activate'):
        raise IOError
    raise IOError

def openWriteMock(*args):
    return MockFile()

def checkOutputMock(*args):
    return """
virtualenv==1.11.4
mock==1.0.1
nose==1.3.1
"""

class MockWalk():
    def __init__(self,dirs):
        self.dirs=dirs
        self.ind=0
    def __iter__(self):
        return self
    def next(self):
        if(len(self.dirs)==self.ind):
            raise StopIteration()
        self.ind=self.ind+1
        return self.dirs[self.ind-1]
    def __call__(self,*args):
        return self

class UpdateNotifierAgentTest(unittest.TestCase):


    def setUp(self):
        if(os.path.exists("./temp.cf")):
            os.remove("./temp.cf")

        self.allDIRs = [
            ('/no_virtualenv', ['dir1','dir2'], ['file1','file2']),
            ('/virtualenv', ['bin','lib','dir1','dir2'], ['file1','file2']),
            ('/virtualenv/bin', [], ['activate','file2']),
            ('/virtualenv/lib', [], []),
            ('/noauth/virtualenv/bin', [], ['activate','file2']),
            ]
        self.walkMock = mock.MagicMock(side_effect=MockWalk(self.allDIRs))
        #self.walkMock.__iter__.return_value = self.allDIRs

    def tearDown(self):
        if(os.path.exists("./temp.cf")):
            os.remove("./temp.cf")

    def test_agent_find_virtualenvs (self):
        testAgent=update_notifier_agent.Agent(library.MainConfig("./temp.cf"))
        mockObj = mock.MagicMock(side_effect=openMock)
        with mock.patch('update_notifier_agent.os.walk', self.walkMock):
            with mock.patch('__builtin__.open', mockObj):
                result=testAgent.find_virtualenvs()
                self.assertEqual(result,["global",'/virtualenv/bin/activate'])

    @mock.patch('update_notifier_agent.subprocess.call')
    @mock.patch('update_notifier_agent.datetime')
    def test_agent_check_pip(self,mockDatetime,mockCall):
        testAgent=update_notifier_agent.Agent(library.MainConfig("./temp.cf"))
        testAgent.set("virtualenvs",'["global","/virtualenv/bin/activate"]')
        times=datetime.datetime.utcnow()
        mockDatetime.datetime.utcnow.return_value =times
        writeMock = mock.MagicMock(side_effect=openWriteMock)
        checkoutMock = mock.MagicMock(side_effect=checkOutputMock)

        with mock.patch('__builtin__.open', writeMock):
            with mock.patch('subprocess.check_output', checkoutMock):
                result=testAgent.check_pip()

        self.assertEqual(json.loads(result["pip"]),{
                "global":{"virtualenv":"1.11.4","mock":"1.0.1","nose":"1.3.1"},
                "/virtualenv/bin/activate":{"virtualenv":"1.11.4","mock":"1.0.1","nose":"1.3.1"},
            })

    @mock.patch('library.urllib2.urlopen')
    def test_agent_upload(self,mockURLopen):
        mockURLopen.return_value = mock.MagicMock()
        mockURLopen.return_value.read.return_value='{"status":"OK"}'

        testAgent=update_notifier_agent.Agent(library.MainConfig("./temp.cf"))
        testAgent.set("virtualenvs",["global",'/virtualenv/bin/activate'])
        pipResult={
          "timestamp":datetime.datetime.utcnow(),
          "pip":{
                "global":{"virtualenv":"1.11.4","mock":"1.0.1","nose":"1.3.1"},
                "/virtualenv/bin/activate":{"virtualenv":"1.11.4","mock":"1.0.1","nose":"1.3.1"},
        }}
        testAgent.upload(pipResult)

    """
    @mock.patch("agent.MainConfig")
    @mock.patch("agent.urllib2.Request")
    def test_agent_registryServer (self,mock_MainConfig,mockReq):
        tempServerName="servername"
        tempServerKey="secret"
        tempServerId="1"
        mMC= mock_MainConfig.return_value
        mMC.getServerName.return_value = tempServerName
        mMC.serverName = tempServerName
        mMC.getServerID.return_value = None
        mMC.getServerKey.return_value = None
        reqm = mock.Mock()
        reqm.get_data.return_value = '{"id":"'+ tempServerId +'","key":"'+tempServerKey+'"}'
        mockReq.return_value = reqm

        ag=agent.Agent()
        ag.registryServer()

        #self.assertEquals(ag.config.serverName, tempServerName)
        self.assertEquals(ag.config.serverKey, tempServerKey)
        self.assertEquals(ag.config.serverID, tempServerId)
    """

    """
    @mock.patch('agent.os.path')
    @mock.patch("agent.os")
    def test_config_normal(self, mock_os, mock_path):
        mock_path.isfile.return_value = False
        conf=agent.MainConfig()

    def test_agent_install(self,):
        ag=agent.Agent()
        ag.install()
    """


if __name__ == "__main__":
    unittest.main()

