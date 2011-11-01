# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is standalone Firefox Windows performance test.
#
# The Initial Developer of the Original Code is Google Inc.
# Portions created by the Initial Developer are Copyright (C) 2006
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Annie Sullivan <annie.sullivan@gmail.com> (original author)
#   Alice Nodelman <anodelman@mozilla.com>
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

"""A set of functions to set up a browser with the correct
   preferences and extensions in the given directory.

"""

__author__ = 'annie.sullivan@gmail.com (Annie Sullivan)'


import platform
import os
import os.path
import re
import shutil
import tempfile
import time
import glob
import zipfile
from xml.dom import minidom
import shutil

import utils
from utils import talosError
import subprocess

def zip_extractall(zipfile, rootdir):
    """Python 2.4 compatibility instead of ZipFile.extractall."""
    for name in zipfile.namelist():
        if name.endswith('/'):
            if not os.path.exists(os.path.join(rootdir, name)):
                os.makedirs(os.path.join(rootdir, name))
        else:
            destfile = os.path.join(rootdir, name)
            destdir = os.path.dirname(destfile)
            if not os.path.isdir(destdir):
                os.makedirs(destdir)
            data = zipfile.read(name)
            f = open(destfile, 'wb')
            f.write(data)
            f.close()

class FFSetup(object):

    ffprocess = None
    _remoteWebServer = 'localhost'
    _deviceroot = ''
    _host = ''
    _port = ''
    _hostproc = None

    def __init__(self, procmgr, options = None):
        self.ffprocess = procmgr
        self._hostproc = procmgr
        if options <> None:
            self.intializeRemoteDevice(options)

    def initializeRemoteDevice(self, options, hostproc = None):
        self._remoteWebServer = options['webserver']
        self._deviceroot = options['deviceroot']
        self._host = options['host']
        self._port = options['port']
        self._env = options['env']
        if (hostproc == None):
          self._hostproc = self.ffprocess
        else:
          self._hostproc = hostproc
        
    def PrefString(self, name, value, newline):
        """Helper function to create a pref string for profile prefs.js
            in the form 'user_pref("name", value);<newline>'

        Args:
            name: String containing name of pref
            value: String containing value of pref
            newline: Line ending to use, i.e. '\n' or '\r\n'

        Returns:
            String containing 'user_pref("name", value);<newline>'
        """

        out_value = str(value)
        if type(value) == bool:
            # Write bools as "true"/"false", not "True"/"False".
            out_value = out_value.lower()
        if type(value) == str:
            # Write strings with quotes around them.
            out_value = '"%s"' % value
        return 'user_pref("%s", %s);%s' % (name, out_value, newline)

    def install_addon(self, profile_path, addon):
        """Installs the given addon in the profile.
           most of this borrowed from mozrunner, except downgraded to work on python 2.4
           # Contributor(s) for mozrunner:
           # Mikeal Rogers <mikeal.rogers@gmail.com>
           # Clint Talbert <ctalbert@mozilla.com>
           # Henrik Skupin <hskupin@mozilla.com>
        """
        def getText(nodelist):
            rc = []
            for node in nodelist:
                if node.nodeType == node.TEXT_NODE:
                    rc.append(node.data)
            return str(''.join(rc))
        def find_id(desc):
            addon_id = None
            for elem in desc:
                apps = elem.getElementsByTagName('em:targetApplication')
                if apps:
                    for app in apps:
                        #remove targetApplication nodes, they contain id's we aren't interested in
                        elem.removeChild(app)
                    if elem.getElementsByTagName('em:id'):
                        addon_id = getText(elem.getElementsByTagName('em:id')[0].childNodes)
                    elif elem.hasAttribute('em:id'):
                        addon_id = str(elem.getAttribute('em:id'))
                else:
                    if ((elem.hasAttribute('RDF:about')) and (elem.getAttribute('RDF:about') == 'urn:mozilla:install-manifest')):
                        if elem.getElementsByTagName('NS1:id'):
                            addon_id = getText(elem.getElementsByTagName('NS1:id')[0].childNodes)
                        elif elem.hasAttribute('NS1:id'):
                            addon_id = str(elem.getAttribute('NS1:id'))
            return addon_id

        def find_unpack(desc):
            unpack = 'false'
            for elem in desc:
                if elem.getElementsByTagName('em:unpack'):
                    unpack = getText(elem.getElementsByTagName('em:unpack')[0].childNodes)
                elif elem.hasAttribute('em:unpack'):
                    unpack = str(elem.getAttribute('em:unpack'))
                elif elem.getElementsByTagName('NS1:unpack'):
                    unpack = getText(elem.getElementsByTagName('NS1:unpack')[0].childNodes)
                elif elem.hasAttribute('NS1:unpack'):
                    unpack = str(elem.getAttribute('NS1:unpack'))
                if not unpack:  #no value in attribute/elements, defaults to false
                    unpack = 'false'
            return unpack

        tmpdir = None
        addon_id = None
        tmpdir = tempfile.mkdtemp(suffix = "." + os.path.split(addon)[-1])
        zip_extractall(zipfile.ZipFile(addon), tmpdir)
        addonTmpPath = tmpdir

        doc = minidom.parse(os.path.join(addonTmpPath, 'install.rdf')) 
        # description_element =
        # tree.find('.//{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description/')

        desc = doc.getElementsByTagName('Description')
        addon_id = find_id(desc)
        unpack = find_unpack(desc)
        if not addon_id:
          desc = doc.getElementsByTagName('RDF:Description')
          addon_id = find_id(desc)
          unpack = find_unpack(desc)
        
        if not addon_id: #bail out, we don't have an addon id
            raise talosError("no addon_id found for extension")
                
        if (str.lower(unpack) == 'true'):  #install addon unpacked
            addon_path = os.path.join(profile_path, 'extensions', addon_id)
            #if an old copy is already installed, remove it 
            if os.path.isdir(addon_path): 
                shutil.rmtree(addon_path, ignore_errors=True) 
            shutil.move(addonTmpPath, addon_path) 
        else: #do not unpack addon
            addon_file = os.path.join(profile_path, 'extensions', addon_id + '.xpi')
            if os.path.isfile(addon_file): 
                os.remove(addon_file) 
            shutil.copy(addon, addon_file)
            shutil.rmtree(addonTmpPath, ignore_errors=True)

    def CreateTempProfileDir(self, source_profile, prefs, extensions):
        """Creates a temporary profile directory from the source profile directory
            and adds the given prefs and links to extensions.

        Args:
            source_profile: String containing the absolute path of the source profile
                            directory to copy from.
            prefs: Preferences to set in the prefs.js file of the new profile.  Format:
                    {"PrefName1" : "PrefValue1", "PrefName2" : "PrefValue2"}
            extensions: list of paths to .xpi files to be installed

        Returns:
            String containing the absolute path of the profile directory.
        """

        # Create a temporary directory for the profile, and copy the
        # source profile to it.
        temp_dir = tempfile.mkdtemp()
        profile_dir = os.path.join(temp_dir, 'profile')
        shutil.copytree(source_profile, profile_dir)
        self._hostproc.MakeDirectoryContentsWritable(profile_dir)

        # Copy the user-set prefs to user.js
        user_js_filename = os.path.join(profile_dir, 'user.js')
        user_js_file = open(user_js_filename, 'w')
        for pref in prefs:
            user_js_file.write(self.PrefString(pref, prefs[pref], '\n'))

        user_js_file.close()

        if (self._remoteWebServer <> 'localhost'):
             self.ffprocess.addRemoteServerPref(profile_dir, self._remoteWebServer)

        # Add links to all the extensions.
        extension_dir = os.path.join(profile_dir, "extensions")
        if not os.path.exists(extension_dir):
            os.makedirs(extension_dir)
        for addon in extensions:
            self.install_addon(profile_dir, addon)

        #if (self._remoteWebServer <> 'localhost'):
        #    remote_dir = self.ffprocess.copyDirToDevice(profile_dir)
        #    profile_dir = remote_dir
        return temp_dir, profile_dir
        
    def InstallInBrowser(self, browser_path, dir_path):
        """
            Take the given directory and copies it to appropriate location in the given
            browser install
        """
        # add the provided directory to the given browser install
        fromfiles = glob.glob(os.path.join(dir_path, '*'))
        todir = os.path.join(os.path.dirname(browser_path), os.path.basename(os.path.normpath(dir_path)))
        for fromfile in fromfiles:
            self.ffprocess.copyFile(fromfile, todir)

    def InstallBundleInBrowser(self, browser_path, bundlename, bundle_path):
        """
        Take the given directory and unzip the bundle into
        distribution/bundles/bundlename.
        """
        destpath = os.path.join(os.path.dirname(browser_path),
                                'distribution', 'bundles', bundlename)
        if os.path.exists(destpath):
            shutil.rmtree(destpath)

        os.makedirs(destpath)
        zip_extractall(zipfile.ZipFile(bundle_path), destpath)

    def InitializeNewProfile(self, profile_dir, browser_config):
        """Runs browser with the new profile directory, to negate any performance
            hit that could occur as a result of starting up with a new profile.
            Also kills the "extra" browser that gets spawned the first time browser
            is run with a new profile.

        Args:
            browser_config: object containing all the browser_config options
            profile_dir: The full path to the profile directory to load
        """
        PROFILE_REGEX = re.compile('__metrics(.*)__metrics', re.DOTALL|re.MULTILINE)
        log = browser_config['browser_log']

        runner = self.ffprocess.GetBrowserRunner(browser_config["browser_path"],
                                                 browser_config["extra_args"],
                                                 profile_dir,
                                                 log,
                                                 browser_config["init_url"])

        runner.start()
        max_wait_time = 1200 # 20 minutes
        runner.wait(timeout = max_wait_time) # throws exception on timeout
        results_raw = self.ffprocess.GetBrowserLog(log)
        if not PROFILE_REGEX.search(results_raw):
            raise talosError("Expected output not found when initializing profile (got: %s)" % results_raw)

