import sys
from os import listdir, stat, environ
from os.path import join, dirname
from os.path import sep as fssep
from time import sleep
from stat import S_IFDIR, S_IFREG, S_ISDIR, S_ISREG

from base import configurationfiles

class test_func_filesystem(object):

    """func filesystem"""
    

    def setup(self):

        """func fs : Mount filesystem"""

        self._paths_ = { \
                           '.' : ['correctuser1', 'correctuser2'],
                           'correctuser1' : [ 'authorized_keys' ],
                           'correctuser2' : [ 'authorized_keys' ],
                       }

        # paths
        self._fs_process_ = None
        basepath = dirname(__file__)        
        self._mountpoint_  = join( basepath,
                                   "mountpoint")
        self._configuration_file_ = configurationfiles
        
        # Call entrypoint
        self.teardown() # Unmount before mount, we must an unmounted fs at this point
        from subprocess import Popen
 
        cmdline =   [ sys.executable,
                      "-m",
                      "fuselpk.start", 
                      self._mountpoint_, 
                      "-o",
                      "config=%s" %self._configuration_file_ ,
                      "-o",
                      "nonempty"]
        
        # Backup and set PYTHONPATH
        bpython_path = 'PYTHONPATH' in environ and environ['PYTHONPATH'] or None
        environ['PYTHONPATH'] = ":".join(sys.path)

        # Call the main module
        self._fs_process_ = Popen( cmdline )
        self._fs_process_.wait()
        sleep(0.1) # for freebsd
        # Restore PYTHONPATH
        if bpython_path:
            environ['PYTHONPATH'] = bpython_path
        else:
            del environ['PYTHONPATH']

    def teardown(self):

        """func fs : Unmount filesystem"""

        from os import system
        from sys import platform
        
        if platform.startswith("freebsd"):
            system("umount %s > /dev/null 2> /dev/null" % self._mountpoint_)
        else:
            system("fusermount -z -u %s > /dev/null 2> /dev/null" % self._mountpoint_) 
        if self._fs_process_:
            self._fs_process_.wait()    


    def test_listdir(self):

        """func fs : python 'listdir'"""

        paths = self._paths_

        for path in paths:
            items = listdir( join(self._mountpoint_, path) + fssep)
            items.sort()
            paths[path].sort()
            assert items == paths[path]
        
    
    def test_stat(self):
        
        """func fs : python 'stat'"""

        paths = self._paths_

        uids = { 'correctuser1' : 10000, 'correctuser2' : 10001 }

        for path in paths:           
            attrs = stat( join(self._mountpoint_, path) )
            assert S_ISDIR(attrs.st_mode)
            uid = uids[path] if path in uids else None
            if path != ".":
                assert attrs.st_uid == uid
                assert attrs.st_gid == uid
                assert attrs.st_nlink == 3
                attrs = stat( join(self._mountpoint_, path, 'authorized_keys') )
                assert S_ISREG(attrs.st_mode)
                assert attrs.st_uid == uid
                assert attrs.st_gid == uid
                assert attrs.st_nlink == 1
       

    def test_readfile(self):
        
        """func fs : python 'open read'"""
        
        paths = self._paths_
        for path in paths:
            if path==".":
                continue
            f = open( join(self._mountpoint_, path, 'authorized_keys') )
            assert f.read() == '%spublickey\n' % path

