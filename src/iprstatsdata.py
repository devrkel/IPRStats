#!/usr/bin/python
import os, ConfigParser
try:
    from pylab import *
    pylab_avail = True
except:
    pylab_avail = False
    
from pygooglechart import PieChart2D
import sqlite3
import MySQLdb

class IPRStatsData:
    
    def __init__(self, session, config):
        self.session = session
        self.config = config
        self.go_lookup = self.config.getboolean('general','go_lookup')
        
        # Database connections
        self.conn = self._get_db_connection(config)
        if self.go_lookup:
            self.go_conn = self._get_go_db_connection(config)
            self.go_cursor = self.go_conn.cursor()
        
        # Separate cursors for counts and matches
        self.count_cursor = self.conn.cursor()
        self.match_cursor = self.conn.cursor()
        
        # Current app/match db being used
        self.current_app = None
        
        # Hash of database links
        self.linkdb = {
            'PFAM'       :'http://pfam.sanger.ac.uk/family?acc=%s',
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
    
    # Private method to retrieve the local database connection given the configuration
    # Throws a connection error if it cannot connect
    def _get_db_connection(self, config):
        if config.getboolean('local db','use_sqlite'):
            return sqlite3.connect(os.path.join(config.get('general','directory'),
                                        self.session,config.get('local db','db')))
        else:
            return MySQLdb.connect(host=self.config.get('local db', 'host'),
                    user=self.config.get('local db','user'), passwd=self.config.get('local db','passwd'),
                    port=self.config.getint('local db','port'), db = self.config.get('local db','db'))
    
    # Private method to retrieve GO Term database connection
    # Throws a connection error if it cannot connect
    def _get_go_db_connection(self, config):
        return MySQLdb.connect(host=self.config.get('go db', 'host'),
            user=self.config.get('go db','user'), passwd=self.config.get('go db','passwd'),
            port=self.config.getint('go db', 'port'), db = self.config.get('go db','db'))
    
    # Get a list of (name, count) pairs for a given app/match db
    # Returns [(name1, name2, name3), (count1, count2, count3)] or None
    def get_counts(self, app, limit=None):
        count_by_name = []
        if not limit:
            limit = self.config.get('general','max_chart_results')
        
        if limit == 0:
            return None
            
        self.count_cursor.execute("SELECT name, count(1) as count FROM `%s_iprmatch` " % (self.session) + 
                        "WHERE db_name ='%s' GROUP BY id " % (app) + 
                        "ORDER BY count DESC, name asc LIMIT %s" % (limit))
        for row in self.count_cursor:
            count_by_name.append((int(row[1]), (row[0])))
        
        if len(count_by_name) > 0:
            return zip(*count_by_name)
        else:
            return None
    
    # Generate a chart given [(label1, label2), (value1, value2)] data
    # Returns True or False depending on if the chart was generated
    def get_chart(self, chart_data, chart_title, chart_filename, chart_type='pylab'):
        if chart_data:
            [count, labels] = chart_data
            chart_generated = False
            if chart_type == 'google':
                chart = PieChart2D(730, 300)
                chart.set_colours(('66FF66', 'FFFF66', '66FF99'))
                chart.set_title(chart_title)
                chart.add_data(list(count))
                chart.set_pie_labels(list(labels))
                try:
                    chart.download(chart_filename)
                    return True
                except:
                    chart_generated = False
            if (chart_type == 'pylab' or not chart_generated) and pylab_avail:
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
    
    # Sets the match cursor for iterating through the matches
    def init_match_data(self, app, limit=None):
        
        if not limit:
            limit = self.config.get('general','max_table_results')
        self.current_app = app
        
        self.match_cursor.execute("""
            select   A.name, B.match_id, C.class_id, A.count
            from     ( select   name, pim_id, count(1) as count
                       from     `%(session)s_iprmatch`
                       where    db_name = '%(db)s'
                       group by id
                       order by count desc, id asc, name asc
                       limit    %(limit)s
                     ) as A
                     left outer join `%(session)s_protein_interpro_match` as B on A.pim_id = B.pim_id
                     left outer join `%(session)s_protein_classification` as C on B.protein_id = C.protein_id
            order by A.count desc, A.name asc;""" %({'session':self.session, 'db':app, 'limit':limit}))

    # Get the raw database results from the match data query
    # Returns (Name, DB_ID, GO_ID, Count) or None
    def get_raw_match_data_row(self):
        return self.match_cursor.fetchone()
    
    # Appends the database url and GO url to the raw match data
    # Returns (DB_ID, DB_Name, DB_URL, Count, GO_Name, GO_URL) or None
    def get_link_data_row(self):
        row = self.get_raw_match_data_row()
        if row:
            name, db_id, go_id, count = row
            if self.current_app in self.linkdb.keys():
                db_url = self.linkdb[self.current_app] % db_id
            else:
                db_url = ''
            go_url = self.linkdb['GO'] % go_id
            
            if self.go_lookup:
                go_info = self.retrieve_go_info(go_id)
                return db_id, name, db_url, count, go_info[0], go_url, go_info[1]
            else:
                return db_id, name, db_url, count, go_id, go_url
        else:
            return None
    
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

if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.readfp(open('ipsstats.cfg'))
    i = IPRStatsData('Xs7O4pYH',config)
    i.init_match_data('TIGRFAMs')
    while True:
        row = i.get_link_data_row()
        if not(row): break
    