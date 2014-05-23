
import os
import urllib2
import urllib
import json
import ConfigParser
import syslog


class InvalidUserKey(Exception):
    message = "User key is not valid"


class TooManyServers(Exception):
    message = "Too many servers"


def connect_and_get_json(url, data=None):
    """
    This function connects to host server, send data and get json response.
    This function returns dictionary.
    """
    try:
        response = None
        if(data):
            tempD = urllib.urlencode(data)
            response = urllib2.urlopen(url, tempD)
        else:
            response = urllib2.urlopen(url)
    except urllib2.URLError:
        syslog.syslog(syslog.LOG_ERR, "Cannot connect to %s" % url)
        raise
    except urllib2.HTTPError:
        syslog.syslog(syslog.LOG_ERR, "Server error on %s" % url)
        raise
    data = response.read()
    try:
        return json.loads(data)
    except Exception:
        syslog.syslog(
            syslog.LOG_ERR, "Invalid Server Response on %s. Response is '%s'" % (url, data))
        raise


class MainConfig():
    """
    Config file object for agents.
    """

    def __init__(self, configFile='/etc/yata/main.cf', storeserver="https://www.whiteblack-cat.info"):
        self.ServerID = None
        self.configFileName = configFile
        self.config = ConfigParser.ConfigParser()
        self.config.read(self.configFileName)
        if(self.config.sections() == []):
            self.config.add_section("common")
            self.config.set("common", "ServerID", None)
            self.config.set("common", "ServerKey", None)
            self.config.set("common", "hostname", os.uname()[1])
            self.config.set("common", "storeserver", storeserver)

    def set(self, section, key, value):
        """
        set method sets key:value pair in section.
        When config file has not section, set method creates the section
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)

    def get(self, section, key):
        """
        get method gets value of key in section.
        When the section or the key is not existed, get method returns None
        """
        try:
            return self.config.get(section, key)
        except ConfigParser.NoSectionError:
            return None
        except ConfigParser.NoOptionError:
            return None

    def registry_server(self, userkey):
        """
        registry_server method connects store server with user key and send hostname.
        Also registry_server method receives server id and key.  The id and key are stored
        in config file.
        """
        url = '%s/common/api/registeryserver/%s' % (
            self.get_store_server(), userkey)
        dataDic = connect_and_get_json(url, {"hostname": self.get_server_name()})
        if(dataDic["status"] == "OK"):
            self.config.set("common", "ServerID", dataDic["id"])
            self.config.set("common", "ServerKey", dataDic["key"])
        elif(dataDic["status"] == "ERROR"):
            if("reason" in dataDic and dataDic["reason"] == "Too many servers"):
                syslog.syslog(syslog.LOG_ERR, TooManyServers.message)
                raise TooManyServers()
            else:
                syslog.syslog(syslog.LOG_ERR, InvalidUserKey.message)
                raise InvalidUserKey()

    def save(self):
        try:
            fp = open(self.configFileName, "w")
            self.config.write(fp)
        except IOError:
            syslog.syslog(
                syslog.LOG_ERR, "Cannot open %s as write" % self.configFileName)
            raise

    def mkdir(self):
        try:
            os.mkdir("/etc/yata")
        except OSError, e:
            if(e.errno != 17):
                raise

    def get_server_name(self):
        return self.config.get("common", "hostname")

    def get_server_id(self):
        return self.config.get("common", "ServerID")

    def get_server_key(self):
        return self.config.get("common", "ServerKey")

    def get_store_server(self):
        return self.get("common", "storeserver")

    def set_store_server(self, server):
        return self.set("common", "storeserver", server)

