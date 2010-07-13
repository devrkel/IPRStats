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
        
        self.count_length = {}
        self.match_length = {}
        for app in self.settings.getapps():
            self.count_length[app] = 0
            self.match_length[app] = 0
        
        # Hash of database links
        self.linkdb = {
            'PFAM'       :'http://pfam.janelia.org/family?acc=%s',
            'PIR'        :'http://pir.georgetown.edu/cgi-bin/ipcSF?id=%s',
            'HAMAP'      :'http://www.expasy.org/unirule/%s',
            'PANTHER'    :'http://www.pantherdb.org/panther/family.do?' + 
                          'clsAccession=%s',
            'PRINTS'     :'http://www.bioinf.manchester.ac.uk/cgi-bin/' + 
                          'dbbrowser/PRINTS/DoPRINTS.pl?cmd_a=Display&' + 
                          'qua_a=/Full&fun_a=Code&qst_a=%s',
            'PRODOM'     :'http://prodom.prabi.fr/prodom/current/cgi-b' + 
                          'in/request.pl?question=DBEN&query=%s',
            'PRO'        :'http://expasy.org/cgi-bin/prosite-search-ac?%s',
            'SMART'      :'http://smart.embl-heidelberg.de/smart/do_ann' + 
                          'otation.pl?BLAST=DUMMY&DOMAIN=%s',
            'SUPERFAMILY':'http://supfam.cs.bris.ac.uk/SUPERFAMILY/cgi-' + 
                          'bin/scop.cgi?sunid=%s',
            'TIGRFAMs'   :'http://cmr.jcvi.org/cgi-bin/CMR/HmmReport.cgi' + 
                          '?hmm_acc=%s',
            'GENE3D'     :'http://www.cathdb.info/gene3d/%s',
            'GO'         :'http://www.ebi.ac.uk/QuickGO/GTerm?id=%s#ancchart'}
        
        self.__populate_cache__()
    
    def __get_db_conn__(self):
        '''Attempt to get a database connection (either MySQL or SQLite
           based on settings) and return the connection.  Defaults to
           SQLite if it cannot get a MySQL connection.
        '''
        dbs=self.settings.getlocaldb()
        
        if not self.settings.usesqlite():
            try:
                conn = self._get_mysql_connection(dbs)
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
                self.count_length[app] += 1
                self.__insert_count_record__(app, name, count)
            self.__commit_records__()
                
            self.__match_query__(app)
            self.__create_match_group__(app)
            for name, dbid, goid, count in self.db_cursor:
                if self.settings.usegolookup():
                    goname = self.__go_name__(goid)
                else: goname = None
                self.match_length[app] += 1
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
    
    def get_match_length(self, app):
        '''Returns the visible number of rows in the stored
           table data, limited by the "max table results"
           setting or the number of available table rows.
        '''
        matchlen = self.match_length[app]
        maxtablelen = self.settings.getmaxtableresults()
        if maxtablelen < 0:
            return matchlen
        return min(matchlen, maxtablelen)

    def get_count_length(self, app):
        '''Returns the number of results to be displayed
           in a graph, limited either by the "max chart
           results" setting or the number of available results.
        '''
        countlen = self.count_length[app]
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

from chart import Chart
        
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
            
        os.remove(os.path.join(self.settings.getsessiondir(), 'iprsql.sql'))
        #if self.settings.usesqlite():
        #    sqlitepath = os.path.join(self.settings.getsessiondir(),
        #                       self.settings.getlocaldb().getdb())
        #    os.remove(sqlitepath)

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
    