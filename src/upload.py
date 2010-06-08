#!/usr/bin/python
import cgi, string, os, sys, tempfile
import cgitb; cgitb.enable()
import ConfigParser
from random import choice
from export_html import export_html
from ebixml import EBIXML
from xml.sax import ContentHandler
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces
try: # Windows needs stdio set for binary mode.
    import msvcrt
    msvcrt.setmode (0, os.O_BINARY) # stdin  = 0
    msvcrt.setmode (1, os.O_BINARY) # stdout = 1
except ImportError:
    pass

def save_uploaded_file (form_field, upload_dir):
    """This saves a file uploaded by an HTML form.
       The form_field is the name of the file input field from the form.
       For example, the following form_field would be "file_1":
           <input name="file_1" type="file">
       The upload_dir is the directory where the file will be written.
       If no file was uploaded or if the field does not exist then
       this does nothing.
    """
    form = cgi.FieldStorage()
    if not form.has_key(form_field): return
    fileitem = form[form_field]
    if not fileitem.file: return
    fout = file (os.path.join(upload_dir, fileitem.filename), 'wb')
    while 1:
        chunk = fileitem.file.read(100000)
        if not chunk: break
        fout.write(chunk)
    fout.close()
    return os.path.join(upload_dir, fileitem.filename)

print "content-type: text/html\n"

# Save the uploaded file temporarily
filepath = save_uploaded_file ("uploadedfile", tempfile.gettempdir())

# Open the configuration file
try:
    config = ConfigParser.ConfigParser()
    config.readfp(open('iprstats.cfg'))
    exp_dir = config.get('html','directory')
except:
    print "You must supply a configuration file and a session id.\n"
    sys.exit(2)

# Create a session ID
chars = string.letters + string.digits
session = ''.join([choice(chars) for i in xrange(8)])

# Parent exits so that the scripts can run without tying up the
# user's browser; redirects them to a "progress" page.
if os.fork():
    print '<META HTTP-EQUIV="Refresh" CONTENT="0; URL=../progress.html?'+session+'">'
    sys.exit()

# Close stdin, stdout, and stderr which would otherwise
# make the parent wait for children to finish before exiting
sys.stdin.close()
sys.stdout.close()
sys.stderr.close()
os.close(0)
os.close(1)
os.close(2)

# Open log file for writing
log = file(os.path.join(exp_dir,session+'.status'), 'a')
log.write('Opening session ' + session + '...\n')
log.write('Beginning to parse file ' + os.path.basename(filepath) + '...\n')
log.flush()

# Create a parser
parser = make_parser()

# Tell the parser we are not interested in XML namespaces
parser.setFeature(feature_namespaces, 0)

# Create the Handler and parse the XML
exh = EBIXML(session, config=config,outfile=open(os.path.join(tempfile.gettempdir(),session+'.sql'),"w"))
parser.setContentHandler(exh)
parser.parse(filepath)
del parser

log.write('Done parsing file ' + os.path.basename(filepath) + '!\n')
log.write('Creating HTML...\n')
log.flush()

exp_dir = os.path.join(exp_dir, session)
if not os.path.exists(exp_dir): os.mkdir(exp_dir)

# Export the HTML
eh = export_html(session, config)
eh.export(directory=exp_dir, chart='google')

log.write('Done! <a href="runs/'+session+'/gene3d.html">Click here</a>\n')
log.close()