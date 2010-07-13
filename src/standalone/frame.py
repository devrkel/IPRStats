import wxversion
wxversion.select('2.8')
import wx.grid

from standalone.menu import IPRStatsMenu
from standalone.about import IPRStatsAbout
from standalone.table import LinkTable

class MainFrame(wx.Frame): 
    """Top level frame
    
    Handles menu actions, linking, and close events
    """
    def __init__(self, apps, *args, **kwds):
        """Initialize the top-level frame
        
        Initializes top-level grid, establishes a home directory,
        and reads in the configuration file.
        """
        
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        
        self.database_results = wx.Listbook(self, -1, style=wx.BK_LEFT)
        
        self.apps = apps
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
            self.grids[app].SetTable(LinkTable(app), True)
            
        # Menu
        self.menu = IPRStatsMenu()
        self.SetMenuBar(self.menu)
        
        # About information
        self.aboutinfo = IPRStatsAbout()
        

        self.__set_properties()
        self.__do_layout()

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