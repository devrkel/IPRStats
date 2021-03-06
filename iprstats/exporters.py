#!/usr/bin/python
import os
import sys
import shutil

class html:
    """Class for exporting all pages at one time"""
    
    def __init__(self, iprstatsdata):
        """Initialize the object with the required cache object"""
        self.iprstat = iprstatsdata
    
    def __get_link__(self, link_name, link_url, target=None, link_title=None):
        """Create a string containing a generic html link
        
        link_name - the name of the link to be displayed to the user
        link_url - the website address of the link
        target - target window for the link to launch in;
        "_blank", "_parent", "_self" (default), or "_top" 
        link_title - hover-over text of the link
        
        returns a string containing the link HTML
        """
        
        link = '<a href="' + str(link_url) + '"'
        if target:
            link += ' target="' + target + '"'
        if link_title:
            link += ' title="' + link_title + '"'
        link += '>' + str(link_name) + '</a>'
        return link
    
    def __get_menu__(self, menu_links, current_page=None, menu_id=None):
        """Generate an HTML list of links to be styled with CSS into a menu
        
        Requires a list of links of form [(title1, url1), (title2, url2), ...]
        current_page - if specified, will add class="selected" to that link
        menu_id - list id for identification and styling
        """
        
        menu = '<ul class="menu"'
        if menu_id:
            menu += ' id="' + menu_id + '"'
            
        for name, url in menu_links:
            menu += '<li'
            if name == current_page or url == current_page:
                menu += ' class="selected"'
            menu += '>' + self.__get_link__(name, url) + '</li>'
        menu += '</ul>'
            
        return menu
    
    def __get_chart__(self, app, directory=None):
        """Saves the application chart to the given directory
        
        chart_data of form [(label1, label2, ...), (value1, value2, ...)]
        chart_title - title to be displayed above the chart
        chart_filename - location to save the chart
        chart_type (optional) - 'google' or 'pylab'
        
        Returns: an HTML img tag (str) or None
        """
        
        if directory:
            # Get chart from cache and create the img tag
            chart = self.iprstat.chart[app]
            filename = os.path.join(directory,app.lower()+'_matches.png')
            
            if os.path.exists(chart.GetFilename()):
                shutil.copy(chart.GetFilename(), filename)
            elif chart.Save(filename):
                pass
            else:
                return ''
            
            img  = '<img'
            img += ' src="' + os.path.basename(filename) + '"'
            img += ' alt="' + app + ' Matches" />'
            return img
        else:
            return ''
    
    def __get_table__(self, app, file):
        """Prints the generated link table to the supplied handle
        using the cache object for data.
        """
        
        # Create title row for the table
        print >> file, '<table cellspacing="0">'
        print >> file, '  <tr class="highlight"'
        print >> file, '    <th>Name</th>'
        print >> file, '    <th>Count</th>'
        print >> file, '    <th>Link</th>'
        print >> file, '  </tr>'
        
        # Create a table row for each row in the cache
        length = self.iprstat.cache.get_match_length(app)
        for r in range(length):
            row = self.iprstat.cache.get_one_row(app, r)
            if row:
                print >> file, '<tr>'
                print >> file, '<td>'
                print >> file, self.__get_link__(row[0],
                                    self.iprstat.cache.get_url(app, r),
                                    '_blank')
                print >> file, '</td>'
                print >> file, '<td>' + str(row[1]) + '</td>'
                print >> file, '<td>'
                
                if self.iprstat.settings.usegolookup(): cell3 = row[4]
                else: cell3 = row[2]
                print >> file, self.__get_link__(cell3,
                                    self.iprstat.cache.get_url(app, r, True),
                                    '_blank')
                
                print >> file, '</td>'
                print >> file, '</tr>'
            else:
                break

        print >> file, '</table>'
    
    def export_page(self, app, directory=None):
        """Export an HTML page using the cache from initialization
        
           app - specific app to export
           directory - output directory or sys.stdout if None
        """
        
        # Use the supplied export directory or default to sys.stdout
        if directory:
            f = open(os.path.join(directory, app.lower()+'.html'),'w')
        else:
            f = sys.stdout

        # Standard header for each page
        print >> f, '<html xmlns="http://www.w3.org/1999/xhtml">'
        print >> f, ' <head>'
        print >> f, '  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />'
        print >> f, '  <title>IPRStats Results</title>'
        print >> f, '  <link href="style.css" rel="stylesheet" type="text/css" />'
        print >> f, ' </head>'
        print >> f, ' <body>'
        print >> f, '  <div id="container">'
        print >> f, '   <div id="header">'
        print >> f, '    <h1>IPRStats</h1>'
        print >> f, '    <ul id="tabs">'
        print >> f, '    </ul>'
        print >> f, '   </div>'
        
        # Print the given menu and content of the page
        print >> f, '   <div id="middlesec">'
        
        links = [(item, item.lower() + '.html')
                 for item in self.iprstat.settings.apps]
        print >> f,      self.__get_menu__(links, menu_id='navigation')
        
        print >> f, '    <div id="content">'
        
        # If a chart was generated, print the HTML img tag
        print >> f, self.__get_chart__(app, directory)
            
        # Generate the link table
        self.__get_table__(app, f)
        
        # Print the standard footer for each page
        print >> f, '    </div>'
        print >> f, '   </div>'
        print >> f, '   <div id="footer">'
        print >> f, '   </div>'
        print >> f, '  </div>'
        print >> f, ' </body>'
        print >> f, '</html>'

        f.close()
    
    def export(self, directory=None):
        """Export all pages as HTML
        
        directory - HTML output directory (default=sys.stdout)
        """
        
        # Copy the static CSS to the export directory to style the HTML
        sout = os.path.join(directory, 'style.css')
        sin = os.path.join(self.iprstat.settings.getinstalldir(), 'style.css')
        if directory and os.path.exists(sin):
            shutil.copyfile(sin, sout)
        else:
            print "Could not find style.css; Disabling HTML styling"
        
        # Export a single app or all apps
        for app in self.iprstat.settings.apps:
            self.export_page(app, directory=directory)


import xlwt

class xls:
    """Class for exporting IPRStatsData as a spreadsheet.
    
    Each application will be generated in its own worksheet.
    """
    
    def __init__(self, cache):
        """Initialize the exporter with the initialized IPRStatsData object"""
        self.cache = cache
        
    def __generate_sheet__(self, app, xls_doc):
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
        length = self.cache.get_match_length(app)
        for r in range(length):
            row = self.cache.get_one_row(app, r)
            if row:
                sheet.write(r+1, 0, str(row[1])) # Count
                sheet.write(r+1, 1, row[0])      # DB Name
                sheet.write(r+1, 2, row[3])      # DB ID
                sheet.write(r+1, 3, row[4])      # GO Name
                sheet.write(r+1, 4, row[2])      # GO ID
                sheet.write(r+1, 5, self.cache.get_url(app, r)) # DB URL
                sheet.write(r+1, 6, self.cache.get_url(app, r, True))#GO URL
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
            self.__generate_sheet__(app, xls_doc)
        else:
            for app in self.cache.settings.getapps():
                self.__generate_sheet__(app, xls_doc)
        
        if filename:
            xls_doc.save(filename)
        else:
            xls_doc.save('iprstats.xls')


import tarfile

class ips:
    """Class used to save a session
    
       This class zips the session directory into
       a tar.bz2 so that it can be unzipped and opened
       later or on a different machine.
    """
    
    def __init__(self, sessiondir):
        """Initialize with session directory to save"""
        self.sessiondir = sessiondir
    
    def export(self, outputdir):
        """Save session directory to outputdir file"""
        
        # Add .ips as the extention if left off
        if outputdir[-4:] != '.ips':
            outputdir += '.ips'
        
        # Package the session directory as a .tar.bz2 file
        tar = tarfile.open(outputdir,'w:bz2')
        tar.add(self.sessiondir, os.path.basename(self.sessiondir))
        tar.close()