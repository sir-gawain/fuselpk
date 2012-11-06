import os
from fuselpk import cfg

 
class unit_test_cfg(object):

    def __init__(self):
        self._base_path_ = os.path.dirname(__file__)


    def test_configuration_file_not_found(self):

        """unit cfg : raise FileNotFound"""

        exception = False
        try:
            cfg.lpkconfig( os.path.join(self._base_path_, 'unexisting_configuration_file'), {} )
        except cfg.ConfigurationFileNotFound:
            exception = True
        assert exception


    def test_section_not_found(self):

        """unit cfg : raise SectionNotFound"""

        exception = False
        try:
            cfg.lpkconfig( os.path.join(self._base_path_, 'configurationfiles', 'section_not_found.cfg'), \
                           {'default' : []} ).values()
        except cfg.ConfigurationSectionNotFound:
            exception = True
        assert exception
        

    def test_section_not_used(self):

        """unit cfg : raise SectionNotUsed"""

        exception = False
        try:
            cfg.lpkconfig( os.path.join(self._base_path_, 'configurationfiles', 'section_not_used.cfg'), \
                           {'default' : []} ).values()
        except cfg.ConfigurationSectionNotUsed:
            exception = True
        assert exception


    def test_option_not_used(self):

        """unit cfg : raise OptionNotUsed"""

        exception = False
        try:
            cfg.lpkconfig( os.path.join(self._base_path_, 'configurationfiles', 'option_not_used.cfg'), \
                           {'default' : []} ).values()
        except cfg.ConfigurationOptionNotUsed:
            exception = True
        assert exception


    def test_section_type_mismatch(self):

        """unit cfg : raise TypeMismatch"""

        exception = False
        schema = { 'default' : {
                                'integer' : {
                                             'type' : int,
                                             'default' : 5,
                                             }
                                }}
        try:
            
            cfg.lpkconfig( os.path.join(self._base_path_, 'configurationfiles', 'option_type_mismatch.cfg'), \
                           schema ).values()
        except cfg.ConfigurationOptionTypeMismatch:
            exception = True
        assert exception


    def test_zzlasttest_ok(self):

        """unit cfg : ok"""

        schema = { 'default' : {
                                'integer' : {
                                             'type' : int,
                                             'default' : 5,
                                             },
                                'unicode' : {
                                             'type' : unicode,
                                             'default' : 5,
                                             },
                                'default_integer' : {
                                             'type' : int,
                                             'default' : 5,
                                             },
                                'default_unicode' : {
                                             'type' : unicode,
                                             'default' : 5,
                                             },
                                }}
        
        v = cfg.lpkconfig( os.path.join(self._base_path_, 'configurationfiles', 'option_ok.cfg'), \
                           schema ).values()
        assert v == { 'default_integer' : 5,
                      'default_unicode' : u'5',
                      'integer' : 10,
                      'unicode' : u'Hello world!' }
