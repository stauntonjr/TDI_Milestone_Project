# TDI_Milestone_Project
Deploy a Heroku Application of an interactive stock chart made with Bokeh Server.

Data: 
A list of NYSE listing tickers is pulled from Quandl's WIKI metadata via API, and used in the dropdown selection menu. 
The Quandl WIKI dataset is no longer supported by Quandl and is not recommended for use.
The selected stock's ticker code is used to query Alpha Venture to acquire the actual price and volume data via their API.
The daily data for the entire history of the stock is downloaded.
    To-Do: @lru-cache 
    
Bokeh:
A real python callback is implemented to get new stock data via API when the user selects a different stock. 
This requires the Bokeh Server rather than a static Bokeh document.
When the user updates month or year, the axis range values of the plots are updated accordingly.
A reset button emits the reset command to both plots simultaneously.
By default, the entire history is displayed when a new stock is selected.
   To-Do: edit toolboxes.
   
This app is not embedded in a Flask app, which would embed the app in a formatted HTML page.
Due to its simplicity, this app is a standalone Bokeh application deployed directly on Heroku.
As such, the Procfile is a run command 'bokeh serve ...' 
Note that Bokeh Server 1.2.0 uses the argument '--allow web-socket-origin=...' and not '--host=...'
The requirements.txt were auto-generated with pipreqs.


    



      

