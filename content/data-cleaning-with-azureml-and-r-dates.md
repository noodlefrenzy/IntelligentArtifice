Title: Data Cleaning with AzureML and R: Dates
Date: 2015-01-19 17:42
Author: noodlefrenzy
Category: Software
Tags: Azure, AzureML, ML, R
Slug: data-cleaning-with-azureml-and-r-dates
Status: published

I've been working with
[AzureML](http://azure.microsoft.com/en-us/services/machine-learning/ "Azure Machine Learning")for
a while now, and it's fantastic.  Having done ML in a few other
platforms over the years, the ease with which I can put together a few
regression models, do parameter-sweeps, and compare results is just
groundbreaking.

However, one area where it isn't quite as groundbreaking is data
cleaning.  Right now, there are only a few options, and a lot of the
time you wind up resorting to using the "Execute R Script" module.  This
is the first in a many-part series on data processing, cleaning, and
filtering using Azure ML - this one focused on a problem I just ran into
with date processing.  When you use the "Execute R Script" module it
attempts to map the incoming data sets into R data types, and then
attempts to map the outgoing data-frame (must be a data frame) into data
types for downstream modules.  This mapping is often where the problem
begins - sometimes it fails to convert incoming data to the types you
expect, and on output only a limited set of R types are supported.

Recently, I had a data-set with a column of date-times in the following
format: "`2014:01:21 17:02:00`".  This is obviously a date to our eyes,
but the system might not see it that way since it's not in a standard
format.  Once I send it into R, how can I figure out what the data-type
converter has done?  The easiest way is to send the classes of your
incoming data to the R output, using the following code:

```R
dataset1 <- maml.mapInputPort(1);

data.set = as.data.frame(lapply(dataset1, class));

maml.mapOutputPort("data.set");
```

I did this, and saw that my date was actually of type `character` - if
it had been in a standard format, it would've been auto-converted
to `POSIXct`.  So it fell to me to convert it - I wanted to convert it
to a date, and then pull out some potential features (date (minus time),
day of week, hour of day), so I wrote the following (the column is
`weirdDateTime`):

```R
data.set$asDateTime = strptime(data.set$weirdDateTime, "%Y:%m:%d %H:%M:%S");
data.set$asDate = as.Date(data.set$asDateTime);
data.set$dayOfWeek = weekdays(data.set$asDate);
data.set$hourOfDay = data.set$asDateTime$hour;
```

I ran this through RStudio to make sure it worked (always a wise move,
don't waste your compute cycles until you need them), and it worked
fine, so I sent it through AzureML... BOOM!  The R module failed, and
gave me a bunch of output, with the important pieces right here:

```
[ModuleOutput] Warning messages:
[ModuleOutput] 
[ModuleOutput] 1: In strptime(data.set$weirdDateTime, "%Y:%m:%d %H:%M:%S") :
[ModuleOutput] 
[ModuleOutput]   unable to identify current timezone 'C':
[ModuleOutput] 
[ModuleOutput] please set environment variable 'TZ'
[ModuleOutput] 
[ModuleOutput] 2: In strptime(data.set$weirdDateTime, "%Y:%m:%d %H:%M:%S") :
[ModuleOutput] 
[ModuleOutput]   unknown timezone 'localtime'
[ModuleOutput] 
[ModuleOutput] DllModuleHost Stop: 1 : DllModuleMethod::Execute. Duration: 00:00:04.6139721
[ModuleOutput] DllModuleHost Error: 1 : Program::Main encountered fatal exception: Microsoft.Analytics.Exceptions.ErrorMapping+ModuleException: Error 1000: RPackage library exception: Failed to convert RObject to DataSet ---> Microsoft.Analytics.Modules.R.ErrorHandling.RException: Failed to convert RObject to DataSet ---> Microsoft.Analytics.Modules.R.ErrorHandling.RNotImplementedException: Parser is not implemented for the Microsoft.MetaAnalytics.RDataSupport.RObject`1[Microsoft.MetaAnalytics.RDataSupport.RObject] type or data is invalid
```

I'll be honest - I burned some cycles on those warning messages - they
seem so bad, and I assumed the data coming back from `strptime` was
garbage.  I tried setting the timezone using a parameter to strptime
(`strptime(data.set$weirdDateTime, "%Y:%m:%d %H:%M:%S", tz="GMT")`) - no
change.  I tried setting the TZ environment variable manually
using `Sys.setenv(TZ="GMT")` - no dice.  So I ran the same code, but
used my other "what class is this?" code to tell me what garbage it
might be generating:

[![r\_type\_conversions](http://www.mikelanzetta.com/wp-content/uploads/2015/01/r_type_conversions-300x144.png)](http://www.mikelanzetta.com/wp-content/uploads/2015/01/r_type_conversions.png)

Hmm, these types look fine.  I spent some time looking around, trying
different things, and finally asked the people on the Azure ML team.
 They told me that they don't yet support the POSIXlt data type on
output, only POSIXct.  It's possible the POSIXlt type will make it into
the GA release, but it's unlikely and it's definitely not there now.  So
what can we do now?  Well, we're almost there - we just need to convert
our POSIXlt to POSIXct before sending it to the output stream and we're
all done - so here's the final script:

```R
data.set = dataset1;
data.set$asDateTime = strptime(data.set$weirdDateTime, "%Y:%m:%d %H:%M:%S");
data.set$asDate = as.Date(data.set$asDateTime);
data.set$dayOfWeek = weekdays(data.set$asDate);
data.set$hourOfDay = data.set$asDateTime$hour;
data.set$asDateTime = as.POSIXct(data.set$asDateTime);
```

Hopefully this simple example gives you some insight into how to
diagnose issues with Azure ML's R module, and some insight into what it
provides and fails to provide.  There's much more to come.

