import alpha_vantage
from datetime import datetime
from bokeh.embed import server_document
import requests
from io import BytesIO
from zipfile import ZipFile
import json
import pandas as pd
from bokeh.io import curdoc
from bokeh.server.server import Server
from bokeh.models import ColumnDataSource, NumeralTickFormatter, HoverTool
from bokeh.models.ranges import Range1d
from bokeh.models.widgets import Select
from bokeh.plotting import figure
from bokeh.layouts import row, column
from bokeh.palettes import Spectral5

Q_API_key = '2QQxWV_Ycg2ULirbUMxB' # Quandl
AV_API_key = '567TRV8RTL728INO' # Alpha Vantage 

def modify_doc(doc):
    # Download WIKI metadata from Quandl via API
    url_0 = 'https://www.quandl.com/api/v3/databases/WIKI/metadata?api_key='+Q_API_key
    response_0 = requests.get(url_0)
    # Unzip the bytes and extract the csv file into memory
    myzip = ZipFile(BytesIO(response_0.content)).extract('WIKI_metadata.csv')
    # Read the csv into pandas dataframe
    df_0 = pd.read_csv(myzip)
    # Clean up the name fields
    df_0['name'] = df_0['name'].apply(lambda s:s[:s.find(')')+1].rstrip())
    # Drop extraneous fields and reorder
    df_0 = df_0.reindex(columns=['name','code'])
    # Make widgets
    stock_picker = Select(title="Select a Stock",  value=df_0['name'][0], options=df_0['name'].tolist())
    year_picker = Select(title="Select a Year",  value="2018", options=[str(i) for i in range(2008,2019)])
    months = ["January","February", "March", "April", "May", "June", 
              "July", "August", "September", "October", "November", "December"]
    month_picker = Select(title="Select a Month",  value="January", options=months)
    widgets = row(stock_picker, year_picker, month_picker)

    # Get data
    def get_data(AV_API_key, ticker):
        from alpha_vantage.timeseries import TimeSeries
        ts = TimeSeries(key=AV_API_key)
        data, metadata = ts.get_daily(ticker,'full')
        data_dict = {}
        for sub in data.values():         
            for key, value in sub.items():
                data_dict.setdefault(key[3:], []).append(float(value))
        data_dict['date'] = list(data.keys())
        df = pd.DataFrame.from_dict(data_dict)
        df['date'] = pd.to_datetime(df['date'])
        return df

    # Make figure
    df = get_data(AV_API_key, 'A')
    dfi = df.set_index(['date'])
    data_dict = df.to_dict('series')
    data_dict = {k:data_dict[k][::-1] for k in data_dict.keys()}
    source = ColumnDataSource(data=data_dict)
    # create a new plot with a datetime axis type
    p1 = figure(plot_width=800, plot_height=400, x_axis_type="datetime")
    p2 = figure(plot_width=800, plot_height=250, x_axis_type="datetime", x_range=p1.x_range)
    # create price glyphs and volume glyph
    p1O = p1.line(x='date', y='open', source=source, color=Spectral5[0], alpha=0.8, legend="OPEN")
    p1C = p1.line(x='date', y='close', source=source, color=Spectral5[1], alpha=0.8, legend="CLOSE")
    p1L = p1.line(x='date', y='low', source=source, color=Spectral5[4], alpha=0.8, legend="LOW")
    p1H = p1.line(x='date', y='high', source=source, color=Spectral5[3], alpha=0.8, legend="HIGH")
    p2V = p2.line(x='date', y='volume', source=source, color="black", alpha=0.8)
    # Add HoverTools to each line
    p1.add_tools(HoverTool(tooltips=[('Date','@date{%F}'),('Open','@open{($ 0.00)}'),('Close','@close{($ 0.00)}'),
                                     ('Low','@low{($ 0.00)}'),('High','@high{($ 0.00)}'),('Volume','@volume{(0.00 a)}')],
                           formatters={'date': 'datetime'},mode='mouse'))
    p2.add_tools(HoverTool(tooltips=[('Date','@date{%F}'),('Open','@open{($ 0.00)}'),('Close','@close{($ 0.00)}'),
                                     ('Low','@low{($ 0.00)}'),('High','@high{($ 0.00)}'),('Volume','@volume{(0.00 a)}')],
                           formatters={'date': 'datetime'},mode='mouse'))
    # Add legend
    p1.legend.orientation = 'horizontal'
    p1.legend.title = 'Daily Stock Price'
    p1.legend.click_policy="hide"
    p1.legend.location="top_left"
    # Add axis labels
    p1.xaxis.axis_label = 'Date'
    p2.xaxis.axis_label = 'Date'
    p1.yaxis.axis_label = 'Price ($USD/share)'
    p2.yaxis.axis_label = 'Volume (shares)'
    # Add tick formatting
    p1.yaxis[0].formatter = NumeralTickFormatter(format="$0.00")
    p2.yaxis[0].formatter = NumeralTickFormatter(format="0.0a")
    p1.outline_line_width = 1
    p2.outline_line_width = 1
    
    # Set up callbacks
    def update_source(attrname, old, new):
        # Get the current Select value
        ticker = df_0.loc[df_0['name'] == stock_picker.value, 'code'].iloc[0]
        print('ticker:', ticker)
        # Get the new data
        df = get_data(AV_API_key, ticker)
        dfi = df.set_index(['date'])
        data_dict = df.to_dict('series')
        data_dict = {k:data_dict[k][::-1] for k in data_dict.keys()}
        source.data = data_dict
        
    def update_axis(attrname, old, new):
        # Get the current Select values
        year = year_picker.value
        month = f'{months.index(month_picker.value) + 1:02d}'   
        start = datetime.strptime(f'{year}-{month}-01', "%Y-%m-%d")
        if month == '12':
            end = datetime.strptime(f'{str(int(year)+1)}-01-01', "%Y-%m-%d")
        else:
            end = datetime.strptime(f'{year}-{int(month)+1:02d}-01', "%Y-%m-%d")     
        p1.x_range.start = start
        p1.x_range.end = end
        p1.y_range.start = dfi.loc[end:start]['low'].min()*0.95
        p1.y_range.end = dfi.loc[end:start]['high'].max()*1.05
        p2.y_range.start = dfi.loc[end:start]['volume'].min()*0.95
        p2.y_range.end = dfi.loc[end:start]['volume'].max()*1.05

    stock_picker.on_change('value', update_source)
    year_picker.on_change('value', update_axis)
    month_picker.on_change('value', update_axis)
        
    # Set up layouts and add to document
    row1 = row(stock_picker, year_picker, month_picker, width=800)
    row2 = row(p1, width=800, height=400)
    row3 = row(p2, width=800, height=150)
    layout = column(row1, row2, row3, width=800)
    doc.add_root(layout)

modify_doc(curdoc())
