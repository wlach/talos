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
#   Ben Hearsum    <bhearsum@wittydomain.com> (OS independence)
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

from ffprocess import FFProcess
import os
import shutil
import utils
import subprocess

try:
    import win32api
    import win32file
    import win32pdhutil
    import win32pdh
    import win32pipe
    import msvcrt
except:
    pass

class Win32Process(FFProcess):
    def __init__(self):
        pass

    def GenerateBrowserCommandLine(self, browser_path, extra_args, profile_dir, url):
        """Generates the command line for a process to run Browser

        Args:
            browser_path: String containing the path to the browser exe to use
            profile_dir: String containing the directory of the profile to run Browser in
            url: String containing url to start with.
        """

        profile_arg = ''
        if profile_dir:
            profile_dir = profile_dir.replace('\\', '\\\\\\')
            profile_arg = '-profile %s' % profile_dir

        cmd = '%s %s %s %s' % (browser_path,
                                extra_args,
                                profile_arg,
                                url)
        return cmd


    def TerminateProcess(self, pid):
        """Helper function to terminate a process, given the pid

        Args:
            pid: integer process id of the process to terminate.
        """
        ret = ''
        PROCESS_TERMINATE = 1
        handle = win32api.OpenProcess(PROCESS_TERMINATE, False, pid)
        win32api.TerminateProcess(handle, -1)
        win32api.CloseHandle(handle)
        ret = 'terminated with PROCESS_TERMINATE'
        return ret


    def ProcessesWithNames(self, *process_names):
        """Returns a list of processes running with the given name(s).
        Useful to check whether a Browser process is still running

        Args:
            process_names: String or strings containing process names, i.e. "firefox"

        Returns:
            An array with a list of processes in the list which are running
        """

        processes_with_names = []
        for process_name in process_names:
            try:
                # refresh list of processes
                win32pdh.EnumObjects(None, None, 0, 1)
                pids = win32pdhutil.FindPerformanceAttributesByName(process_name, counter="ID Process")
                if len(pids) > 0:
                    processes_with_names.append(process_name)
            except:
                # Might get an exception if there are no instances of the process running.
                continue
        return processes_with_names


    def TerminateAllProcesses(self, *process_names):
        """Helper function to terminate all processes with the given process name

        Args:
            process_name: String or strings containing the process name, i.e. "firefox"
        """
        result = ''
        for process_name in process_names:
            # Get all the process ids of running instances of this process, and terminate them.
            try:
                # refresh list of processes
                win32pdh.EnumObjects(None, None, 0, 1)
                pids = win32pdhutil.FindPerformanceAttributesByName(process_name, counter="ID Process")
                for pid in pids:
                    ret = self.TerminateProcess(pid)
                    if result and ret:
                        result = result + ', '
                    if ret:
                        result = result + process_name + '(' + str(pid) + '): ' + ret 
            except:
                # Might get an exception if there are no instances of the process running.
                continue
        return result


    def NonBlockingReadProcessOutput(self, handle):
        """Does a non-blocking read from the output of the process
            with the given handle.

        Args:
            handle: The process handle returned from os.popen()

        Returns:
            A tuple (bytes, output) containing the number of output
            bytes read, and the actual output.
        """

        output = ""

        try:
            osfhandle = msvcrt.get_osfhandle(handle.fileno())
            (read, num_avail, num_message) = win32pipe.PeekNamedPipe(osfhandle, 0)
            if num_avail > 0:
                (error_code, output) = win32file.ReadFile(osfhandle, num_avail, None)

            return (num_avail, output)
        except:
            return (0, output)
            
    def MakeDirectoryContentsWritable(self, dirname):
        """Recursively makes all the contents of a directory writable.
            Uses os.chmod(filename, 0777), which works on Windows.

        Args:
            dirname: Name of the directory to make contents writable.
        """

        try:
            for (root, dirs, files) in os.walk(dirname):
                os.chmod(root, 0777)
                for filename in files:
                    try:
                        os.chmod(os.path.join(root, filename), 0777)
                    except OSError, (errno, strerror):
                        print 'WARNING: failed to os.chmod(%s): %s : %s' % (os.path.join(root, filename), errno, strerror)
        except OSError, (errno, strerror):
            print 'WARNING: failed to MakeDirectoryContentsWritable: %s : %s' % (errno, strerror)
            
    def getFile(self, handle, localFile = ""):
        fileData = ''
        if os.path.isfile(handle):
            results_file = open(handle, "r")
            fileData = results_file.read()
            results_file.close()
        return fileData

    def copyFile(self, fromfile, toDir):
        if not os.path.isfile(os.path.join(toDir, os.path.basename(fromfile))):
            shutil.copy(fromfile, toDir)
            utils.debug("installed " + fromfile)
        else:
            utils.debug("WARNING: file already installed (" + fromfile + ")")

    def removeDirectory(self, dir):
        self.MakeDirectoryContentsWritable(dir)
        shutil.rmtree(dir)

    def launchProcess(self, cmd, outputFile = "process.txt", timeout = -1):
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True, shell=True, env=os.environ)
        handle = process.stdout

        timed_out = True
        if (timeout > 0):
            total_time = 0
            while total_time < 600: #10 minutes
                time.sleep(1)
                if (not self.poll(process)):
                    timed_out = False
                    break
                total_time += 1

        if (timed_out == True):
            return None

        return handle

    def poll(self, process):
        return process.poll()

