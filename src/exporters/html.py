#!/usr/bin/python
import os
import sys
import shutil

class export_html:
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
            shutil.copyfile('style.css', sout)
        else:
            print "Could not find style.css; Disabling HTML styling"
        
        # Export a single app or all apps
        for app in self.iprstat.settings.apps:
            self.export_page(app, directory=directory)
'''
if __name__ == '__main__':

    usage = "Usage: export_html.py -c <config_file> -s <session_id> [-a <db_application> -o <output_directory> -t <chart_type>]"
    app = None
    session = None
    config_file = None
    exp_dir = None
    chart_type = None
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],"h:a:c:s:o:",["help","app=","config=","session=","output=","chart="])
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
        elif o in ("--chart"):
            chart_type = a.lower()
        else:
            pass
    
    if config_file and session:
        config = ConfigParser.ConfigParser()
        config.readfp(open(config_file))
    else:
        print "You must supply a configuration file and a session id.\n" + usage
        sys.exit(2)
    
    eh = export_html(session, config)
    eh.export(app, exp_dir, chart=chart_type)
    #'''