#!/usr/bin/env python

import wx
import wx.grid as gridlib

class LinkTable(gridlib.PyGridTableBase):
    """Class underlying wx.grid.Grid that stores only the data from
    visible cells in memory at a given time
    """

    def __init__(self, app, data):
        """Initialize the table with a specified app and an initialized
        IPRStatsData object
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
        
        Makes columns 0 and 2 look like links
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
        
        self.length = self.data.get_table_length(self.app)
        return self.length

    def GetNumberCols(self):
        """Return the width of the table"""
        
        return 3

    def IsEmptyCell(self, row, col):
        """No visible cells should be empty"""
        
        return False

    def GetValue(self, row, col):
        """Retrieve cell value from the IPRStatsData object"""
        
        if   col == 0: col = 5
        elif col == 1: col = 0
        elif col == 2: col = 3
        
        cell = self.data.get_table_cell(self.app, row, col)
        if not cell: return None
        return cell
    
    def SetValue(self, row, col, value):
        """Cell editing is disabled"""
        
        print 'SetValue(%d, %d, "%s") ignored.' % (row, col, value)
    
    def Update(self):
        """Update the table length based on the underlying
        IPRStatsData object
        """
        
        self.GetView().BeginBatch()
        newlength = self.data.get_table_length(self.app)
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