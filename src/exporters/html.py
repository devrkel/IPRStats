#!/usr/bin/python
import os
import sys
import shutil

class page:
    '''Class for defining and outputting a single HTML page.
    
    A single HTML page can be created given a specific member database
    app and an IPRStatsData object.
    '''
    
    def __init__(self, app, iprstatsdata, directory=None, menu=None,
                chart_type=None, chart_gen=None, log=None):
        """Initialize a single HTML page
        
        Requires a specific app and an IPRStatsData object containing the
        data to be displayed in the HTML page.  Optional arguments include:
            directory - the output HTML directory, defaults to stdout
            menu - whether or not to display a menu on the page
            chart_gen - 'google' or 'pylab' charts?
            log - currently not used
        """
        self.app = app
        self.iprsdata = iprstatsdata
        self.directory = directory
        self.menu = menu
        self.chart_type = chart_type
        self.chart_gen = chart_gen
        self.log = log
    
    def chart(self, chart_data, chart_title, chart_filename,
              chart_type=None, chart_gen=None):
        """Saves a pie chart to the export directory
        
        chart_data of form [(label1, label2, ...), (value1, value2, ...)]
        chart_title - title to be displayed above the chart
        chart_filename - location to save the chart
        chart_type (optional) - 'google' or 'pylab'
        
        returns an HTML img tag or None
        """
        
        # For logging -- currently not being used
        if chart_type == 'google' and self.log:
            self.log.write('Downloading ' + chart_title + ' from Google Charts...\n')
            self.log.flush()
        elif chart_type == 'pylab' and self.log:
            self.log.write('Creating chart ' + chart_title + '...\n')
            self.log.flush()
            
        # Get chart from IPRStatsData object and create the img tag
        if self.iprsdata.get_chart(chart_data, chart_title, chart_filename,
                                   chart_type, chart_gen):
            img  = '<img'
            img += ' src="' + os.path.basename(chart_filename) + '"'
            img += ' alt="' + chart_title + '" />'
            return img
        else:
            return None
    
    # Generates a generic link object with link_name and link_url
    def link(self, link_name, link_url, target=None, link_title=None):
        """Create a string containing a generic html link
        
        link_name - the name of the link to be displayed to the user
        link_url - the website address of the link
        target - target window for the link to launch in;
                 "_blank", "_parent", "_self" (default), or "_top" 
        link_title - hover-over text of the link
        
        returns a string containing the link HTML
        """
        if not link_name:
            return ''
        
        link  = '<a href="' + link_url + '"'
        if target:
            link += ' target="' + target + '"'
        if link_title:
            link += ' title="' + link_title + '"'
        link += '>' + link_name + '</a>'

        return link
    
    def link_table(self, app, file):
        """Prints the HTML for a link table using iprstatsdata
        to the supplied handle.
        """
        
        # Create title row for the table
        print >> file, '<table cellspacing="0">'
        print >> file, '  <tr class="highlight"'
        print >> file, '    <th>Name</th>'
        print >> file, '    <th>Count</th>'
        print >> file, '    <th>Link</th>'
        print >> file, '  </tr>'
        
        # Create a table row for each row in IPRStatsData
        length = self.iprsdata.get_table_length(app)
        for r in range(length):
            row = self.iprsdata.get_one_row(app, r)
            if row:
                print >> file, '<tr>'
                print >> file, '<td>' + self.link(row[5], row[2], '_blank') + '</td>'
                print >> file, '<td>' + str(row[0]) + '</td>'
                print >> file, '<td>' + self.link(row[3],row[4],'_blank') + '</td>'
                print >> file, '</tr>'
            else:
                break

        print >> file, '</table>'
    
    def export(self):
        """Generate an HTML page using the info supplied at initialization"""
        
        # Ignore for now, not using a log
        if self.log:
            self.log.write("Creating page " + self.app.lower() + ".html...\n")
            self.log.flush()
        
        # Use the supplied export directory or default to sys.stdout
        if self.directory:
            f = open(os.path.join(self.directory, self.app.lower()+'.html'),'w')
        else:
            f = sys.stdout
        
        # Begin downloading the chart before generating page HTML
        counts = self.iprsdata.get_counts(self.app)
        if self.directory: chart_filename = os.path.join(self.directory, self.app.lower()+'_matches.png')
        else: chart_filename = self.app.lower()+'_matches.png'
        chart = self.chart(counts, self.app+' Matches', chart_filename,
                           self.chart_type, self.chart_gen)

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
        print >> f,      self.menu
        print >> f, '    <div id="content">'
        
        # If a chart was generated, print the HTML img tag
        if chart:
            print >> f,   chart
            
        # Generate the link table
        self.link_table(self.app, f)
        
        # Print the standard footer for each page
        print >> f, '    </div>'
        print >> f, '   </div>'
        print >> f, '   <div id="footer">'
        print >> f, '   </div>'
        print >> f, '  </div>'
        print >> f, ' </body>'
        print >> f, '</html>'

        f.close()

class export_html:
    """Class for exporting all pages at one time"""
    
    def __init__(self, iprstatsdata):
        """Initialize the object with the required IPRStatsData object"""
        self.iprsdata = iprstatsdata
        self.apps = self.iprsdata.config.get('general','apps').replace('\n',' ').split(', ')
    
    def _generate_link(self, link_name, link_url, target=None, link_title=None):
        """Create a string containing a generic html link
        
        link_name - the name of the link to be displayed to the user
        link_url - the website address of the link
        target - target window for the link to launch in;
                 "_blank", "_parent", "_self" (default), or "_top" 
        link_title - hover-over text of the link
        
        returns a string containing the link HTML
        """
        
        link = '<a href="'+link_url+'"'
        if target:
            link += ' target="' + target + '"'
        if link_title:
            link += ' title="' + link_title + '"'
        link += '>' + link_name + '</a>'
        return link
    
    def _generate_menu(self, menu_links, current_page=None, menu_id=None):
        """Generate a list of links to be styled with CSS into a menu
        
        Requires a list of links of form [(title1, url1), (title2, url2), ...]
        current_page - if specified, will add class="selected" to that link
        menu_id - list id for identification and styling
        """
        
        menu = '<ul class="menu"'
        if menu_id:
            menu += ' id="'+menu_id+'"'
            
        for name, url in menu_links:
            menu += '<li'
            if name == current_page or url == current_page:
                menu += ' class="selected"'
            menu += '>' + self._generate_link(name, url) + '</li>'
        menu += '</ul>'
            
        return menu
    
    def export(self, app=None, directory=None, chart_type=None,
               chart_gen=None, log=None):
        """Export all or a single page as HTML
        
        app - used to limit export to a single page
        directory - HTML output directory (default=sys.stdout)
        chart - 'google', 'pylab', or None
        log - not currently being used
        """
        
        # Copy the static CSS to the export directory to style the HTML
        sout = os.path.join(directory, 'style.css')
        if directory and \
            os.path.exists(os.path.join(os.getcwd(), 'style.css')):
            shutil.copyfile('style.css', sout)
        elif os.path.exists(os.path.join('/usr/share/pyshared/iprstats',
                                         'style.css')):
            shutil.copyfile('/usr/share/pyshared/iprstats/style.css', sout)
        else:
            print "Could not find style.css; Disabling HTML styling"
        
        # Export a single app or all apps
        if app:
            p = page(app, directory, chart_type=chart_type,
                     chart_gen=chart_gen, log=log)
            p.export()
        else:
            links = []
            for app in self.apps:
                links.append((app, app.lower() + '.html'))
            menu = self._generate_menu(links, menu_id='navigation')
            for app in self.apps:
                p = page(app, self.iprsdata, directory=directory, menu=menu,
                         chart_type=chart_type, chart_gen=chart_gen, log=log)
                p.export()
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