#!/usr/bin/python
import os, ConfigParser
try:
    from pylab import *
    pylab_avail = True
except ImportError:
    pylab_avail = False
    
from pygooglechart import PieChart2D, GroupedHorizontalBarChart
import sqlite3
import tempfile
try:
    from tables import *
    USEPYTABLES = True
except:
    USEPYTABLES = False
try:
    import MySQLdb
except ImportError:
    pass
try:
    from win32com.shell import shellcon, shell            
    homedir = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
except ImportError:
    homedir = os.path.expanduser("~")

class IPRStatsData:
    
    def __init__(self, session, config):
        self.session = session
        self.config = config
        self.go_lookup = self.config.getboolean('general','go_lookup')
        self.apps = self.config.get('general','apps').replace('\n',' ')
        self.apps = self.apps.split(', ')
        
        # Database connections
        self.conn = self._get_db_connection(config)
        if self.go_lookup:
            self.go_conn = self._get_go_db_connection(config)
            if self.go_conn:
                self.go_cursor = self.go_conn.cursor()
        
        # Separate cursors for counts and matches
        self.count_cursor = self.conn.cursor()
        self.match_cursor = self.conn.cursor()
        
        # Current app/match db being used
        self.current_app = None
        self.current_apps = None
        self.length = None
        
        # Set cache location to avoid unnecessary queries
        self.sessiondir = os.path.join(homedir, '.iprstats',
                                       self.session)
        if not os.path.exists(self.sessiondir):
            self.sessiondir = tempfile.gettempdir()
        self.cache = os.path.join(self.sessiondir, 'results')
        
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
        
        self.initialize_table_data()
        os.remove(os.path.join(self.sessiondir, 'iprsql.sql'))
        if config.getboolean('local db','use_sqlite'):
            self.match_cursor.close()
            sqlitepath = os.path.join(self.sessiondir,
                                config.get('local db','db'))
            #os.remove(sqlitepath)
    
    # Private method to retrieve the local database connection given the configuration
    # Throws a connection error if it cannot connect
    def _get_db_connection(self, config):
        if config.getboolean('local db','use_sqlite'):
            return sqlite3.connect(os.path.join(homedir, '.iprstats',
                                        self.session,config.get('local db','db')))
        else:
            return MySQLdb.connect(host=self.config.get('local db', 'host'),
                    user=self.config.get('local db','user'), passwd=self.config.get('local db','passwd'),
                    port=self.config.getint('local db','port'), db = self.config.get('local db','db'))
    
    # Private method to retrieve GO Term database connection
    # Throws a connection error if it cannot connect
    def _get_go_db_connection(self, config):
        try: 
            conn = MySQLdb.connect(host=self.config.get('go db', 'host'),
            user=self.config.get('go db','user'), passwd=self.config.get('go db','passwd'),
            port=self.config.getint('go db', 'port'), db = self.config.get('go db','db'))
            return conn
        except:
            print 'Cannot connect to GO DB... disabling GO lookup'
            self.go_lookup = False
            return None
    
    # Get a list of (name, count) pairs for a given app/match db
    # Returns [(name1, name2, name3), (count1, count2, count3)] or None
    def get_counts(self, app, limit=None):
        count_by_name = []
        if not limit:
            limit = self.config.getint('general','max_chart_results')
        
        if limit == 0:
            return None
            
        self.count_cursor.execute("SELECT name, count(1) as count FROM `%s_iprmatch` " % (self.session) + 
                        "WHERE db_name ='%s' GROUP BY id " % (app) + 
                        "ORDER BY count DESC, name asc LIMIT %d" % (limit))
        for row in self.count_cursor:
            count_by_name.append((int(row[1]), (row[0])))
        
        if len(count_by_name) > 0:
            return zip(*count_by_name)
        else:
            return None
    
    # Generate a chart given [(label1, label2, ), (value1, value2, )] data
    # Returns True or False depending on if the chart was generated
    def get_chart(self, chart_data, chart_title, chart_filename,
                  chart_type='pie', chart_gen='pylab'):
        
        if not chart_data:
            return False
        
        if chart_data:
            [count, labels] = chart_data
            chart_generated = False
            if chart_gen == 'google':
                if chart_type == 'pie':
                    chart = PieChart2D(730, 300)
                    chart.add_data(list(count))
                    chart.set_pie_labels(list(labels))
                elif chart_type == 'bar':
                    barwidth = 10
                    height = len(count) * (barwidth+8) + 35
                    stp = int(ceil(count[0] / 10.0))
                    max_x = min(count[0]/stp + 1, 11) * stp
                    chart = GroupedHorizontalBarChart(730, height,
                                                      x_range=(0, max_x))
                    chart.set_bar_width(barwidth)
                    chart.add_data(list(count))
                    labels = list(labels)
                    labels.reverse()
                    '''
                    class FakeAxis:
                        def __init__(self):
                            self.axis_type = 'x'
                            self.positions = None
                            self.has_style = False
                    
                    chart.axis.append(FakeAxis())
                    '''
                    chart.set_axis_labels('x', range(0,max_x + 1, stp))
                    chart.set_axis_labels('y', labels)
                    
                chart.set_title(chart_title)
                chart.set_colours(('66FF66', 'FFFF66', '66FF99'))
                chart.download(chart_filename)
                return True
                    
            if (chart_gen == 'pylab' or not chart_generated) and pylab_avail:
                try:
                    figure(figsize=(7, 2), dpi=150)
                    axis('scaled')
                    _, tlabels = pie(count, labels=labels, shadow=False)
                    for label in tlabels:
                        label.set_size(9)
                    title(chart_title, fontsize=12)
                    savefig(chart_filename)
                    return True
                except:
                    return False
            return False
    
    # Using PyTables and HDF5 to provide data storage to support potentially
    # gigabytes of table information.
    def initialize_table_data(self, app=None):
        if app:
            if type(app) is str:
                self.current_apps = [str]
            else:
                self.current_app = app
        else: self.current_apps = self.apps
        
        if USEPYTABLES:
            
            # Open a file for caching data
            h5f = openFile(self.cache, 'w')
            group = h5f.createGroup("/", 'tables', 'Table information')
            
            for app in self.current_apps:
                
                self.match_cursor.execute("""
                    select   A.name, B.match_id, C.class_id, A.count
                    from     ( select   name, pim_id, count(1) as count
                               from     `%(session)s_iprmatch`
                               where    db_name = '%(db)s'
                               group by id
                               order by count desc, id asc, name asc
                             ) as A
                             left outer join `%(session)s_protein_interpro_match` as B on A.pim_id = B.pim_id
                             left outer join `%(session)s_protein_classification` as C on B.protein_id = C.protein_id
                    order by A.count desc, A.name asc;""" %({'session':self.session, 'db':app}))
                
                table = h5f.createTable(group, app.lower(), TableEntry, app + " table information")
                table_el = table.row
                for match in self.match_cursor:
                    name, db_id, go_id, count = match
                    if app in self.linkdb.keys():
                        db_url = self.linkdb[app] % db_id
                    else:
                        db_url = ''
                    go_url = self.linkdb['GO'] % go_id
                    
                    table_el['dbid'] = db_id
                    table_el['name'] = name
                    table_el['dburl'] = db_url
                    table_el['count'] = count
                    table_el['goid'] = go_id
                    table_el['gourl'] = go_url
                    table_el.append()
                h5f.flush()
            h5f.close()
            self.h5f = openFile(self.cache, 'r')
        else:
            # Open a file for caching data
            self.sqlt = sqlite3.connect(self.cache).cursor()
            
            
            for app in self.current_apps:
                
                self.match_cursor.execute("""
                    select   A.name, B.match_id, C.class_id, A.count
                    from     ( select   name, pim_id, count(1) as count
                               from     `%(session)s_iprmatch`
                               where    db_name = '%(db)s'
                               group by id
                               order by count desc, id asc, name asc
                             ) as A
                             left outer join `%(session)s_protein_interpro_match` as B on A.pim_id = B.pim_id
                             left outer join `%(session)s_protein_classification` as C on B.protein_id = C.protein_id
                    order by A.count desc, A.name asc;""" %({'session':self.session, 'db':app}))
                
                self.sqlt.execute("""
                    CREATE TABLE `%s_matches`
                        ( `dbid` varchar(16) NOT NULL,
                          `name` varchar(2048) NOT NULL,
                          `count` int(10) DEFAULT NULL,
                          `goid` varchar(10) DEFAULT NULL,
                           PRIMARY KEY (`dbid`,`goid`) );""" % (app))
                
                for match in self.match_cursor:
                    name, db_id, go_id, count = match
                    try:
                        self.sqlt.execute("""
                        INSERT OR IGNORE INTO `%s_matches`
                            ( `dbid`, `name`, `count`, `goid` )
                        VALUES ( "%s", "%s", "%s", "%s" );""" %
                            (app, db_id, name, count, go_id))
                    except:
                        print match
        
    def get_table_length(self, app):
        if USEPYTABLES:
            tablelen = eval("self.h5f.root.tables."+app.lower()+".nrows")
        else:
            self.sqlt.execute("""
                select count(1)
                from %s_matches""" % (app))
            (tablelen,) = self.sqlt.fetchone()
        maxtablelen = self.config.getint('general','max_table_results')
        if maxtablelen < 0:
            return tablelen
        return min(tablelen, maxtablelen)
    
    def get_one_row(self, app, rownum):
        if USEPYTABLES and app in self.apps:
            row = eval("self.h5f.root.tables."+app.lower()+"["+str(row)+"]")
        elif app in self.apps:
            self.sqlt.execute("""
                select *
                from   `%s_matches`
                limit %s, 1
            """ % (app, rownum))
            row = self.sqlt.fetchone()
        else:
            return None
        return row
    
    def get_two_rows(self, app, row):
        if app in self.apps:
            if row == 0:
                rows = eval("self.h5f.root.tables."+app.lower()+"["+str(row)+"]")
                return [None, rows]
            try:
                rows = eval("self.h5f.root.tables."+app.lower()+"["+str(row-1)+":"+str(row+1)+"]")
                return rows
            except IndexError:
                return None
        else:
            return None
    
    def get_table_cell(self, app, rownum, colnum):
        if USEPYTABLES and app in self.apps:
            if   colnum == 0: colnum = 5
            elif colnum == 1: colnum = 0
            elif colnum == 2: colnum = 3
            try:
                row = eval("self.h5f.root.tables."+app.lower()+"["+str(rownum)+"]")
                return row[colnum]
            except IndexError:
                return None
        elif app in self.apps:
            colnum += 1
            return self.get_one_row(app, rownum)[colnum]
        else:
            return None
    
    #'''
    
    # Retrieve the GO Term name and definition; slow without local installation
    # Returns (GO_Name, GO_Definition) given GO_ID
    def retrieve_go_info(self, go_id):
        self.go_cursor.execute(
            'select name, term_definition from `term` join `term_definition`' + \
            ' on id = term_id where acc = "%s"' % (go_id))
        goinfo = self.go_cursor.fetchone()
            
        return goinfo
    
    # Closes connections to the databases
    def close(self):
        self.conn.close()
        
if USEPYTABLES:
    class TableEntry(IsDescription):
        dbid      = StringCol(16)   # 16-character String
        name      = StringCol(2048) # 2048-character String
        dburl     = StringCol(2048) # 2048-character String
        count     = UInt16Col()     # Signed 64-bit integer
        goid      = StringCol(10)   # 16-character String
        gourl     = StringCol(2048) # 2048-character String
    

if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.readfp(open('iprstats.cfg'))
    i = IPRStatsData('Xs7O4pYH',config)
    i.init_match_data('TIGRFAMs')
    while True:
        row = i.get_link_data_row()
        if not(row): break
    