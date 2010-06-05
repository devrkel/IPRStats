#!/usr/bin/python
import string, os, sys, time, getopt
import MySQLdb
import ConfigParser
from random import choice
from xml.sax import ContentHandler
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces

class ProteinAnnotation:
    def __init__(self, id):
        self.id = id
        self.length = length
        self.crc64 = crc64
    def __getitem__(self):
        return id

class EBIXML(ContentHandler):

    def __init__(self,session,config=None,outfile=sys.stdout):
        self.protein = {}
        self.interpro = {}
        self.match = {}
        self.location = {}

        self.class_id = ''
        self.class_type = ''
        
        self.session = session

        self.in_protein = False
        self.in_interpro = False
        self.in_match = False
        self.in_location = False
        self.in_classification = False
        self.outfile = outfile
        if config:
            self.config = config
            self.db_con = MySQLdb.connect(host=self.config.get('local db','host'),
                                    user=self.config.get('local db','user'),
                                    passwd=self.config.get('local db','passwd'),
                                    db=self.config.get('local db','db'))
            self.db_cursor = self.db_con.cursor()
            try:
                self.db_cursor.execute("SELECT MAX(pim_id) FROM protein_interpro_match;")
                self.pim_id = self.db_cursor.fetchall()[0][0]
            except:
                self.pim_id = 1
            
            db_struct = open('structure.sql', 'r')
            struct_sql = db_struct.read() % ((self.session,)*7)
            print >> self.outfile, struct_sql
            self.outfile.flush()
            
            if self.pim_id is None:
                self.pim_id = 1
        else:
            self.config = None
            self.pim_id = 1

    def startElement(self, name, attrs):
        if name == "protein":
            self.in_protein = True
            self.protein = {'id': attrs.get('id',None), 'length': int(attrs.get('length',None)),
                         'crc64':attrs.get('crc64', None)}
        elif name in ("interpro", "ipr"):
            self.in_interpro = True
            self.interpro = {'id': attrs.get('id', None), 'name': attrs.get('name',None).replace('"',''), 
                          'type': attrs.get('type',None)}
        elif name == "match":
            self.pim_id += 1
            self.in_match = True
            self.match = {'id': attrs.get('id',None), 'name': attrs.get('name',None).replace('"',''), 
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
            sql_string = 'INSERT INTO `%s_protein` (protein_id, length, crc64, nprot) VALUES ("%s", %d, "%s", %d) ' % (
                       self.session, self.protein["id"], self.protein["length"], self.protein["crc64"], 1)
            sql_string += 'ON DUPLICATE KEY UPDATE nprot=nprot+1;'
            print >> self.outfile, sql_string
            self.outfile.flush()
        elif name in ("interpro", "ipr"):
            self.in_interpro = False
            sql_string = 'INSERT IGNORE INTO `%s_interpro` (interpro_id, name, ipr_type) VALUES ("%s", "%s", "%s");' % (
                            self.session, self.interpro['id'], self.interpro['name'], self.interpro['type'])
            sql_string2 = 'INSERT INTO `%s_protein_interpro` (protein_id, interpro_id) VALUES ("%s", "%s");' % (
                     self.session, self.protein['id'], self.interpro['id'])
            print >> self.outfile, sql_string
            print >> self.outfile, sql_string2
        elif name == "match":
            self.in_match = False
            sql_string = 'INSERT INTO `%s_protein_interpro_match` ' % (
                     self.session)
            sql_string += "(pim_id, protein_id, interpro_id, match_id) "
            
            sql_string += 'VALUES (%d, "%s", "%s", "%s"); ' % (
                      self.pim_id, self.protein['id'], self.interpro['id'], self.match['id'])
            sql_string2 = 'INSERT IGNORE INTO `%s_iprmatch` ' % (
                     self.session)
            sql_string2 += "(id, pim_id, name, db_name) "

            sql_string2 += ' VALUES ("%s", %d, "%s", "%s");' % (
                                self.match['id'], self.pim_id, self.match['name'], self.match['dbname'])
            print >> self.outfile, sql_string
            print >> self.outfile, sql_string2
        elif name in ("location", "lcn"):
            self.in_location = False
            sql_string = 'INSERT INTO `%s_location` ' % (self.session)
            sql_string += "(loc_id, match_id, pim_id, start_p, end_p, score, status, evidence) "
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
            sql_string = 'INSERT INTO `%s_protein_classification` ' % (self.session)
            sql_string += "(id, protein_id, class_id, class_type) "
            sql_string += 'VALUES (NULL, "%s", "%s", "%s");' % (
                        self.protein["id"], self.class_id, self.class_type)
            print >> self.outfile, sql_string
        
    def endDocument(self):
        # Update the mysql database
        if self.outfile is not sys.stdout:
            self.outfile.flush()
            os.system("mysql %s -u%s -h %s -p%s < %s" %
                      (self.config.get('local db','db'), self.config.get('local db','user'),
                       self.config.get('local db','host'), self.config.get('local db','passwd'),
                       self.outfile.name))
            log = open(os.path.join(self.config.get('general','directory'),
                                    'tbl_creation.log'), 'a')
            log.write(str(time.ctime()) + "\t" + self.session + "\n")

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
        opts, args = getopt.getopt(sys.argv[1:],"h:c:o:s:",["help","config=","output=","session="])
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
