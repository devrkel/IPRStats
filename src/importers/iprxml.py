#!/usr/bin/python
import os, sys, time

try: import MySQLdb
except ImportError:
    print "Note: You must have python-mysqldb installed " +\
          "to enable Gene Ontology lookup."

try: import sqlite3
except ImportError:
    print "You must have SQLite3 for Python installed."
    sys.exit(2)

import shutil
from threading import Thread
from xml.sax import ContentHandler
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces

'''
class ProteinAnnotation:
    def __init__(self, id):
        self.id = id
        self.length = length
        self.crc64 = crc64
    def __getitem__(self):
        return id
'''
class EBIXML(ContentHandler):

    def __init__(self,settings):
        self.protein = {}
        self.interpro = {}
        self.match = {}
        self.location = {}

        self.class_id = ''
        self.class_type = ''
        
        self.settings = settings

        self.in_protein = False
        self.in_interpro = False
        self.in_match = False
        self.in_location = False
        self.in_classification = False
        self.outpath = self.settings.getsessiondir()
        sqlfilepath = os.path.join(self.outpath, 'iprsql.sql')
        self.outfile = open(sqlfilepath,'w')

        if self.settings.usesqlite():
            self.ignorecmd = "OR IGNORE"
            self.autoincrement = ""
            sqldb = os.path.join(self.settings.getsessiondir(),
                                 self.settings.getlocaldb().getdb())
            print sqldb
            self.db_con = sqlite3.connect(sqldb)
        else:
            self.ignorecmd = "IGNORE"
            self.autoincrement = " AUTO_INCREMENT"
            
            dbsettings = self.settings.getlocaldb()
            self.db_con = MySQLdb.connect(
                            db=dbsettings.getdb(),
                            host=dbsettings.gethost(),
                            user=dbsettings.getuser(),
                            passwd=dbsettings.getpasswd())
        self.db_cursor = self.db_con.cursor()
        try:
            self.db_cursor.execute(
                        "SELECT MAX(pim_id) FROM protein_interpro_match;")
            self.pim_id = self.db_cursor.fetchall()[0][0]
        except:
            self.pim_id = 1
            
        structpath = os.path.join(self.settings.getdatadir(), 'structure.sql')
        if not os.path.exists(structpath):
            if os.path.exists('structure.sql'):
                shutil.copyfile('structure.sql',structpath)
            elif os.path.exists(os.path.join(
                        self.settings.getinstalldir(), 'structure.sql')):
                shutil.copyfile(
                        os.path.join(self.settings.getinstalldir(),
                                       'structure.sql'), structpath)
            else:
                print "iprstats: import error: can't find structure.sql"
                sys.exit(2)
                
        db_struct = open(structpath,'r')
        struct_sql = db_struct.read() % (
                    {'SESSION':self.settings.getsession(),
                     'AUTO':self.autoincrement})
        print >> self.outfile, struct_sql
        self.outfile.flush()
        
        if self.pim_id is None:
            self.pim_id = 1

    def startElement(self, name, attrs):
        if name == "protein":
            self.in_protein = True
            self.protein = {'id': attrs.get('id',None),
                            'length': int(attrs.get('length',None)),
                            'crc64':attrs.get('crc64', None)}
        elif name in ("interpro", "ipr"):
            self.in_interpro = True
            self.interpro = {'id': attrs.get('id', None),
                             'name': attrs.get('name',None).replace('"',''),
                             'type': attrs.get('type',None)}
        elif name == "match":
            self.pim_id += 1
            self.in_match = True
            self.match = {'id': attrs.get('id',None),
                          'name': attrs.get('name',None).replace('"',''),
                          'dbname': attrs.get('dbname',None)}
        elif name in ("location", "lcn") and self.in_match:
            self.in_location = True
            str_score = attrs.get('score',None)
            if str_score == "." or str_score == "NA": str_score = "0.0"
            self.location = { 'start': int(attrs.get('start',None)), 
                           'end': int(attrs.get('end',None)), 
                            'score': float(str_score),
                           'status': attrs.get('status',None),
                           'evidence': attrs.get('evidence',None)}
        elif name == "classification":
            self.in_classification = True
            self.class_type = attrs.get('class_type', None)
            self.class_id = attrs.get('id', None)
    def endElement(self, name):
        if name == "protein":
            self.in_protein = False
            sql_string  = 'REPLACE INTO `%s_protein` ' % (
                                                self.settings.session)
            sql_string += '(protein_id, length, crc64, nprot) VALUES '
            sql_string += '("%s", %d, "%s", %d); ' % (
                       self.protein["id"], self.protein["length"],
                       self.protein["crc64"], 1)
            #sql_string += 'ON DUPLICATE KEY UPDATE nprot=nprot+1;'
            print >> self.outfile, sql_string
            self.outfile.flush()
        elif name in ("interpro", "ipr"):
            self.in_interpro = False
            sql_string  = 'INSERT %s INTO `%s_interpro` ' % (
                            self.ignorecmd, self.settings.session)
            sql_string += '(interpro_id, name, ipr_type) '
            sql_string += 'VALUES ("%s", "%s", "%s");' % (
                            self.interpro['id'], self.interpro['name'],
                            self.interpro['type'])
            sql_string2  = 'INSERT INTO `%s_protein_interpro` ' % (
                            self.settings.session)
            sql_string2 += '(protein_id, interpro_id) VALUES '
            sql_string2 += '("%s", "%s");' % (
                            self.protein['id'], self.interpro['id'])
            print >> self.outfile, sql_string
            print >> self.outfile, sql_string2
        elif name == "match":
            self.in_match = False
            sql_string = 'INSERT INTO `%s_protein_interpro_match` ' % (
                     self.settings.session)
            sql_string += "(pim_id, protein_id, interpro_id, match_id) "
            
            sql_string += 'VALUES (%d, "%s", "%s", "%s"); ' % (
                      self.pim_id, self.protein['id'],
                      self.interpro['id'], self.match['id'])
            sql_string2 = 'INSERT %s INTO `%s_iprmatch` ' % (
                     self.ignorecmd, self.settings.session)
            sql_string2 += "(id, pim_id, name, db_name) "

            sql_string2 += ' VALUES ("%s", %d, "%s", "%s");' % (
                                self.match['id'], self.pim_id,
                                self.match['name'], self.match['dbname'])
            print >> self.outfile, sql_string
            print >> self.outfile, sql_string2
        elif name in ("location", "lcn"):
            self.in_location = False
            sql_string = 'INSERT INTO `%s_location` ' % (self.settings.session)
            sql_string += "(loc_id, match_id, pim_id, start_p, "
            sql_string += "end_p, score, status, evidence) "
            sql_string += 'VALUES  (NULL, "%s", %d, %d, %d, %e, "%s", "%s");' % (
                       self.match['id'],
                       self.pim_id,
                       self.location['start'],
                       self.location['end'],
                       self.location['score'],
                       self.location['status'],
                       self.location['evidence'])
            print >> self.outfile, sql_string
        elif name == "classification":
            self.in_classification = False
            sql_string  = 'INSERT INTO `%s_protein_classification` ' % (
                          self.settings.session)
            sql_string += "(id, protein_id, class_id, class_type) "
            sql_string += 'VALUES (NULL, "%s", "%s", "%s");' % (
                          self.protein["id"], self.class_id, self.class_type)
            print >> self.outfile, sql_string
        
    def endDocument(self):
        # Update the mysql database
        if self.outfile is not sys.stdout:
            self.outfile.flush()
            if self.settings.usesqlite():
                sqlfile = open(self.outfile.name, 'r')
                for line in sqlfile:
                    self.db_cursor.execute(line)
                self.db_con.commit()
                self.db_cursor.close()
                sqlfile.close()
            else:
                dbsettings = self.settings.getlocaldb()
                os.system("mysql %s -u%s -h %s -p%s < %s" %
                      (dbsettings.getdb(),
                       dbsettings.getuser(),
                       dbsettings.gethost(),
                       dbsettings.getpasswd(),
                       self.outfile.name))
                log = open(os.path.join(self.outpath,'tbl_creation.log'), 'a')
                log.write(str(time.ctime()) + "\t" + \
                          self.settings.getsession() + "\n")

class ParseXMLFile(Thread):
    def __init__(self, filename, settings):
        Thread.__init__(self)
        self.filename = filename
        self.settings = settings
    
    def run(self):
        # Create a parser
        parser = make_parser()
        parser.setFeature(feature_namespaces, 0)

        # Create the Handler
        exh = EBIXML(self.settings)

        # Parse file into DB
        parser.setContentHandler(exh)
        parser.parse(self.filename)
        del parser
'''
if __name__ == '__main__':
    filelist=  []
    outdir = None
    session = None
    usage = "Usage: ebixml.py [-c | --config= <config_file>] " + \
                        "[-o | --output= <output_directory>] " + \
                        "[-s | --session= <unique_identifier>] " +\
                        "<xml_file ...>"
    
    # 
    try:
        opts, args = getopt.getopt(sys.argv[1:],"h:c:o:s:",
                                   ["help","config=","output=","session="])
    except getopt.GetoptError:
        print usage
        sys.exit(2)
    config = None
    for o, a in opts:
        if o in ("-h", "--help"):
            print usage
            sys.exit(1)
        elif o in ("-c", "--config"):
            config = ConfigParser.ConfigParser()
            config.readfp(open(a))
        elif o in ("-o", "--output"):
            outdir = a
        elif o in ("-s", "--session"):
            session = a
        else:
            filelist.append(a)
    if len(args) < 1:
        print usage
        sys.exit(2)
    elif len(args) > 1 and session:
        print "Parsing more than one XML file; using random session ids"

    print args
    fver = 1
    for filename in args:

        # Create a random session id
        if len(args) > 1:
            chars = string.letters + string.digits
            session = ''.join([choice(chars) for i in xrange(8)])
               
        print "doing", filename
        
        if outdir:
            path = os.path.join(outdir, session)
        else:
            path = os.path.join(config.get('general','directory'), session)
            
        if not(os.path.exists(path)):
            os.mkdir(path)
        
        outfile = os.path.join(path,
            os.path.splitext(os.path.basename(filename))[0] + ".iprscan.sql")

        # Create a parser
        parser = make_parser()

        # Tell the parser we are not interested in XML namespaces
        parser.setFeature(feature_namespaces, 0)

        # Create the Handler
        if outfile:
            exh = EBIXML(session, config=config,outfile=open(outfile,"w"))
        else:
            raise Exception, "No output file specified."

        parser.setContentHandler(exh)
        parser.parse(filename)
        print "Done", filename, "Session", session
        fver += 1
        del parser
'''