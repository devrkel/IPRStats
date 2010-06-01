#!/usr/bin/python
import sys, os, getopt
import ConfigParser
import xlwt
from ipsstatsdata import IPSStatsData

# used to export database information as a spreadsheet
class export_xls:
    
    def __init__(self, session, config):
        self.session = session
        self.ipsstats = IPSStatsData(session, config)
        self.apps = ['PFAM', 'PIR', 'GENE3D', 'HAMAP', 'PANTHER', 'PRINTS',
            'PRODOM','PROFILE', 'PROSITE', 'SMART', 'SUPERFAMILY', 'TIGRFAMs']
        
        self.path = os.path.join(config.get('html','directory'), self.session)
        
    # Generates an entire page complete with menus, charts, and tables
    # TODO: write incrementally so that an entire page is not in memory
    def generate_sheet(self, app, xls_doc):
        # Create a worksheet in the workbook
        sheet = xls_doc.add_sheet(app)
        
        # Create header style
        hdr_font = xlwt.Font()
        hdr_font.name = 'Times New Roman'
        hdr_font.colour_index = 2
        hdr_font.bold = True
        hdr_style = xlwt.XFStyle()
        hdr_style.font = hdr_font
        
        # Create header
        sheet.write(0, 0, "Count")
        sheet.write(0, 1, "DB Name")
        sheet.write(0, 2, "DB ID")
        sheet.write(0, 3, "GO Name")
        sheet.write(0, 4, "GO ID")
        sheet.write(0, 5, "DB Link")
        sheet.write(0, 6, "GO Link")
        
        r = 0;
        self.ipsstats.init_match_data(app)
        while True:
            row = self.ipsstats.get_link_data_row()
            if row:
                r += 1
                sheet.write(r, 0, row[2])
                sheet.write(r, 1, row[0])
                sheet.write(r, 2, row[3])
                sheet.write(r, 3, row[1])
                sheet.write(r, 4, row[4])
                if len(row) == 6:
                    sheet.write(r, 5, row[5])
            else:
                break
    
    def export(self, app=None, directory=None):
        xls_doc = xlwt.Workbook()
        
        if app:
            self.generate_sheet(app, xls_doc)
        else:
            for app in self.apps:
                self.generate_sheet(app, xls_doc)
        
        if directory:
            xls_doc.save(os.path.join(directory, 'test.xls'))
        else:
            xls_doc.save('test.xls')

if __name__ == '__main__':

    usage = "Usage: export_xls.py -c <config_file> -s <session_id> [-a <db_application> -o <output_directory>]"
    app = None
    session = None
    config_file = None
    exp_dir = None
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],"h:a:c:s:o:",["help","app=","config=","session=","output="])
    except getopt.GetoptError:
        print usage
        sys.exit(2)

    for o, a in opts:
        if o in ("-h", "--help"):
            print usage
            sys.exit(1)
        elif o in ("-a", "--app"):
            app = a
        elif o in ("-c", "--config"):
            config_file = a
        elif o in ("-s", "--session"):
            session = a
        elif o in ("-o", "--output"):
            exp_dir = a
        else:
            pass

    if config_file and session:
        config = ConfigParser.ConfigParser()
        config.readfp(open(config_file))
    else:
        print "You must supply a configuration file and a session id.\n" + usage
        sys.exit(2)
    
    eh = export_xls(session, config)
    eh.export(app, exp_dir)
    #'''