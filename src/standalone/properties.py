#!/usr/bin/env python

import wx, sys

class PropertiesDlg(wx.Dialog):
    """Defines the properties dialog for changing settings"""
    
    def __init__(self, parent, id, title, config):
        """Requires a parent wx object, an id, a title and
        a ConfigParser object for reading and writing settings"""
        
        self.config = config
        self.dirname = config.get('general','directory')

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
        self.ApplyBtn = wx.Button(self, wx.ID_APPLY, "")
        self.CancelBtn = wx.Button(self, wx.ID_CANCEL, "")
        self.OKBtn = wx.Button(self, wx.ID_OK, "")
        self.PopulateDialog()

        self.Bind(wx.EVT_CHECKBOX, self.OnUseSqlite, self.LDBUseSqliteChk)
        self.Bind(wx.EVT_CHECKBOX, self.OnGoLookup, self.GDBGoLookupChk)
        
        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetTitle("Change properties...")
        
        # Initialize chart type with correct value
        if self.config.get('general','chart_type').lower() == 'pie':
            self.ChartTypeCmb.SetSelection(0)
        else:
            self.ChartTypeCmb.SetSelection(1)
            
        # Initialize chart generator with correct value
        if self.config.get('general','chart_gen').lower() == 'google':
            self.ChartGenCmb.SetSelection(0)
        else:
            self.ChartGenCmb.SetSelection(1)
        
        # Initialize SQLite and GO lookup checkboxes with correct value
        if sys.modules.has_key('MySQLdb'):
            self.LDBUseSqliteChk.SetValue(
                    self.config.getboolean('local db','use_sqlite'))
            self.GDBGoLookupChk.SetValue(
                    self.config.getboolean('general','go_lookup'))
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
        MainSzr = wx.FlexGridSizer(2, 1, 0, 0)
        BtnSzr = wx.FlexGridSizer(1, 3, 0, 0)
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
        
        BtnSzr.Add(self.ApplyBtn, 0, wx.ADJUST_MINSIZE, 0)
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
                                self.config.get('general','max_chart_results')
                                , min=0, max=35)
        self.MaxTableSpn   = wx.SpinCtrl(self.GeneralTab,    -1,
                                self.config.get('general','max_table_results')
                                , min=-1, max=2147483647) #32 bit signed int
        
        # Local database settings
        self.LDBUseSqliteChk=wx.CheckBox(self.DBSettingsTab, -1, '')
        self.LDBHostTxt    = wx.TextCtrl(self.DBSettingsTab, -1,
                                self.config.get('local db','host'))
        self.LDBUserTxt    = wx.TextCtrl(self.DBSettingsTab, -1,
                                self.config.get('local db','user'))
        self.LDBPasswrdTxt = wx.TextCtrl(self.DBSettingsTab, -1,
                                self.config.get('local db','passwd'),
                                style=wx.TE_PASSWORD)
        self.LDBPortSpn    = wx.SpinCtrl(self.DBSettingsTab, -1,
                                self.config.get('local db','port'),
                                min=0, max=10000)
        self.LDBDBTxt= wx.TextCtrl(self.DBSettingsTab, -1,
                                self.config.get('local db','db'))
        
        # Gene Ontology database settings
        self.GDBGoLookupChk= wx.CheckBox(self.DBSettingsTab, -1, '')
        self.GDBHostTxt    = wx.TextCtrl(self.DBSettingsTab, -1,
                                self.config.get('go db','host'))
        self.GDBUserTxt    = wx.TextCtrl(self.DBSettingsTab, -1,
                                self.config.get('go db','user'))
        self.GDBPasswrdTxt = wx.TextCtrl(self.DBSettingsTab, -1,
                                self.config.get('go db','passwd'),
                                style=wx.TE_PASSWORD)
        self.GDBPortSpn    = wx.SpinCtrl(self.DBSettingsTab, -1,
                                self.config.get('go db','port'),
                                min=0, max=10000)
        self.GDBDBTxt= wx.TextCtrl(self.DBSettingsTab, -1,
                                self.config.get('go db','db'))

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
        self.config.set('general', 'chart_type',
                        self.ChartTypeCmb.GetValue().lower())
        self.config.set('general', 'chart_gen',
                        self.ChartGenCmb.GetValue().lower())
        self.config.set('general', 'max_chart_results',
                        self.MaxChartSpn.GetValue())
        self.config.set('general', 'max_table_results',
                        self.MaxTableSpn.GetValue())
        self.config.set('local db', 'use_sqlite',
                        str(self.LDBUseSqliteChk.GetValue()))
        self.config.set('local db', 'host', self.LDBHostTxt.GetValue())
        self.config.set('local db', 'user', self.LDBUserTxt.GetValue())
        self.config.set('local db', 'passwd',
                        self.LDBPasswrdTxt.GetValue())
        self.config.set('local db', 'port', self.LDBPortSpn.GetValue())
        self.config.set('local db', 'db',
                        str(self.LDBDBTxt.GetValue()))
        self.config.set('general', 'go_lookup',
                        str(self.GDBGoLookupChk.GetValue()))
        self.config.set('go db', 'host', self.GDBHostTxt.GetValue())
        self.config.set('go db', 'user', self.GDBUserTxt.GetValue())
        self.config.set('go db', 'passwd', self.GDBPasswrdTxt.GetValue())
        self.config.set('go db', 'port', self.GDBPortSpn.GetValue())
        self.config.set('go db', 'db', str(self.GDBDBTxt.GetValue()))