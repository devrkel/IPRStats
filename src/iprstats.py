#!/usr/bin/env python

import wxversion
wxversion.select('2.8')
import wx.grid
import string
import os
import sys
import ConfigParser
import platform
import webbrowser
import tempfile
import shutil
from random import choice

from iprstatsdata import IPRStatsData
from standalone.menu import IPRStatsMenu
from standalone.about import IPRStatsAbout
from standalone.properties import PropertiesDlg
from standalone.table import LinkTable

from importers.iprxml import ParseXMLFile
from exporters.ips import export_ips
from exporters.html import export_html
from exporters.xls import export_xls

try:
    from win32com.shell import shellcon, shell            
    homedir = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
except ImportError:
    homedir = os.path.expanduser("~")

class IPRStats_Frame(wx.Frame):
    """Top level frame
    
    Handles menu actions, linking, and close events:
      OnOpen(self, event)
      OnOpenSession(self, event)
      OnSaveAs(self, event)
      OnExportHTML(self, event)
      OnExportXLS(self, event)
      OnExit(self, event)
      OnProperties(self, event)
      OnAbout(self, event)
      OnCellLeftClick(self, event)
      OnPopulateGUI(self)
    """
    def __init__(self, *args, **kwds):
        """Initialize the tople-level frame
        
        Initializes top-level grid, establishes a home directory,
        and reads in the configuration file.
        """
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        
        # Create the settings directory if one doesn't exist;
        # If we fail to use the default settings directory (i.e.
        # webserver, use /tmp)
        self.iprsdir = os.path.join(homedir, '.iprstats')
        if not os.path.exists(self.iprsdir):
            try: os.mkdir(self.iprsdir)
            except:
                try:
                    self.iprsdir = os.path.join(os.getcwd(),'.iprstats')
                    os.mkdir(self.iprsdir)
                except: self.iprsdir = tempfile.gettempdir()
        
        # Open and parse settings file
        self.configpath = os.path.join(self.iprsdir,'iprstats.cfg')
        if platform.system() == 'Windows':
            pymodpath = os.path.join(sys.prefix, 'Lib', 'site-packages',
                                     'iprstats', 'iprstats.cfg.example')
        else:
            pymodpath = os.path.join(sys.prefix, 'share', 'pyshared',
                                     'iprstats', 'iprstats.cfg.example')
        if not os.path.exists(self.configpath):
            if os.path.exists('iprstats.cfg.example'):
                shutil.copyfile('iprstats.cfg.example', self.configpath)
            elif os.path.exists(pymodpath):
                shutil.copyfile(pymodpath, self.configpath)
            else:
                print "iprstats: error: config file could not be found"
                sys.exit(2)
        self.config = ConfigParser.ConfigParser()
        configfile = open(self.configpath, 'r')
        self.config.readfp(configfile)
        configfile.close()
        
        # Apps setting isn't implemented yet in GUI form, 
        self.apps = self.config.get('general','apps').replace('\n',' ')
        self.apps = self.apps.split(', ')
        
        # Keep track of current session and open directory
        self.session = None
        self.dirname = ''
        self.database_results = wx.Listbook(self, -1, style=wx.NB_LEFT)
        self.iprstat = None

        self.tabs = {}
        self.charts = {}
        self.grids = {}

        # Create a tab, image, and grid for each app
        for app in self.apps:
            self.tabs[app] = wx.Panel(self.database_results, -1,
                                      style=wx.TAB_TRAVERSAL)
            self.charts[app] = wx.StaticBitmap(self.tabs[app], -1)
            self.charts[app].Hide()
            self.grids[app] = wx.grid.Grid(self.tabs[app], -1, size=(1, 1), name=app)
            
        # Menu
        self.menu = IPRStatsMenu()
        self.SetMenuBar(self.menu)
        
        # About information
        self.aboutinfo = IPRStatsAbout()
        

        self.__set_properties()
        self.__do_layout()

        # Bind events to the menu and open grid links in browser
        self.Bind(wx.EVT_MENU, self.OnOpen, self.menu.open)
        self.Bind(wx.EVT_MENU, self.OnOpenSession, self.menu.open_session)
        self.Bind(wx.EVT_MENU, self.OnSaveAs, self.menu.save_as)
        self.Bind(wx.EVT_MENU, self.OnExportHTML, self.menu.export_html)
        self.Bind(wx.EVT_MENU, self.OnExportXLS, self.menu.export_xls)
        self.Bind(wx.EVT_MENU, self.OnExit, self.menu.exit)
        self.Bind(wx.EVT_MENU, self.OnProperties, self.menu.properties)
        self.Bind(wx.EVT_MENU, self.OnAbout, self.menu.about)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnCellLeftClick)

    def __set_properties(self):
        self.SetTitle("IPRStats")
        self.SetSize((740, 600))

        for app in self.apps:
            self.charts[app].SetSize((1,1))
            self.grids[app].CreateGrid(0, 3)
            self.grids[app].SetColLabelValue(0, "Name")
            self.grids[app].SetColLabelValue(1, "Count")
            self.grids[app].SetColLabelValue(2, "Link")
            self.grids[app].SetRowLabelSize(0)
            self.grids[app].SetColSize(0,250)
            self.grids[app].SetColSize(1,150)
            self.grids[app].SetColSize(2,280)
            self.tabs[app].SetBackgroundColour('white')

    def __do_layout(self):
        main_sizer = wx.FlexGridSizer(1, 1, 0, 0)
        for app in self.apps:
            sizer = wx.FlexGridSizer(2, 1, 0, 0)
            sizer.Add(self.charts[app], 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
            sizer.Add(self.grids[app], 1, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 0)
            self.tabs[app].SetSizer(sizer)
            self.database_results.AddPage(self.tabs[app], app)
            sizer.AddGrowableRow(1)
            sizer.AddGrowableCol(0)
        main_sizer.AddGrowableRow(0)
        main_sizer.AddGrowableCol(0)
        main_sizer.Add(self.database_results, 0, wx.EXPAND, 0)
        self.SetSizer(main_sizer)
        self.Layout()
        self.SetSize((840, 600))

    def OnOpen(self, event):
        """ Open an XML file
        
        Launches a file-chooser dialog for the user to select the
        InterProScan output XML file to be parsed.  Creates a working
        session id and an IPRStatsData object containing the parsed
        data.
        """
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "XML (*.xml)|*.xml|View all files (*.*)|*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            
            # Create a random ID and make a session folder on disk
            chars = string.letters + string.digits
            self.session = ''.join([choice(chars) for i in xrange(8)])
            self.sessiondir = os.path.join(self.iprsdir, self.session)
            os.mkdir(self.sessiondir)
            
            # Pass the user-selected XML to the XML parser
            infile = os.path.join(self.dirname, self.filename)
            parsethread = ParseXMLFile(infile, self.session,
                                       self.config, self.sessiondir)
            
            # Create a progress bar dialog and update it while the
            # XML file is still being parsed.
            dialog = wx.ProgressDialog( 'Progress', 'Opening ' +\
                                        self.filename +'...', maximum = 3 )
            parsethread.start()
            while parsethread.isAlive():
                wx.Sleep(0.1)
                dialog.Update(1, "Parsing XML file...")
            parsethread.join()
            
            # Query the data parsed by the XML parser and populate
            # the GUI with it. Update the progress bar dialog.
            dialog.Update(2, "Retrieving parsed data...")
            self.PopulateGUI()
            dialog.Update(3, "Done!")
            dialog.Destroy()
            
            # Enable previously disabled menu items.
            self.menu.export_html.Enable()
            self.menu.export_xls.Enable()
        dlg.Destroy()
        
    def OnOpenSession(self, event):
        """Opens session previously saved by user
        
        A saved session .ips file is a .tar.bz2 compressed version of
        a standard session folder.  Extracts data and populates GUI.
        """
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "",
                    "IPRStats File (*.ips)|*.ips|View all files (*.*)|*.*",
                    wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
        dlg.Destroy()
    
    def OnSaveAs(self, event):
        """Saves the current session.
        
        Compresseses the current session folder into a .tar.bz2
        so that the user doesn't have to deal with parsing and querying
        an XML file every time.
        """
        dlg = wx.FileDialog(self, "Save as file", self.dirname, "", "*.ips", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            ips = export_ips(self.sessiondir)
            ips.export(os.path.join(self.dirname, self.filename))
        dlg.Destroy()
    
    def OnExportHTML(self, event):
        """Exports current session as HTML
        
        Takes the parsed and queried data from an opened XML file
        and writes it as HTML.  Each app from InterProScan gets its
        own static HTML page.
        """
        dlg = wx.DirDialog(self, "Choose a folder", self.dirname, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.dirname = dlg.GetPath()
            html = export_html(self.iprstat)
            html.export(directory=self.dirname,
                        chart_type=self.config.get('general','chart_type'),
                        chart_gen=self.config.get('general','chart_gen'))
        dlg.Destroy()
    
    def OnExportXLS(self, event):
        """Save current session as a spreadsheet
        
        Uses python-xlwt to write the parsed XML file as a spreadsheet file
        compatible with OpenOffice.org and Microsoft Excel
        """
        dlg = wx.FileDialog(self, "Save as file", self.dirname, "", "*.xls", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            if self.filename[-4:] != '.xls': self.filename += '.xls'
            xls = export_xls(self.iprstat)
            xls.export(filename=os.path.join(self.dirname, self.filename))
        dlg.Destroy()
    
    def OnExit(self, event):
        """Closes the frame, any open files, and database connections. """
        #self.iprstat.close()
        self.Close(True)
        
    def OnProperties(self, event):
        """Opens the properties dialog box so the user can change settings
        
        When the user clicks "OK" on the launched properties dialog,
        the settings are written to disk and the GUI table is refreshed.
        """
        dlg = PropertiesDlg(None, -1, 'Change Settings', self.config)
        if dlg.ShowModal() == wx.ID_OK:
            dlg.SaveProperties()
            configfile = open(self.configpath, 'w')
            self.config.write(configfile)
            configfile.close
            configfile = open(self.configpath,'r')
            self.config.readfp(configfile)
            configfile.close()
            for grid in self.grids.values():
                    try: grid.GetTable().Update()
                    except AttributeError: pass
                
        dlg.Destroy()

    def OnAbout(self, event):
        """Displays an about box"""
        wx.AboutBox(self.aboutinfo)
    
    def PopulateGUI(self):
        """Populates frame's form elements with information pulled from the
        XML file
        
        Creates an IPRStatsData object to contain the data and then
        populates the necessary grid and chart elements using the
        IPRStatsData object.
        """
        self.iprstat = IPRStatsData(self.session, self.config)
        for app in self.apps:
            
            counts = self.iprstat.get_counts(app)
            chart_filename = os.path.join(self.sessiondir,app.lower()+'_matches.png')

            if self.iprstat.get_chart(counts, app+' Matches', chart_filename,
                                    chart_type=self.config.get('general', 'chart_type'),
                                    chart_gen=self.config.get('general','chart_gen')):
                chart_img = wx.Bitmap(chart_filename, wx.BITMAP_TYPE_ANY)
                self.charts[app].SetBitmap(chart_img)
                self.charts[app].SetMinSize(chart_img.GetSize())
                self.charts[app].Show()
            else:
                self.charts[app].Hide()

            self.grids[app].SetTable(LinkTable(app, self.iprstat), True)
            self.grids[app].AutoSizeColumns()
            self.tabs[app].Fit()
    
    def OnCellLeftClick(self, event):
        """Launches web browser when user clicks on certain grid cells
        
        Retrieves the correct URL from the IPRStatsData object and
        launches the user's default web browser.
        """
        grid = event.GetEventObject()
        value = grid.GetCellValue(event.GetRow(), event.GetCol())
        if event.GetCol() != 1 and value != "None":
            app = grid.GetName()
            row = event.GetRow()
            col = event.GetCol()
            print row
            if col == 0:
                url = self.iprstat.get_link(app, row)
            elif col == 2:
                url = self.iprstat.get_link(app, row, True)
                
            if url != None:
                webbrowser.open(url)
        event.Skip()

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    iprstats_frame = IPRStats_Frame(None, -1, "")
    app.SetTopWindow(iprstats_frame)
    iprstats_frame.Show()
    app.MainLoop()
