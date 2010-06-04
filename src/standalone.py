#!/usr/bin/env python
# -*- coding: utf-8 -*-
# generated by wxGlade 0.6.3 on Wed May 26 10:32:35 2010

import string, os, wx, wx.grid
from ebixml import EBIXML
from iprstatsdata import IPRStatsData
from export_html import export_html
from export_xls import export_xls
import ConfigParser
from random import choice
from xml.sax import ContentHandler
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces

# begin wxGlade: extracode
# end wxGlade



class IPSStats_Frame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MetaIPS_Frame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.apps = ['PFAM', 'PIR', 'GENE3D', 'HAMAP', 'PANTHER', 'PRINTS',
                    'PRODOM','PROFILE', 'PROSITE', 'SMART', 'SUPERFAMILY', 'TIGRFAMs']

        self.config = ConfigParser.ConfigParser()
        self.config.readfp(open('iprstats.cfg'))
        if not os.path.exists('.session'): os.mkdir('.session')
        self.session = None
        self.database_results = wx.Notebook(self, -1, style=wx.NB_LEFT)

        self.tabs = {}
        self.charts = {}
        self.grids = {}

        for app in self.apps:
            self.tabs[app] = wx.ScrolledWindow(self.database_results, -1, style=wx.TAB_TRAVERSAL)
            self.charts[app] = wx.BitmapButton(self.tabs[app], -1)
            self.grids[app] = wx.grid.Grid(self.tabs[app], -1, size=(1, 1))
        
        # Menu Bar
        self.metaips_menu = wx.MenuBar()

        self.file_item = wx.Menu()
        self.open_item = wx.MenuItem(self.file_item, wx.ID_OPEN, "&Open...", "", wx.ITEM_NORMAL)
        self.export_html_item = wx.MenuItem(self.file_item, wx.NewId(), "Export as &HTML...", "", wx.ITEM_NORMAL)
        self.export_xls_item = wx.MenuItem(self.file_item, wx.NewId(), "Export as &XLS...", "", wx.ITEM_NORMAL)
        self.exit_item = wx.MenuItem(self.file_item, wx.ID_EXIT, "&Quit", "", wx.ITEM_NORMAL)
        self.file_item.AppendItem(self.open_item)
        self.file_item.AppendItem(self.export_html_item)
        self.file_item.AppendItem(self.export_xls_item)
        self.file_item.AppendSeparator()
        self.file_item.AppendItem(self.exit_item)
        self.metaips_menu.Append(self.file_item, "File")

        self.options_item = wx.Menu()
        self.use_go_lookup_item = wx.MenuItem(self.options_item, wx.NewId(), "Use &GO lookup", "", wx.ITEM_CHECK)
        self.db_settings_item = wx.MenuItem(self.options_item, wx.ID_PROPERTIES, "&Database settings....", "", wx.ITEM_NORMAL)
        self.options_item.AppendItem(self.use_go_lookup_item)
        self.options_item.AppendItem(self.db_settings_item)
        self.metaips_menu.Append(self.options_item, "Options")

        self.help_item = wx.Menu()
        self.about_item = wx.MenuItem(self.help_item, wx.ID_ABOUT, "&About", "", wx.ITEM_NORMAL)
        self.metaips_menu.Append(self.help_item, "Help")
        self.help_item.AppendItem(self.about_item)
        self.SetMenuBar(self.metaips_menu)
        # Menu Bar end

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_MENU, self.OnOpen, self.open_item)
        self.Bind(wx.EVT_MENU, self.OnExportHTML, self.export_html_item)
        self.Bind(wx.EVT_MENU, self.OnExportXLS, self.export_xls_item)
        self.Bind(wx.EVT_MENU, self.OnExit, self.exit_item)
        self.Bind(wx.EVT_MENU, self.OnAbout, self.about_item)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MetaIPS_Frame.__set_properties
        self.SetTitle("Meta IPS")
        self.SetSize((800, 600))

        for app in self.apps:
            self.charts[app].SetMinSize((730, 300))
            self.grids[app].CreateGrid(0, 2)
            self.grids[app].SetColLabelValue(0, "Count")
            self.grids[app].SetColLabelValue(1, "Link")
            self.grids[app].SetRowLabelSize(300)
            self.tabs[app].SetScrollRate(10, 10)
        self.database_results.SetMinSize((490, 511))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MetaIPS_Frame.__do_layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        for app in self.apps:
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(self.charts[app], 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ADJUST_MINSIZE, 0)
            sizer.Add(self.grids[app], 1, wx.EXPAND, 0)
            self.tabs[app].SetSizer(sizer)
            self.database_results.AddPage(self.tabs[app], app)
        main_sizer.Add(self.database_results, 0, wx.EXPAND, 0)
        self.SetSizer(main_sizer)
        self.Layout()
        self.SetSize((800, 600))
        # end wxGlade

    def OnAbout(self, event): # wxGlade: MetaIPS_Frame.<event_handler>
        print "Event handler `OnAbout' not implemented"
        event.Skip()

    def OnOpen(self, event): # wxGlade: MetaIPS_Frame.<event_handler>
        """ Open a file"""
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.out", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            self.ParseFile(os.path.join(self.dirname, self.filename))
            self.PopulateGUI()
        dlg.Destroy()
    
    def OnExportHTML(self, event): # wxGlade: MetaIPS_Frame.<event_handler>
        """ Open a file"""
        self.dirname = ''
        dlg = wx.DirDialog(self, "Choose a folder", self.dirname, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.dirname = dlg.GetPath()
            html = export_html(self.session, self.config)
            html.export(directory=self.dirname)
        dlg.Destroy()
    
    def OnExportXLS(self, event): # wxGlade: MetaIPS_Frame.<event_handler>
        """ Open a file"""
        self.dirname = ''
        dlg = wx.DirDialog(self, "Choose a folder", self.dirname, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.dirname = dlg.GetPath()
            xls = export_xls(self.session, self.config)
            xls.export(directory=self.dirname)
        dlg.Destroy()
    
    def OnExit(self, event):
        # via wx.EVT_CLOSE event, also triggers exit dialog
        self.Close(True)
    
    def ParseFile(self, filename):
        # Create a parser
        parser = make_parser()
        parser.setFeature(feature_namespaces, 0)
        
        # Create a random ID
        chars = string.letters + string.digits
        self.session = ''.join([choice(chars) for i in xrange(8)])
        session_dir = os.path.join('.session', self.session)
        os.mkdir(session_dir)

        # Create the Handler
        exh = EBIXML(self.session, config=self.config, outfile=open(os.path.join(session_dir, self.session+'.sql'),"w"))

        # Parse file into DB
        parser.setContentHandler(exh)
        parser.parse(filename)
        del parser
    
    def PopulateGUI(self):
        ipsstat = IPRStatsData(self.session, self.config)
        for app in self.apps:
            ipsstat.init_match_data(app)
            
            counts = ipsstat.get_counts(app)
            chart_filename = os.path.join('.session',self.session,app.lower()+'_matches.png')
            if ipsstat.get_chart(counts, app+' Matches', chart_filename, False):
                self.charts[app].SetBitmapLabel(wx.Bitmap(chart_filename, wx.BITMAP_TYPE_ANY))
                
            r = 0
            current_name = ''
            while True:
                row = ipsstat.get_link_data_row()
                if not row:
                    break

                if row[0] != current_name:
                    current_name = row[0]
                    self.grids[app].AppendRows()
                    self.grids[app].SetRowLabelValue(r, row[0])
                    self.grids[app].SetCellValue(r, 0, str(row[2]))
                    self.grids[app].SetCellValue(r, 1, str(row[1]))
                    r += 1
                self.grids[app].AppendRows()
                self.grids[app].SetRowLabelValue(r, '')
                self.grids[app].SetCellValue(r, 0, str(row[3]))
                self.grids[app].SetCellValue(r, 1, str(row[4]))
                
                r += 1;
            
# end of class MetaIPS_Frame

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    metaips_frame = IPSStats_Frame(None, -1, "")
    app.SetTopWindow(metaips_frame)
    metaips_frame.Show()
    app.MainLoop()
