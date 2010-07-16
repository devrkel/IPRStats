#!/usr/bin/env python

import wxversion
wxversion.select('2.8')
import wx
import wx.grid as gridlib
import sys


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
        
        self.apps = apps
        self.tabbook = TabBook(self, self.apps)
        
        '''
        self.database_results = wx.Listbook(self, -1, style=wx.BK_LEFT)
        
        self.apps = apps
        self.tabs = {}
        self.charts = {}
        self.grids = {}

        # Create a tab, image, and grid for each app
        for app in self.apps:
            self.tabs[app] = wx.Panel(self.database_results, -1)
            self.charts[app] = wx.StaticBitmap(self.tabs[app], -1)
            self.charts[app].Hide()
            self.grids[app] = gridlib.Grid(self.tabs[app], -1, size=(1, 1),
                                           name=app)
            self.grids[app].SetTable(LinkTable(app), True)
        '''
            
        # Menu
        self.menu = Menu()
        self.SetMenuBar(self.menu)
        
        # About information
        self.aboutinfo = About()

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetTitle("IPRStats")
        self.SetSize((740, 600))
        '''
        for app in self.apps:
            self.charts[app].SetSize((1,1))
            self.grids[app].SetRowLabelSize(0)
            self.grids[app].SetColSize(0,250)
            self.grids[app].SetColSize(1,150)
            self.grids[app].SetColSize(2,280)
            self.tabs[app].SetBackgroundColour('white')
        '''

    def __do_layout(self):
        main_sizer = wx.FlexGridSizer(1, 1, 0, 0)
        '''
        for app in self.apps:
            sizer = wx.FlexGridSizer(2, 1, 0, 0)
            sizer.Add(self.charts[app], 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
            sizer.Add(self.grids[app], 1,
                      wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 0)
            self.tabs[app].SetSizer(sizer)
            self.database_results.AddPage(self.tabs[app], app)
            sizer.AddGrowableRow(1)
            sizer.AddGrowableCol(0)
        '''
        main_sizer.AddGrowableRow(0)
        main_sizer.AddGrowableCol(0)
        main_sizer.Add(self.tabbook, 0, wx.ALL|wx.EXPAND, 0)
        self.SetSizer(main_sizer)
        self.Layout()
        self.SetSize((840, 600))

class TabPanel(wx.Panel):
    """Custom wx.Panel containing a chart and table.
    """
    
    def __init__(self, parent, app):
        """Initialize with a parent (Listbook) object and its
           specified app.
        """
        wx.Panel.__init__(self, parent, -1)
        
        self.app = app
        self.chart = wx.StaticBitmap(self, -1)
        self.chart.Hide()
        self.grid = gridlib.Grid(self, -1, size=(1, 1), name=app)
        self.grid.SetTable(LinkTable(app), True)
        
        self.__set_properties()
        self.__do_layout()
    
    def __set_properties(self):
        self.SetBackgroundColour('white')
        self.chart.SetSize((1,1))
        self.grid.SetRowLabelSize(0)
        self.grid.SetColSize(0,250)
        self.grid.SetColSize(1,150)
        self.grid.SetColSize(2,280)
    
    def __do_layout(self):
        sizer = wx.FlexGridSizer(2, 1, 0, 0)
        sizer.Add(self.chart, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        sizer.Add(self.grid, 1, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 0)
        sizer.AddGrowableRow(1)
        sizer.AddGrowableCol(0)
        self.SetSizer(sizer)
        self.Layout()

class TabBook(wx.Listbook):
    """"""
    def __init__(self, parent, apps):
        wx.Listbook.__init__(self, parent, -1, style=wx.BK_LEFT)
        
        self.tabs = {}
        for app in apps:
            self.tabs[app] = TabPanel(self, app)
            self.AddPage(self.tabs[app], app)
            
    def UpdateTabs(self, iprstat=None):
        """Assuming the values have changed, update each tab
           to display the new data.
        """
        if not iprstat:
            return
        
        for app, tab in self.tabs.iteritems():
            # TODO: update chart as well
            bitmap = iprstat.chart[app].GetChart()
            if bitmap:
                tab.chart.SetBitmap(bitmap)
                tab.chart.Show()
            else:
                tab.chart.Hide()

            tab.grid.GetTable().Update(iprstat.cache)
            tab.grid.AutoSizeColumns()
            tab.grid.Fit()

class Menu(wx.MenuBar):
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
    

class LinkTable(gridlib.PyGridTableBase):
    """Class underlying wx.grid.Grid that stores only the data from
    visible cells in memory at a given time
    """

    def __init__(self, app, data=None):
        """Initialize the table with a specified app and an initialized
        cache object
        """
        gridlib.PyGridTableBase.__init__(self)
        self.app = app
        self.data = data
        
        self.link = gridlib.GridCellAttr()
        self.link.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT,
                          wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, True))
        self.link.SetTextColour('blue')
        
        self.length = None
        
    def GetAttr(self, row, col, kind):
        """Return styling attributes for a cell
        
        Makes columns 0 and 2 look like links if their value
        isn't None; make everything readonly
        """
        attr = gridlib.GridCellAttr()
        if col != 1 and self.GetValue(row, col) != "None":
            attr = self.link
    
        attr.SetReadOnly()
        attr.IncRef()
        return attr
        
    def GetColLabelValue(self, col):
        """Define column labels"""
        
        if   col == 0: return "Name"
        elif col == 1: return "Count"
        elif col == 2: return "GO Term"
    
    def GetNumberRows(self):
        """Return the current length of the table"""
        
        if self.data:
            self.length = self.data.get_match_length(self.app)
            return self.length
        else:
            self.length = 0
            return 0

    def GetNumberCols(self):
        """Return the width of the table"""
        
        return 3

    def IsEmptyCell(self, row, col):
        """No visible cells should be empty"""
        
        return False

    def GetValue(self, row, col):
        """Retrieve cell value from the cache object"""
        
        if self.data.settings.usegolookup() and col==2:
            cell = self.data.get_one_cell(self.app, row, col+2)
        else:
            cell = self.data.get_one_cell(self.app, row, col)
            
        if not cell: return None
        return cell
    
    def SetValue(self, row, col, value):
        """Cell editing is disabled"""
        
        print 'SetValue(%d, %d, "%s") ignored.' % (row, col, value)
    
    def Update(self, data=None):
        """Update the table length based on the underlying
        cache object (for if the max_tables_result value is
        changed).
        """
        
        if data:
            self.data = data
        
        self.GetView().BeginBatch()
        newlength = self.data.get_match_length(self.app)
        if newlength < self.length:
            msg = gridlib.GridTableMessage(self,
                        gridlib.GRIDTABLE_NOTIFY_ROWS_DELETED,
                        self.length - newlength,    # position
                        self.length - newlength)    # how many
            self.GetView().ProcessTableMessage(msg)
        elif newlength > self.length:
            msg = gridlib.GridTableMessage(self,
                        gridlib.GRIDTABLE_NOTIFY_ROWS_APPENDED,
                        newlength - self.length)    # how many
            self.GetView().ProcessTableMessage(msg)
            
        self.length = newlength
        self.GetView().EndBatch()
        msg = gridlib.GridTableMessage(self,
                    gridlib.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        self.GetView().ProcessTableMessage(msg)
        

class PropertiesDlg(wx.Dialog):
    """Defines the properties dialog for changing settings"""
    
    def __init__(self, parent, id, title, settings):
        """Requires a parent wx object, an id, a title and
        a ConfigParser object for reading and writing settings"""
        
        self.settings = settings

        # Dialog initialization and tab creation
        wx.Dialog.__init__(self, parent, id, title)
        self.Tabs = wx.Notebook(self, -1, style=0)
        self.DBSettingsTab = wx.Panel(self.Tabs, -1)
        
        # General settings labels
        self.GeneralTab = wx.Panel(self.Tabs, -1)
        self.ChartTypeLbl = wx.StaticText(self.GeneralTab, -1, "Chart type: ")
        self.ChartGenLbl = wx.StaticText(self.GeneralTab, -1, "Chart generator: ")
        self.MaxChartLbl = wx.StaticText(self.GeneralTab, -1,
                                         "Max chart results: ")
        self.MaxTableLbl = wx.StaticText(self.GeneralTab, -1,
                                           "Max table results: ")
        
        # Local database connetion settings labels
        self.LDBSzrBox = wx.StaticBox(self.DBSettingsTab, -1,"Local database")
        self.LDBUseSqliteLbl = wx.StaticText(self.DBSettingsTab,-1,
                                            "Use SQLite: ")
        self.LDBHostLbl = wx.StaticText(self.DBSettingsTab,-1,"Host: ")
        self.LDBUserLbl = wx.StaticText(self.DBSettingsTab,-1,"User: ")
        self.LDBPasswrdLbl = wx.StaticText(self.DBSettingsTab,-1,"Password: ")
        self.LDBPortLbl = wx.StaticText(self.DBSettingsTab,-1,"Port: ")
        self.LDBDBLbl = wx.StaticText(self.DBSettingsTab,-1,"Database: ")
        
        # Gene Ontology database settings labels
        self.GDBSzrBox = wx.StaticBox(self.DBSettingsTab,-1,
                                         "Gene Ontology database")
        self.GDBGoLookupLbl = wx.StaticText(self.DBSettingsTab,-1,
                                            "Use GO lookup: ")
        self.GDBHostLbl = wx.StaticText(self.DBSettingsTab,-1,"Host: ")
        self.GDBUserLbl = wx.StaticText(self.DBSettingsTab,-1,"User: ")
        self.GDBPasswrdLbl = wx.StaticText(self.DBSettingsTab,-1,"Password: ")
        self.GDBPortLbl = wx.StaticText(self.DBSettingsTab,-1,"Port: ")
        self.GDBDBLbl = wx.StaticText(self.DBSettingsTab,-1,"Database: ")
        
        # Apply, Cancel, OK buttons
        self.CancelBtn = wx.Button(self, wx.ID_CANCEL, "")
        self.OKBtn = wx.Button(self, wx.ID_OK, "")
        self.PopulateDialog()

        self.Bind(wx.EVT_CHECKBOX, self.OnUseSqlite, self.LDBUseSqliteChk)
        self.Bind(wx.EVT_CHECKBOX, self.OnGoLookup, self.GDBGoLookupChk)
        
        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        """Set the default for checkboxes and combo boxes.
        """
        self.SetTitle("Change properties...")
        
        # Initialize chart type with correct value
        if self.settings.chart.gettype() == 'pie':
            self.ChartTypeCmb.SetSelection(0)
        else:
            self.ChartTypeCmb.SetSelection(1)
            
        # Initialize chart generator with correct value
        if self.settings.chart.getgenerator() == 'google':
            self.ChartGenCmb.SetSelection(0)
        else:
            self.ChartGenCmb.SetSelection(1)
        
        # Initialize SQLite and GO lookup checkboxes with correct value
        if sys.modules.has_key('MySQLdb'):
            self.LDBUseSqliteChk.SetValue(
                    self.settings.usesqlite())
            self.GDBGoLookupChk.SetValue(
                    self.settings.usegolookup())
        else:
            self.LDBUseSqliteChk.SetValue(True)
            self.GDBGoLookupChk.SetValue(False)
        
        # Disable MySQL connection inputs if using SQLite
        if self.LDBUseSqliteChk.GetValue():
            self.LDBHostTxt.Disable()
            self.LDBUserTxt.Disable()
            self.LDBPasswrdTxt.Disable()
            self.LDBPortSpn.Disable()
        
        # Disable MySQL GO connection if not using GO lookup
        if not self.GDBGoLookupChk.GetValue():
            self.GDBHostTxt.Disable()
            self.GDBUserTxt.Disable()
            self.GDBPasswrdTxt.Disable()
            self.GDBPortSpn.Disable()
            self.GDBDBTxt.Disable()

    def __do_layout(self):
        """Place all the defined elements into the
           correct sizer and fix any formatting issues.
        """
        MainSzr = wx.FlexGridSizer(2, 1, 0, 0)
        BtnSzr = wx.FlexGridSizer(1, 2, 0, 0)
        DBSzr = wx.BoxSizer(wx.HORIZONTAL)
        GDBSzr = wx.StaticBoxSizer(self.GDBSzrBox, wx.HORIZONTAL)
        GDBOptionsSzr = wx.FlexGridSizer(6, 2, 3, 0)
        LDBSzr = wx.StaticBoxSizer(self.LDBSzrBox, wx.HORIZONTAL)
        LDBOptionsSzr = wx.FlexGridSizer(6, 2, 3, 0)
        
        # General settings
        GeneralSzr = wx.FlexGridSizer(4, 2, 3, 0)
        GeneralSzr.Add(self.ChartTypeLbl,  0,
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        GeneralSzr.Add(self.ChartTypeCmb,  0,
                       wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        GeneralSzr.Add(self.ChartGenLbl,  0,
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        GeneralSzr.Add(self.ChartGenCmb,  0,
                       wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        GeneralSzr.Add(self.MaxChartLbl,   0,
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        GeneralSzr.Add(self.MaxChartSpn,   0,
                       wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        GeneralSzr.Add(self.MaxTableLbl,   0,
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        GeneralSzr.Add(self.MaxTableSpn,   0,
                       wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        self.GeneralTab.SetSizer(GeneralSzr)
        GeneralSzr.AddGrowableCol(1)
        
        # Local database connection settings
        LDBOptionsSzr.Add(self.LDBUseSqliteLbl, 0,
                          wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        LDBOptionsSzr.Add(self.LDBUseSqliteChk, 0,
                          wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        LDBOptionsSzr.Add(self.LDBHostLbl,     0,
                          wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        LDBOptionsSzr.Add(self.LDBHostTxt,     0,
                          wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        LDBOptionsSzr.Add(self.LDBUserLbl,     0,
                          wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        LDBOptionsSzr.Add(self.LDBUserTxt,     0,
                          wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE
                          , 0)
        LDBOptionsSzr.Add(self.LDBPasswrdLbl,  0,
                          wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        LDBOptionsSzr.Add(self.LDBPasswrdTxt,  0,
                          wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        LDBOptionsSzr.Add(self.LDBPortLbl,     0,
                          wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        LDBOptionsSzr.Add(self.LDBPortSpn,     0,
                          wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        LDBOptionsSzr.Add(self.LDBDBLbl, 0,
                          wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        LDBOptionsSzr.Add(self.LDBDBTxt, 0,
                          wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        LDBOptionsSzr.AddGrowableCol(1)
        LDBSzr.Add(LDBOptionsSzr, 1, wx.EXPAND, 0)
        DBSzr.Add(LDBSzr, 1, wx.EXPAND, 0)
        
        # Gene Ontology connection settings
        DBSzr.Add((5, 20), 0, wx.ADJUST_MINSIZE, 0)
        GDBOptionsSzr.Add(self.GDBGoLookupLbl,     0,
                          wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        GDBOptionsSzr.Add(self.GDBGoLookupChk, 0,
                          wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        GDBOptionsSzr.Add(self.GDBHostLbl,     0,
                          wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        GDBOptionsSzr.Add(self.GDBHostTxt,     0,
                          wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        GDBOptionsSzr.Add(self.GDBUserLbl,     0,
                          wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        GDBOptionsSzr.Add(self.GDBUserTxt,     0,
                          wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE
                          , 0)
        GDBOptionsSzr.Add(self.GDBPasswrdLbl,  0,
                          wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        GDBOptionsSzr.Add(self.GDBPasswrdTxt,  0,
                          wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        GDBOptionsSzr.Add(self.GDBPortLbl,     0,
                          wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        GDBOptionsSzr.Add(self.GDBPortSpn,     0,
                          wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        GDBOptionsSzr.Add(self.GDBDBLbl, 0,
                          wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        GDBOptionsSzr.Add(self.GDBDBTxt, 0,
                          wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        GDBOptionsSzr.AddGrowableCol(1)
        GDBSzr.Add(GDBOptionsSzr, 1, wx.EXPAND, 0)
        DBSzr.Add(GDBSzr, 1, wx.EXPAND, 0)
        
        self.DBSettingsTab.SetSizer(DBSzr)
        self.Tabs.AddPage(self.GeneralTab, "General")
        self.Tabs.AddPage(self.DBSettingsTab, "Database settings")
        MainSzr.Add(self.Tabs, 1, wx.EXPAND, 0)
        
        BtnSzr.Add(self.CancelBtn, 0, wx.ADJUST_MINSIZE, 0)
        BtnSzr.Add(self.OKBtn, 0, wx.ADJUST_MINSIZE, 0)
        MainSzr.Add(BtnSzr, 1, wx.ALIGN_RIGHT, 0)
        
        self.SetSizer(MainSzr)
        MainSzr.Fit(self)
        MainSzr.AddGrowableRow(0)
        MainSzr.AddGrowableCol(0)
        self.Layout()
    
    def PopulateDialog(self):
        """Create control elements and initialize their values
        with the settings from self.config
        """
        # General settings
        self.ChartTypeCmb  = wx.ComboBox(self.GeneralTab,    -1,
                                choices=['pie', 'bar'],
                                style=wx.CB_DROPDOWN)
        self.ChartGenCmb  = wx.ComboBox(self.GeneralTab,    -1,
                                choices=['google', 'pylab'],
                                style=wx.CB_DROPDOWN)
        self.MaxChartSpn   = wx.SpinCtrl(self.GeneralTab,    -1,
                                str(self.settings.chart.getmaxresults())
                                , min=0, max=35)
        self.MaxTableSpn   = wx.SpinCtrl(self.GeneralTab,    -1,
                                str(self.settings.getmaxtableresults())
                                , min=-1, max=2147483647) #32 bit signed int
        
        # Local database settings
        dbsettings = self.settings.getlocaldb()
        self.LDBUseSqliteChk=wx.CheckBox(self.DBSettingsTab, -1, '')
        self.LDBHostTxt    = wx.TextCtrl(self.DBSettingsTab, -1,
                                dbsettings.gethost())
        self.LDBUserTxt    = wx.TextCtrl(self.DBSettingsTab, -1,
                                dbsettings.getuser())
        self.LDBPasswrdTxt = wx.TextCtrl(self.DBSettingsTab, -1,
                                dbsettings.getpasswd(),
                                style=wx.TE_PASSWORD)
        self.LDBPortSpn    = wx.SpinCtrl(self.DBSettingsTab, -1,
                                str(dbsettings.getport()),
                                min=0, max=10000)
        self.LDBDBTxt= wx.TextCtrl(self.DBSettingsTab, -1,
                                dbsettings.getdb())
        
        # Gene Ontology database settings
        dbsettings = self.settings.getgodb()
        self.GDBGoLookupChk= wx.CheckBox(self.DBSettingsTab, -1, '')
        self.GDBHostTxt    = wx.TextCtrl(self.DBSettingsTab, -1,
                                dbsettings.gethost())
        self.GDBUserTxt    = wx.TextCtrl(self.DBSettingsTab, -1,
                                dbsettings.getuser())
        self.GDBPasswrdTxt = wx.TextCtrl(self.DBSettingsTab, -1,
                                dbsettings.getpasswd(),
                                style=wx.TE_PASSWORD)
        self.GDBPortSpn    = wx.SpinCtrl(self.DBSettingsTab, -1,
                                str(dbsettings.getport()),
                                min=0, max=10000)
        self.GDBDBTxt= wx.TextCtrl(self.DBSettingsTab, -1,
                                dbsettings.getdb())

    def OnUseSqlite(self, event):
        """Prevents user from disabling SQLite if MySQLdb is not installed
        """
        if not sys.modules.has_key('MySQLdb') and \
            not self.LDBUseSqliteChk.GetValue():
            self.LDBUseSqliteChk.SetValue(True)
            msg ='You must have MySQLdb installed\nto use a MySQL connection.'
            dlg = wx.MessageDialog(None, msg, 'MySQL connection error',
                                   wx.OK |  wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy
        else:
            if self.LDBUseSqliteChk.GetValue():
                self.LDBHostTxt.Disable()
                self.LDBUserTxt.Disable()
                self.LDBPasswrdTxt.Disable()
                self.LDBPortSpn.Disable()
            else:
                self.LDBHostTxt.Enable()
                self.LDBUserTxt.Enable()
                self.LDBPasswrdTxt.Enable()
                self.LDBPortSpn.Enable()

    def OnGoLookup(self, event):
        """Disables gene ontology lookup if MySQLdb is not installed
        """
        if not sys.modules.has_key('MySQLdb') and \
            self.GDBGoLookupChk.GetValue():
            self.GDBGoLookupChk.SetValue(False)
            msg = 'You must have MySQLdb installed\nto use GO lookup.'
            dlg = wx.MessageDialog(None, msg, 'Gene Ontology lookup error',
                                   wx.OK |  wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy
        else:
            if not self.GDBGoLookupChk.GetValue():
                self.GDBHostTxt.Disable()
                self.GDBUserTxt.Disable()
                self.GDBPasswrdTxt.Disable()
                self.GDBPortSpn.Disable()
                self.GDBDBTxt.Disable()
            else:
                self.GDBHostTxt.Enable()
                self.GDBUserTxt.Enable()
                self.GDBPasswrdTxt.Enable()
                self.GDBPortSpn.Enable()
                self.GDBDBTxt.Enable()
            
    
    def SaveProperties(self):
        """Writes all the dialog settings back to self.config
        """
        config = self.settings.getconfigparser()
        
        config.set('general', 'chart_type',
                        self.ChartTypeCmb.GetValue().lower())
        config.set('general', 'chart_gen',
                        self.ChartGenCmb.GetValue().lower())
        config.set('general', 'max_chart_results',
                        self.MaxChartSpn.GetValue())
        config.set('general', 'max_table_results',
                        self.MaxTableSpn.GetValue())
        config.set('local db', 'use_sqlite',
                        str(self.LDBUseSqliteChk.GetValue()))
        config.set('local db', 'host', self.LDBHostTxt.GetValue())
        config.set('local db', 'user', self.LDBUserTxt.GetValue())
        config.set('local db', 'passwd',
                        self.LDBPasswrdTxt.GetValue())
        config.set('local db', 'port', self.LDBPortSpn.GetValue())
        config.set('local db', 'db',
                        str(self.LDBDBTxt.GetValue()))
        config.set('go db', 'go_lookup',
                        str(self.GDBGoLookupChk.GetValue()))
        config.set('go db', 'host', self.GDBHostTxt.GetValue())
        config.set('go db', 'user', self.GDBUserTxt.GetValue())
        config.set('go db', 'passwd', self.GDBPasswrdTxt.GetValue())
        config.set('go db', 'port', self.GDBPortSpn.GetValue())
        config.set('go db', 'db', str(self.GDBDBTxt.GetValue()))
        
        self.settings.setconfigparser()


import platform

class About(wx.AboutDialogInfo):
    """Defines information to display in the "about" dialog"""
    
    def __init__(self, *args, **kwds):
        wx.AboutDialogInfo.__init__(self, *args, **kwds)
        self.SetName('IPRStats')
        self.SetVersion('0.4')
        self.SetDescription('A statistical tool that eases ' +\
                'the analysis of InterProScan results by generating ' +\
                'charts and tables with links to additional information.')
        self.AddDeveloper('David Vincent')
        self.AddDeveloper('Ryan Kelly')
        self.AddDeveloper('Iddo Friedberg')
        # NOTE: Mac/Windows don't natively support urls or license text;
        if platform.system == 'Linux':
            self.SetWebSite('http://github.com/devrkel/IPRStats')
            self.SetLicence("""Academic Free License ("AFL") v. 3.0

This Academic Free License (the "License") applies to any original work
of authorship (the "Original Work") whose owner (the "Licensor") has
placed the following licensing notice adjacent to the copyright notice
for the Original Work:

Licensed under the Academic Free License version 3.0

1) Grant of Copyright License. Licensor grants You a worldwide,
royalty-free, non-exclusive, sublicensable license, for the duration of
the copyright, to do the following:

a) to reproduce the Original Work in copies, either alone or as part of
a collective work;

b) to translate, adapt, alter, transform, modify, or arrange the
Original Work, thereby creating derivative works ("Derivative Works")
based upon the Original Work;

c) to distribute or communicate copies of the Original Work and
Derivative Works to the public, under any license of your choice that
does not contradict the terms and conditions, including Licensor's
reserved rights and remedies, in this Academic Free License;

d) to perform the Original Work publicly; and

e) to display the Original Work publicly.

2) Grant of Patent License. Licensor grants You a worldwide,
royalty-free, non-exclusive, sublicensable license, under patent claims
owned or controlled by the Licensor that are embodied in the Original
Work as furnished by the Licensor, for the duration of the patents, to
make, use, sell, offer for sale, have made, and import the Original Work
and Derivative Works.

3) Grant of Source Code License. The term "Source Code" means the
preferred form of the Original Work for making modifications to it and
all available documentation describing how to modify the Original Work.
Licensor agrees to provide a machine-readable copy of the Source Code of
the Original Work along with each copy of the Original Work that
Licensor distributes. Licensor reserves the right to satisfy this
obligation by placing a machine-readable copy of the Source Code in an
information repository reasonably calculated to permit inexpensive and
convenient access by You for as long as Licensor continues to distribute
the Original Work.

4) Exclusions From License Grant. Neither the names of Licensor, nor the
names of any contributors to the Original Work, nor any of their
trademarks or service marks, may be used to endorse or promote products
derived from this Original Work without express prior permission of the
Licensor. Except as expressly stated herein, nothing in this License
grants any license to Licensor's trademarks, copyrights, patents, trade
secrets or any other intellectual property. No patent license is granted
to make, use, sell, offer for sale, have made, or import embodiments of
any patent claims other than the licensed claims defined in Section 2.
No license is granted to the trademarks of Licensor even if such marks
are included in the Original Work. Nothing in this License shall be
interpreted to prohibit Licensor from licensing under terms different
from this License any Original Work that Licensor otherwise would have a
right to license.

5) External Deployment. The term "External Deployment" means the use,
distribution, or communication of the Original Work or Derivative Works
in any way such that the Original Work or Derivative Works may be used
by anyone other than You, whether those works are distributed or
communicated to those persons or made available as an application
intended for use over a network. As an express condition for the grants
of license hereunder, You must treat any External Deployment by You of
the Original Work or a Derivative Work as a distribution under section
1(c).

6) Attribution Rights. You must retain, in the Source Code of any
Derivative Works that You create, all copyright, patent, or trademark
notices from the Source Code of the Original Work, as well as any
notices of licensing and any descriptive text identified therein as an
"Attribution Notice." You must cause the Source Code for any Derivative
Works that You create to carry a prominent Attribution Notice reasonably
calculated to inform recipients that You have modified the Original
Work.

7) Warranty of Provenance and Disclaimer of Warranty. Licensor warrants
that the copyright in and to the Original Work and the patent rights
granted herein by Licensor are owned by the Licensor or are sublicensed
to You under the terms of this License with the permission of the
contributor(s) of those copyrights and patent rights. Except as
expressly stated in the immediately preceding sentence, the Original
Work is provided under this License on an "AS IS" BASIS and WITHOUT
WARRANTY, either express or implied, including, without limitation, the
warranties of non-infringement, merchantability or fitness for a
particular purpose. THE ENTIRE RISK AS TO THE QUALITY OF THE ORIGINAL
WORK IS WITH YOU. This DISCLAIMER OF WARRANTY constitutes an essential
part of this License. No license to the Original Work is granted by this
License except under this disclaimer.

8) Limitation of Liability. Under no circumstances and under no legal
theory, whether in tort (including negligence), contract, or otherwise,
shall the Licensor be liable to anyone for any indirect, special,
incidental, or consequential damages of any character arising as a
result of this License or the use of the Original Work including,
without limitation, damages for loss of goodwill, work stoppage,
computer failure or malfunction, or any and all other commercial damages
or losses. This limitation of liability shall not apply to the extent
applicable law prohibits such limitation.

9) Acceptance and Termination. If, at any time, You expressly assented
to this License, that assent indicates your clear and irrevocable
acceptance of this License and all of its terms and conditions. If You
distribute or communicate copies of the Original Work or a Derivative
Work, You must make a reasonable effort under the circumstances to
obtain the express assent of recipients to the terms of this License.
This License conditions your rights to undertake the activities listed
in Section 1, including your right to create Derivative Works based upon
the Original Work, and doing so without honoring these terms and
conditions is prohibited by copyright law and international treaty.
Nothing in this License is intended to affect copyright exceptions and
limitations (including "fair use" or "fair dealing"). This License shall
terminate immediately and You may no longer exercise any of the rights
granted to You by this License upon your failure to honor the conditions
in Section 1(c).

10) Termination for Patent Action. This License shall terminate
automatically and You may no longer exercise any of the rights granted
to You by this License as of the date You commence an action, including
a cross-claim or counterclaim, against Licensor or any licensee alleging
that the Original Work infringes a patent. This termination provision
shall not apply for an action alleging patent infringement by
combinations of the Original Work with other software or hardware.

11) Jurisdiction, Venue and Governing Law. Any action or suit relating
to this License may be brought only in the courts of a jurisdiction
wherein the Licensor resides or in which Licensor conducts its primary
business, and under the laws of that jurisdiction excluding its
conflict-of-law provisions. The application of the United Nations
Convention on Contracts for the International Sale of Goods is expressly
excluded. Any use of the Original Work outside the scope of this License
or after its termination shall be subject to the requirements and
penalties of copyright or patent law in the appropriate jurisdiction.
This section shall survive the termination of this License.

12) Attorneys' Fees. In any action to enforce the terms of this License
or seeking damages relating thereto, the prevailing party shall be
entitled to recover its costs and expenses, including, without
limitation, reasonable attorneys' fees and costs incurred in connection
with such action, including any appeal of such action. This section
shall survive the termination of this License.

13) Miscellaneous. If any provision of this License is held to be
unenforceable, such provision shall be reformed only to the extent
necessary to make it enforceable.

14) Definition of "You" in This License. "You" throughout this License,
whether in upper or lower case, means an individual or a legal entity
exercising rights under, and complying with all of the terms of, this
License. For legal entities, "You" includes any entity that controls, is
controlled by, or is under common control with you. For purposes of this
definition, "control" means (i) the power, direct or indirect, to cause
the direction or management of such entity, whether by contract or
otherwise, or (ii) ownership of fifty percent (50%) or more of the
outstanding shares, or (iii) beneficial ownership of such entity.

15) Right to Use. You may use the Original Work in all ways not
otherwise restricted or conditioned by this License or by law, and
Licensor promises not to interfere with or be responsible for such uses
by You.

16) Modification of This License. This License is Copyright (c) 2005
Lawrence Rosen. Permission is granted to copy, distribute, or
communicate this License without modification. Nothing in this License
permits You to modify this License as applied to the Original Work or to
Derivative Works. However, You may modify the text of this License and
copy, distribute or communicate your modified version (the "Modified
License") and apply it to other original works of authorship subject to
the following conditions: (i) You may not indicate in any way that your
Modified License is the "Academic Free License" or "AFL" and you may not
use those names in the name of your Modified License; (ii) You must
replace the notice specified in the first paragraph above with the
notice "Licensed under <insert your license name here>" or with a notice
of your own that is not confusingly similar to the notice in this
License; and (iii) You may not claim that your original works are open
source software unless your Modified License has been approved by Open
Source Initiative (OSI) and You comply with its license review and
certification process.
""")
        
        self.__set_properties()
        self.__do_layout()
        
    def __set_properties(self):
        pass
    
    def __do_layout(self):
        pass