#!/usr/bin/python
import os
import sqlite3

try:
    import MySQLdb
    from _mysql_exceptions import OperationalError
except ImportError:
    pass

class Cache:
    '''Object to temporarily store aggregate information retrieved
       by complex, time-intensive queries. This is the top-level class
       that stores all information in memory.  Subclasses of this
       class should attempt to preserve memory by caching to disk.
       
       Methods you are required to override when making a subclass are:
       __open_cache__(self)
       __create_count_group__(self, app)
       __insert_count_record__(self, app, name, count)
       __create_match_group__(self, app)
       __insert_match_record__(self, app, dbid, name, count, goid, goname)
       get_one_row(self, app, rownum)
       get_counts(self, app)
       
       It is also recommended to override the following methods:
       __commit_records__(self)
       __close_writing__(self)
    '''
    
    def __init__(self, settings):
        '''Initialize the cache object with a settings object in order
           for it to get a database connection and the working session
           directory.
        '''
        self.settings = settings
        self.filename = os.path.join(self.settings.getsessiondir(), 'results')
        self.db_conn = self.__get_db_conn__()
        self.db_cursor = self.db_conn.cursor()
        self.go_conn, self.go_cursor = self.__get_go_db_conn__()
        
        # Hash of database links
        self.linkdb = {
            'PFAM'       :'http://pfam.janelia.org/family?acc=%s',
            'PIR'        :'http://pir.georgetown.edu/cgi-bin/ipcSF?id=%s',
            'HAMAP'      :'http://www.expasy.org/unirule/%s',
            'PANTHER'    :'http://www.pantherdb.org/panther/family.do?' + 
                          'clsAccession=%s',
            'PRINTS'     :'http://www.bioinf.manchester.ac.uk/cgi-bin/' +
                          'dbbrowser/PRINTS/DoPRINTS.pl?cmd_a=Display&' +
                          'qua_a=none&fun_a=Text&qst_a=%s',
            'PRODOM'     :'http://prodom.prabi.fr/prodom/current/cgi-b' + 
                          'in/request.pl?question=DBEN&query=%s',
            'PRO'        :'http://expasy.org/cgi-bin/prosite-search-ac?%s',
            'SMART'      :'http://smart.embl-heidelberg.de/smart/do_ann' + 
                          'otation.pl?BLAST=DUMMY&DOMAIN=%s',
            'SUPERFAMILY':'http://supfam.cs.bris.ac.uk/SUPERFAMILY/cgi-' + 
                          'bin/scop.cgi?ipid=%s',
            'TIGRFAMs'   :'http://cmr.jcvi.org/cgi-bin/CMR/HmmReport.cgi' + 
                          '?hmm_acc=%s',
            'GENE3D'     :'http://www.cathdb.info/gene3d/%s',
            'GO'         :'http://www.ebi.ac.uk/QuickGO/GTerm?id=%s#ancchart'}
        
        if not os.path.exists(self.filename):
            self.__populate_cache__()
        else:
            self.__open_cache__()
    
    def __get_db_conn__(self):
        '''Attempt to get a database connection (either MySQL or SQLite
           based on settings) and return the connection.  Defaults to
           SQLite if it cannot get a MySQL connection.
        '''
        dbs=self.settings.getlocaldb()
        
        if not self.settings.usesqlite():
            try:
                conn = self.__get_mysql_conn__(dbs)
                default2sqlite = False
                
            except OperationalError:
                default2sqlite = True
                print "cannot connect to " + dbs.gethost() + \
                      " using user " + dbs.getuser() + \
                      ". Defaulting to SQLite."
                
        if self.settings.usesqlite() or default2sqlite:
            sqldb = os.path.join(self.settings.getsessiondir(), dbs.getdb())
            conn = sqlite3.connect(sqldb)
        return conn
    
    def __get_go_db_conn__(self):
        '''Retrieve a connection (conn, cursor) to the gene ontology terms
           database using connection details specified in the settings if
           the settings if GO lookup is set as True.  Returns (None, None)
           otherwise.
        '''
        if self.settings.usegolookup():
            dbs=self.settings.getgodb()
            try:
                db_conn = self.__get_mysql_conn__(dbs)
                db_cursor = db_conn.cursor()
            except:
                print 'Cannot connect to GO DB... disabling GO lookup'
                self.settings.setgolookup(False)
                db_conn = None
                db_cursor = None
            return db_conn, db_cursor
        return None, None
        
    def __get_mysql_conn__(self, dbsettings):
        '''Generic class for retrieving a MySQL connection object
           given a DBSettings object.
        '''
        conn = MySQLdb.connect(host=dbsettings.gethost(),
                               user=dbsettings.getuser(),
                               passwd=dbsettings.getpasswd(),
                               port=dbsettings.getport(),
                               db=dbsettings.getdb())
        return conn
    
    def __populate_cache__(self):
        '''Main method for executing queries against the IPRStats
           database and storing them in memory or on disk.
        '''
        self.__open_cache__()
        
        for app in self.settings.apps:
            self.__count_query__(app)
            self.__create_count_group__(app)
            for name, count in self.db_cursor:
                self.__insert_count_record__(app, name, count)
            self.__commit_records__()
                
            self.__match_query__(app)
            self.__create_match_group__(app)
            for name, dbid, goid, count in self.db_cursor:
                if self.settings.usegolookup():
                    goname = self.__go_name__(goid)
                else: goname = None
                self.__insert_match_record__(app, dbid, name, count, goid, goname)
                
            self.__commit_records__()
        
        self.__close_writing__()
        self.db_cursor.close()
        if self.go_cursor:
            self.go_cursor.close()
    
    def __open_cache__(self):
        '''Method for creating the underlying data structure
           for storing query results.  Subclasses must override
           this method to open handles to disk-based structures
           or create memory maps.
        '''
        self.table = {}
        self.count = {}
    
    def __count_query__(self, app):
        '''Method for executing the query used to retrieve
           information for making charts.
        '''
        self.db_cursor.execute("""
            select   name, count(1) as count
            from     `%(session)s_iprmatch`
            where    db_name = '%(db)s'
            group by id
            order by count desc, name asc""" %
            ({'session':self.settings.session, 'db':app}))
    
    def __create_count_group__(self, app):
        '''Method used for creating a group or section in
           the underlying data structure for a particular
           app to store chart data.  Subclasses of Cache
           must override this method to make a group in the
           disk-based structure.
        '''
        self.count[app] = []
    
    def __insert_count_record__(self, app, name, count):
        '''Method for inserting a chart data record into
           the underlying cache data structure.  Subclasses
           must override this method.
        '''
        self.count[app].append((count, name))
        
    def __match_query__(self, app):
        '''Method for executing the query that retrieves table
           data from the IPRStats database.
        '''
        self.db_cursor.execute("""
            select   A.name, B.match_id, C.class_id, A.count
            from     ( select   name, pim_id, count(1) as count
                       from     `%(session)s_iprmatch`
                       where    db_name = '%(db)s'
                       group by id
                       order by count desc, id asc, name asc
                     ) as A
                     left outer join `%(session)s_protein_interpro_match` 
                       as B on A.pim_id = B.pim_id
                     left outer join `%(session)s_protein_classification`
                       as C on B.protein_id = C.protein_id
            group by B.match_id, C.class_id
            order by A.count desc, A.name asc;""" %
            ({'session':self.settings.session, 'db':app}))
    
    def __create_match_group__(self, app):
        '''Method used for creating a group or section in
           the underlying data structure for a particular
           app to store table data.  Subclasses of Cache
           must override this method to make a group in the
           disk-based structure.
        '''
        self.table[app] = []
    
    def __insert_match_record__(self, app, dbid, name, count, goid, goname):
        '''Method for inserting a table data record into
           the underlying cache data structure.  Subclasses
           must override this method.
        '''
        self.table[app].append((name, count, goid, dbid, goname))
        
    def __commit_records__(self):
        '''Method for committing or flushing records to disk
           that have been retrieved so far.
        '''
        pass
    
    def __close_writing__(self):
        '''Method for closing the underlying data structure
           for writing and opening it for reading.
        '''
        pass
    
    def __match_length__(self, app):
        return len(self.table[app])
    
    def __count_length__(self, app):
        return len(self.count[app])
    
    def get_match_length(self, app):
        '''Returns the visible number of rows in the stored
           table data, limited by the "max table results"
           setting or the number of available table rows.
        '''
        matchlen = self.__match_length__(app)
        maxtablelen = self.settings.getmaxtableresults()
        if maxtablelen < 0:
            return matchlen
        return min(matchlen, maxtablelen)

    def get_count_length(self, app):
        '''Returns the number of results to be displayed
           in a graph, limited either by the "max chart
           results" setting or the number of available results.
        '''
        countlen = self.__count_length__(app)
        maxchartlen = self.settings.chart.getmaxresults()
        if maxchartlen < 0:
            return countlen
        return min(countlen, maxchartlen)

    def get_one_row(self, app, rownum):
        '''Return one row of table data for the specified app.
           This should be overridden in any Cache subclasses
           to access the underlying data storage object.
           
           Returns (dbname, count, goid, dbid, goname)
        '''
        if app in self.settings.apps:
            return self.table[app][rownum]
        else:
            return None
        
    def get_one_cell(self, app, rownum, colnum):
        '''Returns a particular table cell for application
           app. This method likely does not need to be
           overridden in subclasses.
        '''
        if app in self.settings.apps:
            return self.get_one_row(app, rownum)[colnum]
        else:
            return None
    
    def get_url(self, app, rownum, go_link=False):
        '''Retrieve the linking URL to a particular app
           or gene ontology website.
        '''
        row = self.get_one_row(app, rownum)
        
        if not row: return None
        elif go_link: id = row[2]
        else: id = row[3]
        
        if id != None and app in self.linkdb.keys() and not go_link:
            return self.linkdb[app] % id
        elif id != None:
            return self.linkdb['GO'] % id
        else:
            return None
    
    def __go_name__(self, go_id):
        '''Retrieve the gene ontology name for the given
           term id. This should only be called if GO lookup
           is set to True.
        '''
        self.go_cursor.execute(
            'select name, term_definition from `term` join `term_definition`' + \
            ' on id = term_id where acc = "%s"' % (go_id))
        goinfo = self.go_cursor.fetchone()
        
        if goinfo: return goinfo[0]
        else: return None
    
    def get_counts(self, app):
        '''Retrieve an array of data for chart generation.
           Returns [(value1, value2, ...), (label1, label2, ...)]
           This method must be overridden in any subclasses
           to retrieve the data from the underlying structure
           and return it in the specified format.
        '''
        if app in self.settings.apps:
            counts = [self.count[app][n] for n in \
                      range(self.get_count_length(app))]
            counts = zip(*counts)
            if len(counts) > 0:
                return counts
            else:
                return [None, None]
        else:
            return [None, None]

class SQLiteCache(Cache):
    '''Subclass of Cache that uses a SQLite database to
       store the results of the MySQL query.
    '''
    
    def __init__(self, settings):
        Cache.__init__(self, settings)
    
    def __open_cache__(self):
        '''Open a connection and cursor to the SQLite
           database located at self.filename
        '''
        self.conn = sqlite3.connect(self.filename)
        self.cache_cursor = self.conn.cursor()
    
    def __create_count_group__(self, app):
        '''Create a group (table) in the open SQLite
           database for storing count query results.
        '''
        self.cache_cursor.execute("""
                CREATE TABLE `%s_counts`
                    ( `name` varchar(2048) NOT NULL,
                      `count` int(10) DEFAULT NULL,
                PRIMARY KEY (`name`) );""" % (app))
    
    def __insert_count_record__(self, app, name, count):
        '''Insert a record retrieved by the MySQL query
           into the SQLite database $APP_counts table.
        '''
        self.cache_cursor.execute("""
                INSERT OR IGNORE INTO `%s_counts`
                    ( `name`, `count` )
                VALUES ( "%s", "%s" );""" %
                    (app, name, count))
        
    def __create_match_group__(self, app):
        '''Create a group (table) in the open SQLite
           database for storing match query results.
        '''
        self.cache_cursor.execute("""
                CREATE TABLE `%s_matches`
                    ( `name` varchar(2048) NOT NULL,
                      `count` int(10) DEFAULT NULL,
                      `goid` varchar(10) DEFAULT NULL,
                      `dbid` varchar(16) NOT NULL,
                      `goname` varchar(1024) DEFAULT NULL,
                PRIMARY KEY (`dbid`,`goid`) );""" % (app))
    
    def __insert_match_record__(self, app, dbid, name, count, goid, goname):
        '''Insert a match record into the SQLite database.
        '''
        self.cache_cursor.execute("""
                INSERT OR IGNORE INTO `%s_matches`
                    ( `name`, `count`, `goid`, `dbid`, `goname` )
                VALUES ( "%s", "%s", "%s", "%s", "%s" );""" %
                    (app, name, count, goid, dbid, goname))
        
    def __commit_records__(self):
        '''Commit the statements that have been executed so far.
        '''
        self.conn.commit()
    
    def __match_length__(self, app):
        self.cache_cursor.execute("""
                SELECT count(1) FROM `%s_matches`;""" % (app))
        (length, ) = self.cache_cursor.fetchone()
        return length
    
    def __count_length__(self, app):
        self.cache_cursor.execute("""
                SELECT count(1) FROM `%s_counts`;""" % (app))
        (length, ) = self.cache_cursor.fetchone()
        return length

    def get_one_row(self, app, rownum):
        '''Retrieve a row from the match SQLite table for
           application app.
           Format: (dbname, count, goid, dbid, goname)
        '''
        if app in self.settings.apps:
            self.cache_cursor.execute("""
                    select name, count, goid, dbid, goname
                    from   `%s_matches`
                    limit %s, 1
                """ % (app, rownum))
            return self.cache_cursor.fetchone()
        else:
            return None
    
    def get_counts(self, app):
        '''Query the SQLite database for the counts
           data and return it in the format
           [(count1, count2, ...), (label1, label2, ...)]
        '''
        if app in self.settings.apps:
            maxresults = self.get_count_length(app)
            self.cache_cursor.execute("""
                    select count, name
                    from   `%s_counts`
                    limit %s
                """ % (app, maxresults))
            results = self.cache_cursor.fetchall()
            if results:
                return zip(*results)
            else:
                return [None, None]
        else:
            return [None, None]
        
class IPRStatsData:
    '''This class is the original object used to retrieve
       aggregate results from the database.  It is now
       fairly useless except to choose between different
       cache objects.
    '''
    
    def __init__(self, settings):
        
        self.settings = settings
        self.cache = SQLiteCache(self.settings)
        
        self.chart = {}
        for app in self.settings.getapps():
            self.chart[app] = Chart(app, self.cache, app + ' Matches')
        
        sqlpath = os.path.join(self.settings.getsessiondir(), 'iprsql.sql')
        if os.path.exists(sqlpath):
            os.remove(sqlpath)
        

# Settings classes
#-----------------------------------------------------------------------------

# General imports
import tempfile
import platform
import shutil
import sys

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
                self.installdir = os.path.join(sys.prefix, 'data')
            else:
                self.installdir = os.path.join(sys.prefix, 'share',
                                        'pyshared', 'iprstats', 'data')
        else:
            self.installdir = os.path.join(os.getcwd(), 'data')

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
            raise TypeError, "argument ConfigPath in __load_" + \
                             "settings__() cannot be None."
        
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
           and deletes the old session files if possible.
           Returns: the new session id (str)
        '''
        
        if session_id:
            self.session = session_id
        else:
            try: # Bad hack... fix this...
                shutil.rmtree(self.getsessiondir())
            except:
                pass
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
        
        
# Chart class
#-----------------------------------------------------------------------------

try:
    import pylab
    pylab_avail = True
except ImportError:
    pylab_avail = False
    
try:
    import wx
    wx_avail = True
except ImportError:
    wx_avail = False
    
from pygooglechart import PieChart2D, GroupedHorizontalBarChart

class Chart:
    """Object used to define the data, labels, title, filename,
       etc for generating, saving, and displaying charts.
    """
    
    def __init__(self, app, cache, chart_title=None):
        """Initialize a chart with its associated app, the
           global cache, and a title you'd like to give it.
        """

        self.app = app
        self.cache = cache
        self.chart_title = chart_title
        
        if chart_title:
            self.filename = os.path.join(self.cache.settings.getsessiondir(),
                    chart_title.replace(' ','_').lower() +
                    self.cache.settings.getchartsettings().getgenerator() +
                    self.cache.settings.getchartsettings().gettype() + '.png')
        else:
            self.filename = os.path.join(self.cache.settings.getsessiondir(),
                                         app + '.png')
    
    def GetChartTitle(self):
        """Returns the chart title
        """
        return self.chart_title
    
    def GetFilename(self):
        """Returns the generated file path that the chart
           is downloaded to by default.
        """
        return self.filename
    
    def SetChartTitle(self, chart_title):
        """Set the chart title, and by doing so, change
           default filename for the chart.
        """
        assert(type(chart_title) is str)
        self.chart_title = chart_title
        self.filename = os.path.join(self.cache.settings.getsessiondir(),
                    chart_title.replace(' ','_').lower() +
                    self.cache.settings.getchartsettings().getgenerator() +
                    self.cache.settings.getchartsettings().gettype() + '.png')
        
    def CreateGooglePie(self, counts, labels, settings):
        """Create a pie chart using the Google Charting API.
        """
        width = int(3.6*settings.getscale())
        height = int(settings.getscale())
        chart = PieChart2D(width, height)
        chart.add_data(counts)
        chart.set_pie_labels(labels)
        chart.set_title(self.chart_title)
        chart.set_colours(('66FF66', 'FFFF66', '66FF99'))
        return chart
    
    def CreateGoogleBar(self, counts, labels, settings):
        """Create a bar chart using the Google Charting API.
        """
        barwidth = int(settings.getscale() / 20)
        width = int(3.6*settings.getscale())
        height = len(counts) * (barwidth+8) + 35
        stp = (counts[0] + 9) / 10
        max_x = min(counts[0]/stp + 1, 11) * stp
        chart = GroupedHorizontalBarChart(width, height, x_range=(0, max_x))
        chart.set_bar_width(barwidth)
        chart.add_data(counts)
        reversed_labels = [label for label in labels]
        reversed_labels.reverse()
        chart.set_axis_labels('x', range(0,max_x + 1, stp))
        chart.set_axis_labels('y', reversed_labels)
        chart.set_title(self.chart_title)
        chart.set_colours(('66FF66', 'FFFF66', '66FF99'))
        return chart
    
    def CreatePylabPie(self, counts, labels, settings):
        """Create a pie chart using PyLab/Matplotlib.
        """
        pylab.figure(figsize=(7, 2), dpi=150)
        pylab.axis('scaled')
        _, tlabels = pylab.pie(counts, labels=labels, shadow=False)
        for label in tlabels:
            label.set_size(9)
        pylab.title(self.chart_title, fontsize=12)
    
    def CreatePylabBar(self, counts, labels, settings):
        """Create a bar chart using PyLab/Matplotlib.
        """
        pylab.figure(figsize=(7, 2), dpi=150)
        pylab.barh(range(len(counts)-1, -1, -1), counts, height=0.6)
        pylab.title(self.chart_title, fontsize=12)
        
    def Save(self, settings=None, filename=None):
        """Generate the chart using the given ChartSettings
           object and download it to chart_filename.
        """
        if not settings:
            settings = self.cache.settings.getchartsettings()
        if not filename:
            filename = self.filename
        
        counts, labels = self.cache.get_counts(self.app)
        if not counts or len(counts) < 1:
            return False
        
        assert(len(counts) == len(labels))
        
        #try:
        if settings.getgenerator() == 'pylab':
            if settings.gettype() == 'pie':
                self.CreatePylabPie(counts, labels, settings)
            else:
                self.CreatePylabBar(counts, labels, settings)
            pylab.savefig(filename)
        else:
            if settings.gettype() == 'pie':
                chart = self.CreateGooglePie(counts, labels, settings)
            else:
                chart = self.CreateGoogleBar(counts, labels, settings)
            chart.download(filename)
        return True
        #except:
        #    return False
    
    def GetChart(self, settings=None):
        """Return a wxPython object to display in the GUI. Right
           now it only saves the chart and returns a Bitmap, but
           eventually it could draw and return charts drawn in a
           wxCanvas object.
        """
        if not settings:
            settings = self.cache.settings.getchartsettings()
        
        if self.Save(settings) and wx_avail:
            return wx.Bitmap(self.filename, wx.BITMAP_TYPE_ANY)
        else:
            return None

'''
if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.readfp(open('iprstats.cfg'))
    i = IPRStatsData('Xs7O4pYH',config)
    i.init_match_data('TIGRFAMs')
    while True:
        row = i.get_link_data_row()
        if not(row): break
'''
    
