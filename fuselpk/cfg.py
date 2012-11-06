import os
from ConfigParser import ConfigParser

default_config_file = '/etc/ssh/fuselpk.cfg'

# This is the "schema" of configuration
cfg_schema = {
    'default' : 
        {
              'url' : 
                  { 
                      'type' : unicode,
                      'totype' : unicode,
                      'default' : 'ldap://localhost:389',
                  }, 
              'rootdn' :
                  {
                      'type' : unicode,
                      'totype' : unicode,                      
                      'default' : 'cn=admin,dc=localhost',
                  },
              'rootpw' : 
                  {
                      'type' : unicode,                      
                      'default' : 'admin',
                  },
              'auth' :
                  {
                      'type' : unicode,                      
                      'choices' : ['simple'],
                      'default' : 'simple',
                  },
              'basedn' :
                  {
                      'type' : unicode,
                      'default' : 'dc=localhost',
                  },                      
              'query' : 
                  {
                      'type' : unicode,
                      'default' : 'objectClass=ldapPublicKey',
                  },
              'scope' :
                  {
                      'type' : unicode,
                      'default' : 'subtree',
                  },
              'login_attr' : 
                  {
                      'type' : str,
                      'default' : 'cn',
                  },
              'uid_attr' : 
                  {
                      'type' : str,
                      'default' : 'uidNumber',
                  },
              'gid_attr' :
                  {
                      'type' : str,
                      'default' : 'gidNumber',
                  },
              'pkey_attr' :
                  {
                      'type' : str,
                      'default' : 'sshPublicKey',
                  },
              'timeout' :
                  {
                      'type' : int,
                      'default' : 60,
                 },
             }
        }


class ConfigurationFileNotFound(Exception):
    """Exception marker"""
    exitvalue = 1

class ConfigurationSectionNotFound(Exception):
    """Exception marker"""
    exitvalue = 2
    
class ConfigurationSectionNotUsed(Exception):
    """Exception marker"""
    exitvalue = 3

class ConfigurationOptionNotUsed(Exception):
    """Exception marker"""
    exitvalue = 4

class ConfigurationOptionTypeMismatch(Exception):
    """Exception marker"""
    exitvalue = 5


class lpkconfig(ConfigParser):
    
    def __init__(self, file, schema):
        if not os.path.isfile(file):
            raise ConfigurationFileNotFound, \
                'The configuration file (\'%s\') is not readable' % file
        defaults = [] # default values
        self._schema_ = schema
        self._configuration_file_ = file
        
    def values(self):
        # get schemas defaults
        schema = self._schema_
        values = self._default_values_()
        
        # let's parse configuration file
        cp = ConfigParser()
        cp.read(self._configuration_file_)
        
        # Sections verifications
        unused_sections = [section for section in cp.sections() \
                           if section not in schema.keys()]
        if unused_sections != []:
            raise ConfigurationSectionNotUsed, \
                  "Section(s) not used in configuration file : %s" % \
                  ' '.join(unused_sections)
        
        not_found_sections = [section for section in schema.keys() \
                              if section not in cp.sections()]
        if not_found_sections != []:
            raise ConfigurationSectionNotFound, \
                  "Section(s) not found in configuration file : %s" % \
                  ' '.join(not_found_sections)

        # Options verifications and merging
        for section in schema:
            not_used_options = [option for option in cp.options(section) \
                                if option not in schema[section]]
            if not_used_options != []:
                raise ConfigurationOptionNotUsed, \
                    'Option(s) not used in section \'%s\' : %s' % \
                    (section, ' '.join(not_used_options))
            
            for option in cp.options(section):
                t = schema[section][option]['type']
                try:
                    v = t( cp.get(section,option) )
                except ValueError:
                    raise ConfigurationOptionTypeMismatch, \
                          'Option \'%s\' must be \'%s\'' % (option, t.__name__)
                values[option] = v
        return values

    def _default_values_(self):
        values = {}
        for section in self._schema_:
            for param in self._schema_[section]:
                t = self._schema_[section][param]['type']
                values[param] = t( self._schema_[section][param]['default'] )
        return values

