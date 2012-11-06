import sys

from cfg import default_config_file, \
                ConfigurationFileNotFound, \
                ConfigurationSectionNotFound, \
                ConfigurationSectionNotUsed, \
                ConfigurationOptionNotUsed, \
                ConfigurationOptionTypeMismatch
from fs import fs

try:
    import fuse
    from fuse import Fuse
except:
    print 'The Python bindings for fuse do not seem to be installed.'
    print 'Please install fuse-python.'
    sys.exit(1)

def start():
    """Run the file system"""

    # show help by default
    if len(sys.argv) == 1:
        sys.argv.append('--help')

    # prepare server    
    usage = 'usage: %s' % (Fuse.fusage)
    server = fs(default_config_file, version=fuse.__version__, usage=usage)

    # Don't work with thread
    server.parse(values=server, errex=1)
    server.multithreaded = False
    
    # run FS server
    server.main()
