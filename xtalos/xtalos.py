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
# The Original Code is mozilla.org code.
#
# The Initial Developer of the Original Code is
# the Mozilla Foundation.
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Joel Maher <joel.maher@gmail.com>
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

import os
import optparse
import sys

DEBUG_CRITICAL =0
DEBUG_ERROR =   1
DEBUG_WARNING = 2
DEBUG_INFO =    3
DEBUG_VERBOSE = 4

class XtalosOptions(optparse.OptionParser):
  def __init__(self, **kwargs):
    optparse.OptionParser.__init__(self, **kwargs)
    defaults = {}

    self.add_option("-p", "--process",
                    action = "store", dest = "processName",
                    help = "name of the process we launch, defaults to 'firefox.exe'")
    defaults["processName"] = "firefox.exe"

    self.add_option("-x", "--xperf",
                    action = "store", dest = "xperf_tool",
                    help = "location of xperf tool, defaults to 'xperf.exe'")
    defaults["xperf_tool"] = "xperf.exe"

    self.add_option("-e", "--etl_filename",
                    action = "store", dest = "etl_filename",
                    help = "Name of the .etl file to work with. Defaults to 'output.etl'")
    defaults["etl_filename"] = "output.etl"

    self.add_option("-d", "--debug",
                    type="int", dest = "debug_level",
                    help = "debug level for output from tool (0-5, 5 being everything), defaults to 1")
    defaults["debug_level"] = 1

    self.add_option("-o", "--output-file",
                    action="store", dest = "outputFile",
                    help = "Filename to write all output to, default is stdout")
    defaults["outputFile"] = None

    self.set_defaults(**defaults)

    usage = ""
    self.set_usage(usage)

  def verifyOptions(self, options):
    options.xperf_tool = os.path.abspath(options.xperf_tool)
    if (os.path.exists(options.xperf_tool) == False):
      print "ERROR: unable to verify '%s' exists" % (options.xperf_tool)
      return None

    return options

