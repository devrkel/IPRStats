#!/usr/bin/env python

import wxversion
wxversion.select('2.8')
import wx.grid
import os
import sys
import webbrowser

from settings import Settings
from iprstatsdata import IPRStatsData
from standalone.frame import MainFrame
from standalone.properties import PropertiesDlg
from chart import Chart

from importers.iprxml import ParseXMLFile
from exporters.ips import export_ips
from exporters.html import export_html
from exporters.xls import export_xls

class IPRStats:
    """Top level application for calling GUI
    
    Handles menu actions, linking, and close events
    """
    
    def __init__(self, installed=False):
        """Initialize the top-level frame
        
        Initializes top-level grid, establishes a home directory,
        and reads in the configuration file.
        """
        app = wx.PySimpleApp(0)
        wx.InitAllImageHandlers()

        self.settings = Settings(installed=installed)
        self.iprstat = None
        
        self.mainframe = MainFrame(self.settings.getapps(), None, -1, "")
        
        # Bind events to the menu and open grid links in browser
        self.mainframe.Bind(wx.EVT_MENU, self.OnOpen,
                            self.mainframe.menu.open)
        self.mainframe.Bind(wx.EVT_MENU, self.OnOpenSession,
                            self.mainframe.menu.open_session)
        self.mainframe.Bind(wx.EVT_MENU, self.OnSaveAs,
                            self.mainframe.menu.save_as)
        self.mainframe.Bind(wx.EVT_MENU, self.OnExportHTML,
                            self.mainframe.menu.export_html)
        self.mainframe.Bind(wx.EVT_MENU, self.OnExportXLS,
                            self.mainframe.menu.export_xls)
        self.mainframe.Bind(wx.EVT_MENU, self.OnExit,
                            self.mainframe.menu.exit)
        self.mainframe.Bind(wx.EVT_MENU, self.OnProperties,
                            self.mainframe.menu.properties)
        self.mainframe.Bind(wx.EVT_MENU, self.OnAbout,
                            self.mainframe.menu.about)
        self.mainframe.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK,
                            self.OnCellLeftClick)
        
        app.SetTopWindow(self.mainframe)
        self.mainframe.Show()
        app.MainLoop()

    def OnOpen(self, event):
        """ Open an XML file
        
        Launches a file-chooser dialog for the user to select the
        InterProScan output XML file to be parsed.  Creates a working
        session id and an IPRStatsData object containing the parsed
        data.
        """
        dlg = wx.FileDialog(self.mainframe, "Choose a file",
                            self.settings.getexportdir(), "",
                            "XML (*.xml)|*.xml|View all files (*.*)|*.*",
                            wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            self.settings.setexportdir(dlg.GetDirectory())
            
            # Create a random ID and make a session folder on disk
            self.settings.newsession()
            
            # Pass the user-selected XML to the XML parser
            infile = os.path.join(self.settings.getexportdir(), filename)
            parsethread = ParseXMLFile(infile, self.settings)
            
            # Create a progress bar dialog and update it while the
            # XML file is still being parsed.
            dialog = wx.ProgressDialog( 'Progress', 'Opening ' +\
                                        filename +'...', maximum = 3 )
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
            self.mainframe.menu.save_as.Enable()
            self.mainframe.menu.export_html.Enable()
            self.mainframe.menu.export_xls.Enable()
        dlg.Destroy()
        
    def OnOpenSession(self, event):
        """Opens session previously saved by user
        
        A saved session .ips file is a .tar.bz2 compressed version of
        a standard session folder.  Extracts data and populates GUI.
        """
        dlg = wx.FileDialog(self.mainframe, "Choose a file",
                    self.settings.getexportdir(), "",
                    "IPRStats File (*.ips)|*.ips|View all files (*.*)|*.*",
                    wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
#            filename = dlg.GetFilename()
            self.settings.setexportdir(dlg.GetDirectory())
        dlg.Destroy()
    
    def OnSaveAs(self, event):
        """Saves the current session.
        
        Compresseses the current session folder into a .tar.bz2
        so that the user doesn't have to deal with parsing and querying
        an XML file every time.
        """
        dlg = wx.FileDialog(self.mainframe, "Save as file",
                            self.settings.getexportdir(),
                            "", "*.ips", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            self.settings.setexportdir(dlg.GetDirectory())
            ips = export_ips(self.settings.getsessiondir())
            ips.export(os.path.join(self.settings.getexportdir(), filename))
        dlg.Destroy()
    
    def OnExportHTML(self, event):
        """Exports current session as HTML
        
        Takes the parsed and queried data from an opened XML file
        and writes it as HTML.  Each app from InterProScan gets its
        own static HTML page.
        """
        dlg = wx.DirDialog(self.mainframe, "Choose a folder",
                           self.settings.getexportdir(), wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.settings.setexportdir(dlg.GetPath())
            html = export_html(self.iprstat)
            html.export(directory=self.settings.getexportdir())
        dlg.Destroy()
    
    def OnExportXLS(self, event):
        """Save current session as a spreadsheet
        
        Uses python-xlwt to write the parsed XML file as a spreadsheet file
        compatible with OpenOffice.org and Microsoft Excel
        """
        dlg = wx.FileDialog(self.mainframe, "Save as file",
                        self.settings.getexportdir(), "", "*.xls", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            self.settings.setexportdir(dlg.GetDirectory())
            if filename[-4:] != '.xls': filename += '.xls'
            xls = export_xls(self.iprstat.cache)
            xls.export(filename=os.path.join(
                                    self.settings.getexportdir(),
                                    filename))
        dlg.Destroy()
    
    def OnExit(self, event):
        """Closes the frame, any open files, and database connections. """
        #self.iprstat.close()
        self.mainframe.Close(True)
        
    def OnProperties(self, event):
        """Opens the properties dialog box so the user can change settings
        
        When the user clicks "OK" on the launched properties dialog,
        the settings are written to disk and the GUI table is refreshed.
        """
        dlg = PropertiesDlg(None, -1, 'Change Settings',
                            self.settings)
        if dlg.ShowModal() == wx.ID_OK:
            dlg.SaveProperties()
            for grid in self.mainframe.grids.values():
                try: grid.GetTable().Update()
                except AttributeError: pass
                
        dlg.Destroy()

    def OnAbout(self, event):
        """Displays an about box"""
        wx.AboutBox(self.mainframe.aboutinfo)
    
    def PopulateGUI(self):
        """Populates frame's form elements with information pulled from the
        XML file
        
        Creates an IPRStatsData object to contain the data and then
        populates the necessary grid and chart elements using the
        IPRStatsData object.
        """
        self.iprstat = IPRStatsData(self.settings)
        for app in self.settings.getapps():
            
            bitmap = self.iprstat.chart[app].GetChart()
            if bitmap:
                self.mainframe.charts[app].SetBitmap(bitmap)
                self.mainframe.charts[app].Show()
            else:
                self.mainframe.charts[app].Hide()

            self.mainframe.grids[app].GetTable().Update(self.iprstat.cache)
            self.mainframe.grids[app].AutoSizeColumns()
            self.mainframe.tabs[app].Fit()
    
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
            if col == 0:
                url = self.iprstat.cache.get_url(app, row)
            elif col == 2:
                url = self.iprstat.cache.get_url(app, row, True)
                
            if url != None:
                webbrowser.open(url)
        event.Skip()

if __name__ == "__main__":
    installed = False
    for arg in sys.argv:
        if arg == '-i': installed=True
        
    ipr = IPRStats(installed)
