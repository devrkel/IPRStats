# General imports
import tempfile
import platform
import shutil
import sys
import os

# Import for reading and writing the configuration file
import ConfigParser

# Used for generating a random session id
import string
from random import choice

class DBSettings:
    '''This class provides database connection details
       and type checking.
    '''
    
    def __init__(self, user, passwd, db, host=None, port=None):
        '''Initialize with the essential details, including
           host, user, passwd and db.  Make sure they are of
           the correct type.
        '''
        
        assert(type(user) is str)
        assert(type(passwd) is str)
        assert(type(db) is str)
        
        self.user = user
        self.passwd = passwd
        self.db = db
        
        if not host or type(host) is not str:
            self.host = 'localhost'
        else: self.host = host
        
        if not port or type(port) is not int:
            self.port = 3306 # default MySQL port
        else: self.port = port
    
    def gethost(self):
        '''Returns: connection host (str)
           Default: 'localhost'
        '''
        return self.host
    
    def getuser(self):
        '''Returns: connecting user (str)
        '''
        return self.user
    
    def getpasswd(self):
        '''Returns: user's password (str)
        '''
        return self.passwd
    
    def getport(self):
        '''Returns: connection port (int)
           Default: 3306
        '''
        return self.port
    
    def getdb(self):
        '''Returns: connection db (str)
        '''
        return self.db

class ChartSettings:
    '''This class provides chart settings, such as the
       maximum results, chart type, and chart generator.
    '''
    
    def __init__(self, max_results, chart_type, generator):
        '''Initialize the chart object with max results (int),
           type (pie or bar), and generator (google or pylab)
        '''
        
        assert(type(max_results) is int)
        assert(chart_type in ['pie', 'bar'])
        assert(generator in ['google','pylab'])
        
        self.max_results = max_results
        self.chart_type = chart_type
        self.generator = generator
        self.scale = 200
    
    def getmaxresults(self):
        '''Returns: maximum results to appear
           in the chart (int)
        '''
        return self.max_results
    
    def gettype(self):
        '''Returns: current chart type (str)
        '''
        return self.chart_type
    
    def getgenerator(self):
        '''Returns: current chart generator (str)
        '''
        return self.generator
    
    def getscale(self):
        '''Returns: the chart scale; currently unchangable
           at 200 (int)
        '''
        return self.scale

class Settings:
    '''Class to centralize all the general IPRStats settings
    '''
    
    def __init__(self, configpath=None, installed=False):
        '''Open the specified configuration path and initialize
           all the settings variables.
           
           Default: it opens '.iprstats/iprstats.cfg' or
           '$HOME/.iprstats/iprstats.cfg'
        '''
        self.__load_file_paths__(installed=installed)
        
        if not configpath:
            self.ConfigPath = os.path.join(self.getdatadir(), 'iprstats.cfg')
        else:
            self.ConfigPath = configpath
        
        self.__load_settings__()
    
    def __load_file_paths__(self, installed=False, export_dir=None):
        '''Loads the default paths that IPRStats will used based on
           whether it's installed (True) or running locally (False)
        '''
        
        if installed:
            self.homedir = os.path.expanduser("~")
        else:
            self.homedir = os.getcwd()
 
        self.datadir = os.path.join(self.homedir, '.iprstats')
        self.datadir = self.__get_real_folder__(self.datadir)
        
        self.sessiondir = None
        
        self.sessionsdir = os.path.join(self.datadir, 'sessions')
        self.sessionsdir = self.__get_real_folder__(self.sessionsdir)
        
        if export_dir and os.path.exists(export_dir):
            self.exportdir = export_dir
        else:
            self.exportdir = self.homedir
        
        if installed:
            if platform.system() == 'Windows':
                self.installdir = os.path.join(sys.prefix, 'Lib',
                                           'site-packages', 'iprstats')
            else:
                self.installdir = os.path.join(sys.prefix, 'share',
                                           'pyshared', 'iprstats')
        else:
            self.installdir = os.getcwd()

    def __get_real_folder__(self, path):
        '''Tries to create the given path if it doesn't exist
           and defaults to the temp directory otherwise.
           Returns: folder path (str)
        '''
        if not os.path.exists(path):
            try:
                os.mkdir(path)
            except:
                print "Could not create folder '" + path + \
                      "'; using '" + tempfile.gettempdir() + "'"
                path = tempfile.gettempdir()
        return path
    
    def __open_config_file__(self, config_path):
        '''Attempts to find the given config file.  If it can't, it
           attempts to copy it to the given location from a standard
           location.  If that fails, it raises an IOError.
           Returns: config file (ConfigParser)
        '''
        
        if not config_path:
            raise TypeError, "argument ConfigPath in __load_settings__() " + \
                             "cannot be None."
        
        config = ConfigParser.ConfigParser()
        
        if not os.path.exists(config_path):
            try:
                exConfig = os.path.join(self.installdir,
                                        'iprstats.cfg.example')
                shutil.copy(exConfig, config_path)
            except IOError:
                raise IOError, "No such configuration file: " + config_path
                sys.exit(2)
        
        configfile = open(config_path, 'r')
        config.readfp(configfile)
        configfile.close()
        
        return config
    
    def __load_settings__(self):
        '''Read the opened config file (self.config) into
           settings variables.
        '''
            
        self.config = self.__open_config_file__(self.ConfigPath)
        self.session = ''
        
        # List containing applications; ex - ['PIR', 'PFAM', ...]
        self.apps = self.config.get('general','apps')
        self.apps = self.apps.replace('\n',' ').split(', ')
        
        self.maxtableresults = self.config.getint('general',
                                                  'max_table_results')
        self.chart = ChartSettings(
                        self.config.getint('general', 'max_chart_results'),
                        self.config.get('general', 'chart_type'),
                        self.config.get('general', 'chart_gen'))
        
        self.sqlite = self.config.getboolean('local db', 'use_sqlite')
        self.localdb = self.__load_db_settings__('local db')
        
        self.golookup = self.config.getboolean('go db', 'go_lookup')
        self.godb = self.__load_db_settings__('go db')
    
    def __load_db_settings__(self, section):
        '''Load connections from a given section in the configuration.
           Returns: dbsettings (DBSettings)
        '''
        
        dbsettings = DBSettings(
                        db=self.config.get(section, 'db'),
                        host=self.config.get(section, 'host'),
                        user=self.config.get(section, 'user'),
                        passwd=self.config.get(section, 'passwd'),
                        port=self.config.getint(section, 'port'))
        return dbsettings

    def newsession(self, session_id=None):
        '''Create a new session with the provided session_id;
           creates a random session id if session_id is not provided
           Returns: the new session id (str)
        '''
        if session_id:
            self.session = session_id
        else:
            chars = string.letters + string.digits
            self.session = ''.join([choice(chars) for _ in xrange(8)])
        
        self.setsessiondir(self.session)
        
        return self.session

    def gethomedir(self):
        '''Returns: home directory (str)
           Default: current working directory or $HOME
        '''
        return self.homedir
    
    def getdatadir(self):
        '''Returns: data directory (str)
           Default: '.iprstats' or '$HOME/.iprstats'
        '''
        return self.datadir
    
    def getsessiondir(self):
        '''Returns: current session directory (str)
           Default: '.iprstats/sesssion/$SESSIONID' or
                    '$HOME/.iprstats/session/$SESSIONID'
        '''
        return self.sessiondir
    
    def getsessionsdir(self):
        '''Returns: sessions directory (str)
           Default: '.iprstats/session' or '$HOME/.iprstats/session'
        '''
        return self.sessionsdir
    
    def getexportdir(self):
        '''Returns: current export directory (str)
           Default: current working directory or $HOME
        '''
        return self.exportdir
    
    def getinstalldir(self):
        '''Returns: module install directory (str)
           Default: 'C:\PythonX.X\Lib\site-packages\iprstats' or
                    '/usr/share/pyshared/iprstats'
        '''
        return self.installdir
    
    def setexportdir(self, new_export_dir):
        '''Sets the new export directory from opening a dialog
        '''
        assert(os.path.exists(new_export_dir))
        self.exportdir = new_export_dir
        
    def setsessiondir(self, session_id):
        '''Sets the session directory variable to point to the
           correct session directory and creates the folder if
           necessary
        '''
        self.sessiondir = os.path.join(self.sessionsdir, session_id)
        if not os.path.exists(self.sessiondir):
            os.mkdir(self.sessiondir)
    
    def getconfigparser(self):
        '''Get the ConfigParser object.
           Returns: config (ConfigParser)
        '''
        return self.config
    
    def getsession(self):
        '''Get the current session id.
           Returns: session id (str)
        '''
        return self.session
    
    def getmaxtableresults(self):
        '''Get the user-specified maximum number of
           table results.
           Returns: max table results (int)
        '''
        return self.maxtableresults
    
    def getchartsettings(self):
        '''Returns: current chart settings (ChartSettings)
        '''
        return self.chart
    
    def getapps(self):
        '''Returns: list of supported apps (list of str)
        '''
        return self.apps
    
    def usesqlite(self):
        '''Returns: whether to use SQLite (bool)
        '''
        return self.sqlite
    
    def usegolookup(self):
        '''Returns: whether to use GO lookup (bool)
        '''
        return self.golookup
    
    def getlocaldb(self):
        '''Returns: local MySQL db connection details (DBSettings)
        '''
        return self.localdb
    
    def getgodb(self):
        '''Returns: Gene Ontology MySQL db connection details (DBSettings)
        '''
        return self.godb
    
    def setgolookup(self, value):
        '''Sets the GO lookup variable to the specified value
        '''
        assert(type(value) is bool)
        self.golookup = value
    
    def setconfigparser(self, NewConfigParser=None):
        '''Sets a new ConfigParser object and reloads the configuration
           data.  Reloads the current ConfigParser if no arguments
        '''
        if NewConfigParser:
            self.config = NewConfigParser
        ConfigFile = open(self.ConfigPath, 'w')
        self.config.write(ConfigFile)
        ConfigFile.close()
        self.__load_settings__()
        
        