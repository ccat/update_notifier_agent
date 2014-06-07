
import os
import shutil
from distutils.dir_util import copy_tree
import sys
import json
import datetime
import subprocess
import random
#import pytz

from library import *


class UploadFailedError(Exception):
    message = "Failed to upload data"


class Agent():
    """
    Agent for Update Notifier.  This agent detects virtualenvs and upload 'pip freeze' results.
    """

    def __init__(self, config=None):
        if not config:
            self.config = MainConfig()
        else:
            self.config = config

    def is_registered(self):
        if not self.config.get_server_id():
            return False
        return True

    def register(self, userkey):
        self.config.registry_server(userkey)

    def save(self):
        self.config.save()

    def install(self):
        self.mkdir()
        #shutil.copytree("../agents", "/usr/local/lib/yata/agents")
        copy_tree("../agents", "/usr/local/lib/yata/agents")

        crontab = open("/etc/crontab", "r")
        for line in crontab:
            if(line.find("update_notifier_agent")!=-1):
                return
        crontab.close()

        crontab = open("/etc/crontab", "a")
        crontab.write("\n")
        minutes = random.randint(0, 59)
        hours = random.randint(1, 23)
        crontab.write(
                      "%s %s * * * root python /usr/local/lib/yata/agents/update_notifier_agent.py"  % (minutes, hours))
        crontab.close()

    def mkdir(self):
        self.config.mkdir()
        try:
            os.mkdir("/usr/local/lib/yata")
        except OSError, e:
            if(e.errno != 17):
                raise

    def find_virtualenvs(self):
        result = ["global"]
        for root, dirs, files in os.walk("/"):
            if "activate" in files:
                tempPath = os.path.join(root, "activate")
                try:
                    if 'VIRTUAL_ENV' in open(tempPath).read():
                        result.append(tempPath)
                except Exception:
                    pass
        self.set("virtualenvs", json.dumps(result))
        return result

    def check_all(self,debug = False):
        result = {"timestamp": datetime.datetime.utcnow().isoformat()}
        result = self.check_pip(result)
        result = self.check_dpkg(result)
        if(debug):
            print result
        return result

    def check_pip(self,result):
        #result = {"timestamp": datetime.datetime.utcnow().isoformat()}
        envs = json.loads(self.get("virtualenvs"))

        temp = {}
        for item in envs:
            temp[item] = self._pipcheck(item)
        result["pip"] = json.dumps(temp)

        return result

    def check_dpkg(self,result):
        try:
            dpkg_file = open("/var/lib/dpkg/available","r")
        except:
            return result

        tempResult = self._dpkg_current(dpkg_file)
        dpkg_file.close()
        tempResult = self._dpkg_update(tempResult)

        result["dpkg"] = json.dumps(tempResult)

        return result

    def upload(self, data):
        url = '%s/update_notifier/api/upload/%s/%s/' % (
            self.config.get_store_server(), self.config.get_server_id(), self.config.get_server_key())
        result = connect_and_get_json(url, data)
        if(result["status"] != "OK"):
            syslog.syslog(syslog.LOG_ERR, UploadFailedError.message)
            raise UploadFailedError()

    def set(self, key, item):
        self.config.set("update_notifier", key, item)

    def get(self, key):
        return self.config.get("update_notifier", key)

    def _dpkg_current(self,dpkg_file):
        tempResult = {}
        tempPackage = None

        for line in dpkg_file:
            if(line.startswith("Package:")):
                tempPackage = {}
                tempPackage["name"]=line.split(": ")[1][0:-1]

            elif(line.startswith("Version:")):
                tempPackage["current"]=line.split(": ")[1][0:-1]
                tempResult[tempPackage["name"]] = tempPackage
                tempPackage = None

        return tempResult

    def _dpkg_update(self,result):
        try:
            subprocess.check_output(["apt-get", "update"])
        except:
            result["status"] = "error"
            return result
        try:
            tempStr = subprocess.check_output(["apt-get","-V","-s","upgrade"])
        except:
            result["status"] = "error"
            return result

        tempStr = tempStr.split("\n")
        flag=False
        for item in tempStr:
            if(item.startswith("The following packages will be upgraded")):
                flag=True
            elif(item.find("upgraded,")!=-1):
                flag=False
            elif(flag):
                item = item.lstrip()
                item = item.split(" ")
                if(item[0] not in result):
                    result[item[0]] = {"name":item[0],"current":item[1][1:]}
                result[item[0]]["latest"] = item[3][0:-1]
                #openssl (1.0.1f-1ubuntu2.1 => 1.0.1f-1ubuntu2.2)

        return result

    def _pipcheck(self, activate):
        f = open("/tmp/tempcommand", "w")
        f.write("#!/bin/bash\n")
        if(activate != "global"):
            # print activate
            f.write("source %s\n" % activate)
        f.write("pip freeze\n")
        f.close()
        subprocess.check_output(["chmod", "755", "/tmp/tempcommand"])
        # pipfreeze=subprocess.check_output(["/tmp/tempcommand"])
        # (["/bin/bash","/tmp/tempcommand"])
        pipfreeze = subprocess.check_output(["/tmp/tempcommand"])
        subprocess.check_output(["rm", "-f", "/tmp/tempcommand"])
        result = {}
        # print pipfreeze
        for line in pipfreeze.split("\n"):
            pack = line.split("==")
            if(len(pack) == 2):
                result[pack[0]] = pack[1]
        return result


def main():
    """
    Usage: python update_notifier_agent.py <command>
      command:
         scan : detects virtualenvs
         install : copy files to /usr/local/lib/yata and modify /etc/crontab
         <None> : upload pip freeze results.  Basically, called by cron.
    """

    agent = Agent()
    argvs = sys.argv
    debug = False
    if(len(argvs) > 1):
        if(argvs[1] == "scan_envs"):
            agent.find_virtualenvs()
        elif(argvs[1] == "install"):
            if(len(argvs) > 2):
                agent.config.set_store_server(argvs[2])
            if not agent.is_registered():
                userkey = raw_input("Your User key:")
                agent.register(userkey)
            agent.install()
            agent.find_virtualenvs()
        elif(argvs[1] == "debug"):
            debug = True
    agent.save()
    agent.upload(agent.check_all(debug))


if __name__ == "__main__":
    main()

