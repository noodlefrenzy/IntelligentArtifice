Title: Time-Series Processing in Azure ML Using Python
Date: 2015-03-14 22:09
Author: noodlefrenzy
Category: Machine Learning
Tags: Azure, Machine Learning, ML, Python, Time Series
Slug: time-series-processing-in-azure-ml-using-python
Status: published

With the general availability of Azure Machine Learning, the team has
added a ton of new features.  Perhaps the one I'm most excited about is
the addition of a general "Execute Python Script" module.  I've been
meaning to brush up on my Python skills, and with the inclusion of
Pandas and Numpy it opens up a lot of data processing options -
particularly for time-series data.  There are still a few quirks when
using it though, so similar to my previous post on [coping with dates in
AzureML's R
module](http://www.mikelanzetta.com/2015/01/data-cleaning-with-azureml-and-r-dates/), I
thought I'd outline those quirks in a post.  I'll be doing so in a
step-by-step fashion so hopefully I can show how you'd go about
diagnosing these sorts of quirks yourself.

One of the things I love about Python's Pandas library is its [fantastic
support for
time-series](http://pandas.pydata.org/pandas-docs/stable/timeseries.html)
data manipulation.  The ability to normalize dates, roll up into
aggregates, and easily slice ranges is phenomenal.

![execute\_python]({filename}/images/execute_python.png)

 

To get started, we'll pull in some time-series data, and mess around
with it in the Python module - set up an experiment with a Reader
connected to an "Execute Python Script" module.

The Reader can pull data directly from plenty of different sources, but
for this time-series example, let's use finance data from Yahoo's ichart
API.  We'll pull data for a single stock's history - let's use an
exasperating one like
TSLA: http://ichart.finance.yahoo.com/table.csv?s=TSLA.  This returns
data as a CSV with a header row, leading to the final Reader
configuration
below.

![ichart\_reader\_config]({filename}/images/ichart_reader_config.png)

Once we have the data coming in, it's time to do something fun with it.
 Let's take a first crack at it - we'll take the input and turn it into
monthly means.  In regular Python with Pandas, that looks like:

```python
import pandas as pd

tsla = pd.read_csv('http://ichart.finance.yahoo.com/table.csv?s=TSLA', index_col=0, parse_dates=True)
tsla_monthly = tsla.resample('M', how='mean')
```

This is why I love Pandas - that code is clean, easy to read, and easy
to write (at least with intellisense/completion).  Let's assume that
resample would work the same on the data from the reader, and try it in
the module:

```python
import pandas as pd

def azureml_main(dataframe1 = None, dataframe2 = None):

    dfMonthly = dataframe1.resample('M', how='mean')

    return dfMonthly,
```

Boom!  Well, that didn't work:

> ` File "C:\pyhome\lib\site-packages\pandas\tseries\resample.py", line 101, in resample`\
>  ` raise TypeError('Only valid with DatetimeIndex or PeriodIndex')`

So we don't have a `DatetimeIndex `- must not be importing an index,
we'll need to make our own
using `dataframe1.set_index('Date', inplace=True).`  Hmm, same error.
 Is Azure ML just not parsing the dates?  Let's print things out and see
what we have:

```python
def azureml_main(dataframe1 = None, dataframe2 = None):
    print(dataframe1.info(verbose=True))
    print(dataframe1.head())

    return dataframe1,
```

gives us:

```
<class 'pandas.core.frame.DataFrame'>
Int64Index: 1185 entries, 0 to 1184
Data columns (total 7 columns):
Date         1185 non-null float64
Open         1185 non-null float64
High         1185 non-null float64
Low          1185 non-null float64
Close        1185 non-null float64
Volume       1185 non-null int32
Adj Close    1185 non-null float64
```

Notice `Date` is listed as a `float64`.  That's exciting news!  Why is
it a float64?  I'd expect it to be either a Date, a Datetime, or maybe a
String - but a Float?  And why did I not get the `head()` output?  Let's
solve the second part first - I'm going to guess it's an issue with
buffering, since I've seen similar issues in the past (the distant
past - C++ streams - but still).  Let's just print a bunch of spaces and
hope for the best: `print(' ' * 4096)`.  Paydirt!

```
         Date    Open    High     Low   Close   Volume  Adj Close
0  1426204800  188.95  191.75  187.32  188.68  5378600     188.68
1  1426118400  193.75  194.45  189.75  191.07  4123500     191.07
2  1426032000  191.15  196.18  191.01  193.74  4950300     193.74
3  1425945600  188.46  193.50  187.60  190.32  5530900     190.32
4  1425859200  194.39  194.49  188.25  190.88  6717300     190.88
```

I notice two things immediately - we were right about the lack of an
index and that float actually looks like a long, in particular a
timestamp.  Let's guess this is related to Posix timestamps, and add a
conversion before our set\_index call:

```python
import pandas as pd
import datetime as dt

def azureml_main(dataframe1 = None, dataframe2 = None):
    dataframe1.Date = dataframe1.apply(lambda x : dt.datetime.fromtimestamp(x['Date']), axis=1)
    dataframe1.set_index('Date', inplace=True)
    dfMonthly = dataframe1.resample('M', how='mean')

    return dfMonthly,
```

![orig\_output]({filename}/images/orig_output.png) 

This worked!  However, looking at the output there is no Date column - so I'm
guessing that in the same way the input data didn't pull the first
column as an index, the output doesn't write out the index either.
 We'll need to turn our index back into a
column: `dfMonthly.reset_index(level=0, inplace=True)`.  Finally, all
don... wha?!

` Exception: Type unsupported <class 'pandas.tslib.Timestamp'>`

Crap.  Looks like the output from the Python module can't handle
Timestamps.  Well, we really only want the date, and strings should be
fine, so lets just convert these Timestamps to strings and hope that
downstream modules can handle those effectively, and in the meantime
I'll let the AzureML team know.  The final code looks like:

```python
import pandas as pd
import datetime as dt

def azureml_main(dataframe1 = None, dataframe2 = None):
    dataframe1.Date = dataframe1.apply(lambda x : dt.datetime.fromtimestamp(x['Date']), axis=1)
    dataframe1.set_index('Date', inplace=True)
    dfMonthly = dataframe1.resample('M', how='mean')
    dfMonthly.reset_index(level=0, inplace=True)
    dfMonthly.Date = dfMonthly.apply(lambda x : x['Date'].strftime('%Y-%m-%d'), axis=1)

    return dfMonthly,
```

I hope this helps!  If you find any other quirks let me know - I'll
definitely let the AzureML team know, and add the workarounds to my
list.

