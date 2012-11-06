# -*- coding: utf-8 -*-

# FuseLPK -- FUSE filesystem for LDAP Public Key Copyright
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import fuse
fuse.fuse_python_api = (0, 2)

import ldap
import errno

from time import mktime, gmtime
from fuse import Fuse
from os.path import sep as fssep
from stat import S_IFDIR, S_IFREG
from StringIO import StringIO

from cfg import lpkconfig, cfg_schema


class NotFound(Exception):
    """Used for response to crazy query"""
    

def ifDeprecatedCache(reloadCacheFunc):

    """Decorator only used by fs, reload cache if necessary"""

    def wrapper(func):
        def wrapped(self, *arg, **kw):
            if mktime(gmtime()) - float(self._cfg_['timeout']) \
               > self._lastCacheRefresh_:
                 reloadCacheFunc(self)
            return func(self, *arg, **kw)
        return wrapped
    return wrapper


class pkfile(object):

    """file data's operation, this is read only"""
    

    def __init__(self, path, content):

        """File content"""        
        self._content_ = StringIO(content)
        self._len_ = len(content)
        self._path_ = path

        # Needed by fuse, else a traceback appear
        # (without blocking file operation)
        self.keep_cache = False
        self.direct_io = False
        

    def read(self, length, offset):

        """Read file data"""

        self._content_.seek(offset)
        return self._content_.read(length)
    

    def size(self):

        """Size of content"""

        return self._len_


    def __repr__(self):

	"""String representing a pkfile"""

        return "<File %s>" % self._path_


class fs(Fuse):

    """The file system, FUSE interfaced"""

    def __init__(self, default_config_file, *args, **kwargs):
        
        """initialize filesystem"""
        
        Fuse.__init__(self, *args, **kwargs)
        self.parser.add_option(mountopt='config', metavar='FILE',
                               default=default_config_file,
                               help="Configuration place [default: %default]")
        self._users_ = {}
        self._lastCacheRefresh_ = -1 # first time cache is reloaded
        self._default_config_file_ = default_config_file


    def main(self, *a, **kwargs):

        """Start and lose control"""
        
        Fuse.main(self, *a, **kwargs)


    def fsinit(self):

        """required by fuse, process configuration"""

        option_config_file = getattr(self, 'config', None)
        option_config_file = option_config_file if option_config_file \
                                                else self._default_config_file_

        self._cfg_ = lpkconfig(option_config_file, cfg_schema).values()


    def _ldapConnect_(self):
        """for ssl use, pass a ldaps:// url form"""
        try:
            con = \
                ldap.initialize( self._cfg_['url'] ) 

            auth = ldap.AUTH_SASL \
                if self._cfg_['auth'] == "sasl" \
                else ldap.AUTH_SIMPLE

            con.bind_s(self._cfg_['rootdn'],
                     self._cfg_['rootpw'],
                     auth)

        except ldap.INVALID_CREDENTIALS:
            # todo : make better and log it correctly
            print "Manager DN or password is incorrect (INVALID CREDENTIALS)."
            con = None

        except ldap.LDAPError, e:
            # todo : make better and log it correctly
            raise ldap.LDAPError, e
            con = None
        return con
    

    def _query_all_users_(self, con):
        """Retrieve all users"""
        
        login_attr = self._cfg_["login_attr"]
        uid_attr = self._cfg_['uid_attr']
        gid_attr = self._cfg_['gid_attr']
        pkey_attr = self._cfg_['pkey_attr']
        
        users = con.search_s( self._cfg_['basedn'],
                              ldap.SCOPE_SUBTREE,
                              self._cfg_['query'],
                              ( login_attr, uid_attr, gid_attr, pkey_attr)
                            )

        # Prepare users dict (login is the key, not dn)
        results = {}        
        for user in users:
            dn = user[0]
            attrs = user[1]

            if len(attrs) != 4:
                # incomplete data set
                continue

            login = attrs[login_attr][0]
            content = pkfile('/%s/authorized_keys' % login,'%s\n' % ('\n'.join(attrs[pkey_attr]))) \
                if pkey_attr in attrs else File('')
            results[login] = \
                { 'dn' : dn,                               
                  'uid' : int(attrs[uid_attr][0]),
                  'gid' : int(attrs[gid_attr][0]),
                  'pkey' : content,
                } 
        return results


    def _ldapDisconnect_(self, con):
        """Disconnect ldap"""
        con.unbind()
        

    def _reloadKeys_(self):
        """Reload users and keys from ldap"""
        con = self._ldapConnect_()
        if con:
            self._users_ = self._query_all_users_(con)
            self._ldapDisconnect_(con)
            self._lastCacheRefresh_ = mktime(gmtime())
        else:
            self._users_ = []
                                                            

    def _parsePath_(self, path):
        """Valid and parse path"""
        root = False
        user = None
        keyfile = False

        # Root directory (world readable
        if path == fssep:
            root = True
        else:
            # Stats: user defined
            path_len = len(path.split(fssep))
            
            if path_len not in [2,3]:
                raise NotFound

            # Retrieve user
            login = path.split(fssep)[1]
            if not login in self._users_:
                raise NotFound

            user = self._users_[login]
       
            # User file
            if path_len == 3:
                if not path.endswith('%sauthorized_keys' % fssep):
                    raise NotFound
                keyfile = True
                
        return root, user, keyfile
    


    @ifDeprecatedCache(_reloadKeys_)
    def readdir(self, path, offset):
        """list directory or file"""
        # current and parent directory
        # are already present

        # todo : user parsepath
        if path == fssep:
            # users directory
            
            for user in self._users_:
                yield fuse.Direntry(user)

        elif len(path.split(fssep)) == 2:
            # authorized_keys file
            yield fuse.Direntry('authorized_keys')


    @ifDeprecatedCache(_reloadKeys_)
    def getattr(self, path):
        """Return attributes of file or directory"""

        # nlink value : number of physical link
        #
        # directory :
        # the directory itself, the '.' and the '..' reference, 3
        # file :
        # the file itself only : 1
        
        st = fuse.Stat()

        try:
            root, user, keyfile = self._parsePath_(path)
        except NotFound:
            return -errno.ENOENT
        
        if root:
            # Root directory (world readable)
            st.st_mode = S_IFDIR | 0755
            st.st_uid = 0
            st.st_gid = 0
            st.st_nlink = 3
            return st
        else:
            # Stats: UID and GID for file and directory
            st.st_uid = user['uid']
            st.st_gid = user['gid']
            
            if keyfile:
                # User key file
                st.st_mode = S_IFREG | 0700
                st.st_size = user['pkey'].size()
                st.st_nlink = 1
            else:
                # User directory
                st.st_mode = S_IFDIR | 0700
                st.st_nlink = 3
            
        return st

    @ifDeprecatedCache(_reloadKeys_)
    def open(self, path, flags):
        """Open a file"""
        root, user, keyfile = self._parsePath_(path) 
        if (not user) or (not keyfile):
            return -errno.ENOENT
        return user['pkey']
        
    def read(self, path, length, offset, fileobj):
        """Read a file"""
        return fileobj.read(length, offset)
