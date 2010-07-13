#!/usr/bin/env python

import wx

class IPRStatsMenu(wx.MenuBar):
    """Main menu bar object used by iprstats.py"""
    
    def __init__(self, *args, **kwds):
        wx.MenuBar.__init__(self, *args, **kwds)

        # Override std wxMenuBar
        self.file = wx.Menu()
        self.open = wx.MenuItem(self.file, wx.ID_OPEN,
                                     "&Open...", "", wx.ITEM_NORMAL)
        self.open_session = wx.MenuItem(self.file, wx.NewId(),
                                     "Open session...", "", wx.ITEM_NORMAL)
        self.save_as = wx.MenuItem(self.file, wx.ID_SAVEAS,
                                     "Save as...", "", wx.ITEM_NORMAL)
        self.export_html = wx.MenuItem(self.file, wx.NewId(),
                                    "Export as &HTML...", "", wx.ITEM_NORMAL)
        self.export_xls = wx.MenuItem(self.file, wx.NewId(),
                                    "Export as &XLS...", "", wx.ITEM_NORMAL)
        self.properties = wx.MenuItem(self.file, wx.ID_PROPERTIES,
                                    "&Properties....", "", wx.ITEM_NORMAL)
        self.exit = wx.MenuItem(self.file, wx.ID_EXIT,
                                    "&Quit","", wx.ITEM_NORMAL)
        
        self.file.AppendItem(self.open)
        self.file.AppendItem(self.open_session)
        self.file.AppendItem(self.save_as)
        self.file.AppendItem(self.export_html)
        self.file.AppendItem(self.export_xls)
        self.save_as.Enable(False)
        self.export_html.Enable(False)
        self.export_xls.Enable(False)
        self.file.AppendItem(self.properties)
        self.file.AppendSeparator()
        self.file.AppendItem(self.exit)
        self.Append(self.file, "File")

        self.help = wx.Menu()
        self.about = wx.MenuItem(self.help, wx.ID_ABOUT,
                                      "&About", "", wx.ITEM_NORMAL)
        self.Append(self.help, "Help")
        self.help.AppendItem(self.about)
        
        self.__set_properties()
        self.__do_layout()
        
    def __set_properties(self):
        pass
    
    def __do_layout(self):
        pass