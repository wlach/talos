import PerfConfigurator as pc
import os, sys
import optparse

class remotePerfConfigurator(pc.PerfConfigurator):
    def __init__(self, options):
        self.__dict__.update(options.__dict__)
        self._remote = False
        if (self.remoteDevice <> ''):
            self._setupRemote()
            options.deviceRoot = self.deviceRoot

        #this depends on buildID which requires querying the device
        pc.PerfConfigurator.__init__(self, options)
        pc.PerfConfigurator.attributes += ['remoteDevice', 'remotePort', 'webServer', 'deviceRoot']

    def _setupRemote(self):
        import devicemanager
        self.testAgent = devicemanager.DeviceManager(self.remoteDevice, self.remotePort)
        self.deviceRoot = self.testAgent.getDeviceRoot()
        self._remote = True

    def _dumpConfiguration(self):
        pc.PerfConfigurator._dumpConfiguration(self)

    def convertLine(self, line, testMode, printMe):
        printMe, newline = pc.PerfConfigurator.convertLine(self, line, testMode, printMe)
        if 'deviceip:' in line:
           newline = 'deviceip: %s\n' % self.remoteDevice
        if 'webserver:' in line:
           newline = 'webserver: %s\n' % self.webServer
        if 'deviceroot:' in line:
            newline = 'deviceroot: %s\n' % self.deviceRoot
        if 'deviceport:' in line:
            newline = 'deviceport: %s\n' % self.remotePort
        if 'remote:' in line:
            newline = 'remote: %s\n' % self._remote
        if 'init_url' in line:
            newline = self.convertUrlToRemote(line)
        if testMode:
            if ('url' in line) and ('url_mod' not in line):
                newline = self.convertUrlToRemote(line)
        if 'talos.logfile:' in line:
            parts = line.split(':')
            if (parts[1] != None and parts[1].strip() == ''):
                lfile = os.path.join(os.getcwd(), 'browser_output.txt')
            else:
                lfile = parts[1].strip().strip("'")
            lfile = self.deviceRoot + '/' + lfile.split('/')[-1]
            newline = '%s: %s\n' % (parts[0], lfile)
        return printMe, newline

    def convertUrlToRemote(self, line):
        """
          For a give url line in the .config file, add a webserver.
          In addition if there is a .manifest file specified, covert 
          and copy that file to the remote device.
        """
        if self._remote == False:
            return line

        parts = line.split(' ')
        newline = ''
        for part in parts:
            if ('.html' in part):
                newline += 'http://' + self.webServer + '/' + part
            elif ('.manifest' in part):
                newline += self.buildRemoteManifest(part)
            elif ('.xul' in part):
                newline += 'http://' + self.webServer + '/' + part
            else:
                newline += part
                if (part <> parts[-1]):
                    newline += ' '

        #take care of tpan/tzoom tests
        newline = newline.replace('webServer=', 'webServer=' + self.webServer);
        return newline

    def buildRemoteManifest(self, manifestName):
        """
          Take a given manifest name, convert the localhost->remoteserver, and then copy to the device
          returns the remote filename on the device so we can add it to the .config file
        """
        remoteName = self.deviceRoot
        fHandle = open(manifestName, 'r')
        manifestData = fHandle.read()
        fHandle.close()

        newHandle = open(manifestName + '.remote', 'w')
        for line in manifestData.split('\n'):
            newHandle.write(line.replace('localhost', self.webServer) + "\n")
        newHandle.close()

        remoteName += '/' + os.path.basename(manifestName) + ' '
        if self.testAgent.pushFile(manifestName + '.remote', remoteName) == None:
            raise pc.Configuration("Unable to copy remote manifest file " 
                                + manifestName + ".remote to " + remoteName)
        return remoteName

    def _getMasterIniContents(self):
        """ Open and read the application.ini on the device under test """
        if (self._remote == True):
            localfilename = "remoteapp.ini"
            
            #we need a better OS detection method, but for now this is how we work on android
            if (self.exePath == 'org.mozilla.fennec'):
              remoteFile = '/data/data/' + self.exePath + '/' + self.masterIniSubpath            
            else:
              parts = self.exePath.split('/')
              remoteFile = '/'.join(parts[0:-1]) + '/' + self.masterIniSubpath
            
            retVal = self.testAgent.getFile(remoteFile, localfilename)
            master = open(localfilename)
        else:
            return pc.PerfConfigurator._getMasterIniContents(self)
            
        data = master.read()
        master.close()
        return data.split('\n')

class remoteTalosOptions(pc.TalosOptions):

    def __init__(self, **kwargs):
        defaults = {}
        pc.TalosOptions.__init__(self)

        self.add_option("-r", "--remoteDevice", action="store",
                    type = "string", dest = "remoteDevice",
                    help = "Device IP of the SUTAgent")
        defaults["remoteDevice"] = ''

        self.add_option("-p", "--remotePort", action="store",
                    type="int", dest = "remotePort",
                    help = "port the SUTAgent uses (defaults to 20701")
        defaults["remotePort"] = 20701

        self.add_option("--webServer", action="store",
                    type = "string", dest = "webServer",
                    help = "IP address of the webserver hosting the talos files")
        defaults["webServer"] = ''

        self.add_option("--deviceRoot", action="store",
                    type = "string", dest = "deviceRoot",
                    help = "path on the device that will hold files and the profile")
        defaults["deviceRoot"] = ''
        self.set_defaults(**defaults)

    def verifyOptions(self, options):
        #webServer can be used without remoteDevice, but is required when using remoteDevice
        if (options.remoteDevice != '' or options.deviceRoot != ''):
            if (options.webServer == 'localhost'  or options.remoteDevice == ''):
                raise AssertionError("ERROR: When running Talos on a remote device, you need to provide a webServer and optionally a remotePort")
        return options

def main(argv=None):
    parser = remoteTalosOptions()
    options, args = parser.parse_args()

    try:
      options = parser.verifyOptions(options)
    except err:
      print err.msg
      return 2

    configurator = remotePerfConfigurator(options)
    try:
        configurator.writeConfigFile()
    except pc.Configuration, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        return 5
    return 0
    
if __name__ == "__main__":
    sys.exit(main())
