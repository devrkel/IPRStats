try:
    import pylab
    pylab_avail = True
except ImportError:
    pylab_avail = False
    
try:
    import wx
    wx_avail = True
except ImportError:
    wx_avail = False
    
from lib.pygooglechart import PieChart2D, GroupedHorizontalBarChart
import os

class Chart:
    """Object used to define the data, labels, title, filename,
       etc for generating, saving, and displaying charts.
    """
    def __init__(self, app, cache, chart_title=None):
        """Initialize a chart with its associated app, the
           global cache, and a title you'd like to give it.
        """

        self.app = app
        self.cache = cache
        self.chart_title = chart_title
        
        if chart_title:
            self.filename = os.path.join(self.cache.settings.getsessiondir(),
                    chart_title.replace(' ','_').lower() +
                    self.cache.settings.getchartsettings().getgenerator() +
                    self.cache.settings.getchartsettings().gettype() + '.png')
        else:
            self.filename = os.path.join(self.cache.settings.getsessiondir(),
                                         app + '.png')
    
    def GetChartTitle(self):
        """Returns the chart title
        """
        return self.chart_title
    
    def GetFilename(self):
        """Returns the generated file path that the chart
           is downloaded to by default.
        """
        return self.filename
    
    def SetChartTitle(self, chart_title):
        """Set the chart title, and by doing so, change
           default filename for the chart.
        """
        assert(type(chart_title) is str)
        self.chart_title = chart_title
        self.filename = os.path.join(self.cache.settings.getsessiondir(),
                    chart_title.replace(' ','_').lower() +
                    self.cache.settings.getchartsettings().getgenerator() +
                    self.cache.settings.getchartsettings().gettype() + '.png')
        
    def CreateGooglePie(self, counts, labels, settings):
        """Create a pie chart using the Google Charting API.
        """
        width = int(3.6*settings.getscale())
        height = int(settings.getscale())
        chart = PieChart2D(width, height)
        chart.add_data(counts)
        chart.set_pie_labels(labels)
        chart.set_title(self.chart_title)
        chart.set_colours(('66FF66', 'FFFF66', '66FF99'))
        return chart
    
    def CreateGoogleBar(self, counts, labels, settings):
        """Create a bar chart using the Google Charting API.
        """
        barwidth = int(settings.getscale() / 20)
        width = int(3.6*settings.getscale())
        height = len(counts) * (barwidth+8) + 35
        stp = (counts[0] + 9) / 10
        max_x = min(counts[0]/stp + 1, 11) * stp
        chart = GroupedHorizontalBarChart(width, height, x_range=(0, max_x))
        chart.set_bar_width(barwidth)
        chart.add_data(counts)
        reversed_labels = [label for label in labels]
        reversed_labels.reverse()
        chart.set_axis_labels('x', range(0,max_x + 1, stp))
        chart.set_axis_labels('y', reversed_labels)
        chart.set_title(self.chart_title)
        chart.set_colours(('66FF66', 'FFFF66', '66FF99'))
        return chart
    
    def CreatePylabPie(self, counts, labels, settings):
        """Create a pie chart using PyLab/Matplotlib.
        """
        pylab.figure(figsize=(7, 2), dpi=150)
        pylab.axis('scaled')
        _, tlabels = pylab.pie(counts, labels=labels, shadow=False)
        for label in tlabels:
            label.set_size(9)
        pylab.title(self.chart_title, fontsize=12)
    
    def CreatePylabBar(self, counts, labels, settings):
        """Create a bar chart using PyLab/Matplotlib.
        """
        pylab.figure(figsize=(7, 2), dpi=150)
        pylab.barh(range(len(counts)-1, -1, -1), counts, height=0.6)
        pylab.title(self.chart_title, fontsize=12)
        
    def Save(self, settings=None, filename=None):
        """Generate the chart using the given ChartSettings
           object and download it to chart_filename.
        """
        if not settings:
            settings = self.cache.settings.getchartsettings()
        if not filename:
            filename = self.filename
        
        counts, labels = self.cache.get_counts(self.app)
        if not counts or len(counts) < 1:
            return False
        
        assert(len(counts) == len(labels))
        
        #try:
        if settings.getgenerator() == 'pylab':
            if settings.gettype() == 'pie':
                self.CreatePylabPie(counts, labels, settings)
            else:
                self.CreatePylabBar(counts, labels, settings)
            pylab.savefig(filename)
        else:
            if settings.gettype() == 'pie':
                chart = self.CreateGooglePie(counts, labels, settings)
            else:
                chart = self.CreateGoogleBar(counts, labels, settings)
            chart.download(filename)
        return True
        #except:
        #    return False
    
    def GetChart(self, settings=None):
        """Return a wxPython object to display in the GUI. Right
           now it only saves the chart and returns a Bitmap, but
           eventually it could draw and return charts drawn in a
           wxCanvas object.
        """
        if not settings:
            settings = self.cache.settings.getchartsettings()
        
        if self.Save(settings) and wx_avail:
            return wx.Bitmap(self.filename, wx.BITMAP_TYPE_ANY)
        else:
            return None
