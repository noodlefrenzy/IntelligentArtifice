Title: Processing Data In Python - Pandas + sklearn
Date: 2016-01-19 17:36
Author: noodlefrenzy
Category: Data Science, Software
Tags: Data, Data Science, Machine Learning, ML, Python
Slug:  
Status: draft

One of my stated goals when I started this blog was as a holding pen for
various techniques that I use when writing code - common pieces of code
that I use frequently and don't want to forget. I haven't really used
this blog as a forum for that, but with this series of blog posts I'm
planning on changing that - hopefully in a way that'll be useful to the
reader as well.

I wind up doing data analytics and machine learning projects in a
variety of different languages, so need to be at least somewhat
comfortable manipulating, visualizing, and learning on data in all of
them. Lately I've been messing around with Python as it's been useful
for a number of projects (including [my previous post on
TensorFlow](http://www.mikelanzetta.com/2015/12/tensorflow-on-azure-using-docker/)).
I'd resisted Python for a long time, as both the version schism (2 vs.
3) and the semantic use of whitespace bothered me, but now that I've
started using it the language is growing on me.

### Data Manipulation in Python

Almost every data scientist has used R for data manipulation and
visualization, and everyone who has is familiar with the concept of the
Data Frame. A Data Frame can be viewed somewhat like a heterogeneous
matrix - each column can have its own data type, which in theory could
even be its own multi-dimensional data. This is just the way R works -
(almost) everything operates on these Data Frames and they wind up being
very convenient.

Python has a module called [Pandas](http://pandas.pydata.org/)which
basically provides R-like Data Frames inside Python. It works fairly
seamlessly with [Numpy](http://www.numpy.org/)to ensure that numeric
operations on the data within the frame are efficient, and has flexible
data reshaping operations, robust time-series manipulation capabilities,
and is generally easy to work with.

We'll be using these features on a simple, easily solved problem -
forecasting the stock market. Just kidding! Not about the problem, just
about the solved part - I chose this problem because it has time-series
data that's easy to get, and it's easy to turn it into everything from a
forecasting, to a regression, to a classification problem. Also, if I
"solve" it during the course of these posts, I can retire!

### Gathering Data

We'll start with a simple Python function for pulling stock data from a
number of stocks into a number of `DataFrames`. For this, we use
the `yahoo_finance`package, which pulls data from (you guessed it)
Yahoo!'s excellent finance REST API. We also import Pandas, and pull in
`date` from `datetime`.

``` {.lang:python .decode:true title="Grabbing stock history data as a Data Frame"}
from yahoo_finance import Share
from datetime import date
import pandas as pd

def stock_hist(tickers, start_date = '2012-01-01', end_date = None):
    if (end_date is None):
        end_date = date.today().isoformat()
    result = {}
    for ticker in tickers:
        stock = Share(ticker)
        cur_hist = stock.get_historical(start_date, end_date)
        cur_df = pd.DataFrame(cur_hist)
        cur_df = cur_df.convert_objects(convert_dates=True, convert_numeric=True)
        cur_df.set_index(pd.DatetimeIndex(cur_df.Date), inplace=True)
        result[ticker] = cur_df
    return result
```

There are a number of items of interest here. First, notice how easy it
is to pull stock history data using `yahoo_finance` - you just
instantiate a `Share` object and call `get_historical` with the dates of
interest. We build a `DataFrame` from the result, and then convert the
date- and numeric-looking fields to ensure they are the correct types.
Finally, we set the `DataFrame's` index to be a `DateTimeIndex` of the
stock ticker date, instead of the default (numeric counter) index.
Finally, we return a map of tickers to each of their `DataFrames` - we
could build a composite `DataFrame`, but I felt that was more difficult
to grok for a beginner post.

Pandas includes some easy plotting utilities based on matplotlib, making
it easy to plot elements of your data frames, so you can easily use the
above code to grab stocks and plot the Adjusted Close prices and Volume:

``` {.lang:python .decode:true title="Plotting some stock data"}
tickers = ['TSLA', 'MSFT']
stocks = stock_hist(tickers)

stocks['MSFT'][['Adj_Close', 'Volume']].plot(figsize=[20,10], subplots=True)
```

[![Microsoft stock adjusted close and
volume](http://www.mikelanzetta.com/wp-content/uploads/2016/01/msft_stock-1024x498.png "Microsoft stock adjusted close and volume")](http://www.mikelanzetta.com/wp-content/uploads/2016/01/msft_stock.png)

### Featurizing Your Data

Let's take one of these stocks - in this case TSLA - and generate some
labeled, featurized data from these raw time-series. I'm not advocating
this as the best way to do things (unless it works), but for
illustrative purposes we'll break the whole time-series into six-month
chunks, build up some aggregate data, and compare that data to "the
future" (six months after the final date in the chunk). If the future
price is better than the measure we're using, we'll consider the stock a
"buy".

 

