from os import environ
from os.path import sep as fssep
from os.path import join, dirname
from time import mktime, gmtime
from stat import S_IFDIR, S_IFREG, S_ISDIR, S_ISREG

from fuselpk import fs
from base import configurationfiles

class test_unit_ifDeprecatedCache():

    class cacheclient:

        def __init__(self):
            self._lastCacheRefresh_ = -1
        
        def refresh(self):
            """reload next value"""
            self._value_ = self._refreshed_value_
            self._lastCacheRefresh_ = mktime(gmtime())
            
        def newvalue(self,value):
            self._refreshed_value_ = value
        
        @fs.ifDeprecatedCache(refresh)
        def value(self):
            return self._value_

    
    def test_unit_ifDeprecatedCache(self):

        """unit fs : decorator 'ifDeprecatedCache'"""
        
        cc = self.cacheclient()
        cc._cfg_ = {}
        cc._cfg_['timeout'] = -2
        cc._lastCacheRefresh_ = -1
        
        cc.newvalue("IT'S OK")
        assert cc.value() == "IT'S OK"
        
    
        # Set a null cache and get always the last value
        cc.newvalue("SO IT'S CHANGED NOW")
        assert cc.value() == "SO IT'S CHANGED NOW"
        
        # Another one
        cc.newvalue("SO IT'S CHANGED NOW THE RETURN")
        assert cc.value() == "SO IT'S CHANGED NOW THE RETURN"
    
        # Another one
        cc.newvalue("END, TEST CACHE NOW")
        assert cc.value() == "END, TEST CACHE NOW"
    
        # Set cache to n secondes
        cc._cfg_['timeout'] = 10
        cc._lastCacheRefresh_ = -1
    
        # Load the cache
        cc.newvalue("Cached Value")
        assert cc.value() == "Cached Value"
        
        # Access cached value
        cc.newvalue("Refreshed Value")

        # After 5 seconds cached is returned    
        cc._lastCacheRefresh_ -= 5
        assert cc.value() == "Cached Value"
        
        # Access 11 seconds refreshed value
        cc._lastCacheRefresh_ -= 6
        assert cc.value() == "Refreshed Value"




class test_unit_file():

    def test_unit_file(self):

        """unit fs : object 'pkfile'"""

        f = fs.pkfile("/onefile", "testing string")
        assert f.read(4096,0) == "testing string"
        assert f.read(3,7) == " st"
        assert f.size() == 14



    
class test_unit_filesystem(object):
    """unit filesystem"""

    
    def setup(self):

        """Set up fs"""

        self.fs = fs.fs( configurationfiles )
        self.fs.fsinit()
        self.attendees = ['correctuser1', 'correctuser2']
    

    def test_connection(self):

        """unit fs : object 'fs' '_ldapConnect_ _ldapDisconnect_'"""

        # Connection
        con = self.fs._ldapConnect_()
        assert con
    
        # Disconnection
        self.fs._ldapDisconnect_(con)


    def test_all_users_query(self):
        
        """unit fs : object 'fs' '_query_all_users_'"""
        
        con = self.fs._ldapConnect_()
        assert self.fs._query_all_users_(con).keys() == self.attendees
        self.fs._ldapDisconnect_( con )        
    

    def test_cache(self):
        
        """unit fs : object 'fs' '_reloadKeys_'"""
        
        con = self.fs._ldapConnect_()
        assert self.fs._users_ == {}
        self.fs._reloadKeys_()
        assert self.fs._users_.keys() == self.attendees
        self.fs._ldapDisconnect_(con)        
    

    def test_parsepath(self):
        
        """unit fs : object 'fs' '_parsePath_'"""
        
        con = self.fs._ldapConnect_()
        self.fs._reloadKeys_()
        # Root
        assert self.fs._parsePath_("/") == (True, None, False) 

        for login in self.attendees:

            root, file, is_key_file = self.fs._parsePath_( "/%s" % login) 
            assert root == False    
            assert is_key_file == False

            root, file, is_key_file = self.fs._parsePath_( "/%s/authorized_keys" % login) 
            assert root == False
            assert is_key_file == True
          
    
        self.fs._ldapDisconnect_(con)
    


    def test_unit_filesystem_fuseapi(self):

        """unit fs : object 'fs' fuse api 'readdir stat open read'"""
    
        # root list
        directories = [f.name for f in self.fs.readdir('/',0)]
        assert  directories == ['correctuser1', 'correctuser2']  
        
    
        for login in directories:
            numericid = {"correctuser1":10000, "correctuser2":10001}[login]
            
    
            # directory stats : getattr
            stats = self.fs.getattr(fssep + login)
            assert stats.st_uid == numericid
            assert stats.st_gid == numericid
            assert stats.st_mode == S_IFDIR | 0700
    
            
            # directory : readdir
            files = [f.name for f in self.fs.readdir(fssep + login,0)] 
            assert files == ['authorized_keys']
            filepath = fssep + login + fssep + files[0]
    
            
            # file stats : getattr
            stats = self.fs.getattr(filepath)
            assert stats.st_uid == numericid
            assert stats.st_gid == numericid
            assert stats.st_mode == S_IFREG | 0700
    
            
            # file content : open and read
            f = self.fs.open(filepath, 'r')
            assert self.fs.read(filepath,4096,0,f) == "%spublickey\n" % login
