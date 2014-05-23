

#import mock
import unittest
import urllib2
import os

import sys, os
sys.path = [os.path.abspath(os.path.dirname(__file__))] + sys.path

#import library

class MainConfigTest(unittest.TestCase):

    def setUp(self):
        if(os.path.exists("./temp.cf")):
            os.remove("./temp.cf")

    def tearDown(self):
        if(os.path.exists("./temp.cf")):
            os.remove("./temp.cf")

    def test_init_no_args(self):
        import library
        mconf = library.MainConfig()

        self.assertEqual(mconf.configFileName,'/etc/yata/main.cf')
        self.assertTrue(mconf.config.get("common", "hostname") != None)
        self.assertEqual(mconf.config.get("common", "storeserver"),"https://www.whiteblack-cat.info")

    def test_init_with_args(self):
        import library
        mconf = library.MainConfig(configFile='noconf.cf', storeserver="http://localhost")

        self.assertEqual(mconf.configFileName,'noconf.cf')
        self.assertEqual(mconf.config.get("common", "ServerID"),None)
        self.assertEqual(mconf.config.get("common", "ServerKey"),None)
        self.assertTrue(mconf.config.get("common", "hostname") != None)
        self.assertEqual(mconf.config.get("common", "storeserver"),"http://localhost")

    def test_set_with_existing_section(self):
        import library
        mconf = library.MainConfig(configFile='./temp.cf', storeserver="http://localhost")
        mconf.set("common","testKey","testValue")
        self.assertEqual(mconf.config.get("common", "testKey"),"testValue")

    def test_set_with_no_existing_section(self):
        import library
        mconf = library.MainConfig(configFile='./temp.cf', storeserver="http://localhost")
        mconf.set("no_existing_section","testKey","testValue")
        self.assertEqual(mconf.config.get("no_existing_section", "testKey"),"testValue")

    def test_get_with_section_key(self):
        import library
        mconf = library.MainConfig(configFile='./temp.cf', storeserver="http://localhost")
        mconf.config.set("common","testKey","testValue")
        self.assertEqual(mconf.get("common", "testKey"),"testValue")

    def test_get_with_no_section_no_key(self):
        import library
        mconf = library.MainConfig(configFile='./temp.cf', storeserver="http://localhost")
        self.assertEqual(mconf.get("common", "testKey"),None)
        self.assertEqual(mconf.get("no_existing_section", "testKey"),None)

    def test_registry_server_valid_user_valid_server_num(self):
        import library
        def mock_connect_and_get_json(url, data=None):
            result = {"status":"OK", "id":"testID", "key":"testServerKey"}
            return result
        library.connect_and_get_json = mock_connect_and_get_json

        mconf = library.MainConfig(configFile='./temp.cf', storeserver="http://localhost")
        mconf.registry_server("valid userkey")

        self.assertEqual(mconf.config.get("common", "ServerID"),"testID")
        self.assertEqual(mconf.config.get("common", "ServerKey"),"testServerKey")

    def test_registry_server_invalid_user_valid_server_num(self):
        import library
        def mock_connect_and_get_json(url, data=None):
            result = {"status":"ERROR"}
            return result
        library.connect_and_get_json = mock_connect_and_get_json

        mconf = library.MainConfig(configFile='./temp.cf', storeserver="http://localhost")
        self.assertRaises(library.InvalidUserKey,mconf.registry_server,"invalid userkey")

    def test_registry_server_valid_user_invalid_server_num(self):
        import library
        def mock_connect_and_get_json(url, data=None):
            result = {"status":"ERROR","reason":"Too many servers"}
            return result
        library.connect_and_get_json = mock_connect_and_get_json

        mconf = library.MainConfig(configFile='./temp.cf', storeserver="http://localhost")
        self.assertRaises(library.TooManyServers,mconf.registry_server,"valid userkey")


"""
    @mock.patch('library.urllib2.urlopen')
    @mock.patch('library.os.uname')
    @mock.patch('library.syslog.syslog')
    def test_normal(self,mockSyslog,mockUname,mockReq):
        mockUname.return_value = ('Linux', 'devenv2', '3.13.0-24-generic', '#46-Ubuntu SMP Thu Apr 10 19:11:08 UTC 2014', 'x86_64')
        mockReq.return_value = mock.Mock()
        mockReq.return_value.read.return_value='{"id":"1","key":"VALID_SERVER_KEY","status":"OK"}'
        #openMock = mock.Mock()
        #openMock.return_value = mock.MagicMock(spec=file)
        conf=library.MainConfig("./temp.cf")
        #with mock.patch('__builtin__.open', openMock):
        self.assertNotEqual(conf.config.sections(),[])
        self.assertEqual(conf.getServerID(),None)
        self.assertEqual(conf.getServerKey(),None)
        self.assertEqual(conf.getServerName(),"devenv2")
        conf.registryServer("VALID_USER_KEY")
        self.assertEqual(conf.getServerID(),"1")
        self.assertEqual(conf.getServerKey(),"VALID_SERVER_KEY")
        conf.set("common","option","val")
        self.assertEqual(conf.get("common","option"),"val")
        conf.save()
        conf=library.MainConfig("./temp.cf")
        self.assertEqual(conf.getServerID(),"1")
        self.assertEqual(conf.getServerKey(),"VALID_SERVER_KEY")
        self.assertEqual(conf.getServerName(),"devenv2")
        self.assertEqual(conf.get("common","option"),"val")

    @mock.patch('library.urllib2.urlopen')
    @mock.patch('library.syslog.syslog')
    def test_invalid_user_key(self,mockSyslog,mockReq):
        openMock = mock.Mock()
        openMock.return_value = mock.MagicMock(spec=file)
        mockReq.return_value = mock.Mock()
        mockReq.return_value.read.return_value='{"status":"ERROR"}'
        conf=library.MainConfig()
        with mock.patch('__builtin__.open', openMock):
            self.assertEqual(conf.getServerID(),None)
            self.assertEqual(conf.getServerKey(),None)
            self.assertRaises(library.InvalidUserKey,conf.registryServer,"INVALID_USER_KEY")
            self.assertTrue(mockSyslog.has_been_called())
            conf=None

    @mock.patch('library.syslog.syslog')
    def test_cannot_connect_to_server(self,mockSyslog):
        openMock = mock.Mock()
        openMock.return_value = mock.MagicMock(spec=file)
        mockURL = mock.Mock(side_effect=urllib2.URLError(""))
        #mockURL.return_value = mock.MagicMock(spec=file)
        conf=library.MainConfig()
        with mock.patch('__builtin__.open', openMock):
            self.assertEqual(conf.getServerID(),None)
            self.assertEqual(conf.getServerKey(),None)
            with mock.patch('library.urllib2.urlopen', mockURL):
                self.assertRaises(urllib2.URLError,conf.registryServer,"VALID_USER_KEY")
                self.assertTrue(mockSyslog.has_been_called())
                conf=None

    @mock.patch('library.syslog.syslog')
    def test_server_error(self,mockSyslog):
        openMock = mock.Mock()
        openMock.return_value = mock.MagicMock(spec=file)
        mockURL = mock.Mock(side_effect=urllib2.HTTPError("http://localhost/", 500, "Server is down", None, None))
        conf=library.MainConfig()
        with mock.patch('__builtin__.open', openMock):
            self.assertEqual(conf.getServerID(),None)
            self.assertEqual(conf.getServerKey(),None)
            with mock.patch('library.urllib2.urlopen', mockURL):
                self.assertRaises(urllib2.HTTPError,conf.registryServer,"VALID_USER_KEY")
                self.assertTrue(mockSyslog.has_been_called())
                conf=None

    #@patch('library.ConfigParser.SafeConfigParser')
    @mock.patch('library.syslog.syslog')
    def test_file_error(self,mockSyslog):
        confMock = mock.Mock(spec=library.ConfigParser.ConfigParser)
        openMock = mock.Mock(side_effect=IOError())
        openMock.return_value = mock.MagicMock(spec=file)
        openMock2 = mock.Mock()
        openMock2.return_value = mock.MagicMock(spec=file)
        with mock.patch('library.ConfigParser.ConfigParser', confMock):
            conf=library.MainConfig()
            conf.set("section","option","val")
            with mock.patch('__builtin__.open', openMock):
                self.assertRaises(IOError,conf.save)
                openMock.assert_called_with('/etc/yata/main.cf', 'w')
                self.assertTrue(mockSyslog.has_been_called())
            with mock.patch('__builtin__.open', openMock2):
                conf=None
"""

if __name__ == "__main__":
    unittest.main()

