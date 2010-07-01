#!/usr/bin/python
import xlwt

class export_xls:
    """Class for exporting IPRStatsData as a spreadsheet.
    
    Each application will be generated in its own worksheet.
    """
    
    def __init__(self, iprstatsdata):
        """Initialize the exporter with the initialized IPRStatsData object"""
        self.iprsdata = iprstatsdata
        self.apps = self.iprsdata.config.get('general','apps').\
                                    replace('\n',' ').split(', ')
        
    def _generate_sheet(self, app, xls_doc):
        """Generate a single worksheet with a single app
        
        app - app to create a worksheet for
        xls_doc - xlwt.Workbook object to append to
        """
        # Create the worksheet
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
        
        # Write a row to the spreadsheet for each row in iprstatsdata
        length = self.iprsdata.get_table_length(app)
        for r in range(length):
            row = self.iprsdata.get_one_row(app, r)
            if row:
                r += 1
                sheet.write(r, 0, str(row[0])) # Count
                sheet.write(r, 1, row[5])      # DB Name
                sheet.write(r, 2, row[1])      # DB ID
                sheet.write(r, 3, row[3])      # GO Name
                #                              # GO ID
                sheet.write(r, 5, row[2])      # DB URL
                sheet.write(r, 6, row[4])      # GO URL
                if len(row) == 7:
                    sheet.write(r, 7, row[6]) # GO Definition
            else:
                break
    
    def export(self, app=None, filename=None):
        """Exports IPRStatsData as a spreadsheet
        
        app - export only a single app (default: all)
        filename - save as file (default: iprstats.xls in current directory)
        """
        xls_doc = xlwt.Workbook()
        
        if app:
            self._generate_sheet(app, xls_doc)
        else:
            for app in self.apps:
                self._generate_sheet(app, xls_doc)
        
        if filename:
            xls_doc.save(filename)
        else:
            xls_doc.save('iprstats.xls')

'''
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