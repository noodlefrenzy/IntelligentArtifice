Title: Writing a Powershell Snapin for Bing
Date: 2009-06-05 19:16
Author: noodlefrenzy
Category: Software
Tags: Powershell
Slug: writing-a-powershell-snapin-for-bing
Status: published

I’ve been meaning to write a post on how to author custom Powershell
Cmdlets for some time now, as it’s incredibly easy to do and makes an
awesome cmd shell even better.  I’m still more comfortable in tcsh, but
for working in Windows, Powershell makes life a lot easier – and the
fact that the pipeline is composed of objects allows for some serious
craziness.

Anyway, I’ll have a future article on using Powershell itself, but for
now I want to focus on writing cmdlets.  You write cmdlets in .NET as
part of a “snapin” – ‘10 blue links’.  I work on the team and am still
surprised by queries that answer my questions ([98102
weather](http://www.bing.com/search?q=98102+weather&go=&form=QBRE), [seattle
zip code](http://www.bing.com/search?q=seattle+zip+code&go=&form=QBRE))
or make me laugh ([calories in a
squirrel](http://www.bing.com/search?q=calories+in+a+squirrel&go=&form=QBRE)). 
Well, they’ve released a new version of the API to coincide with Bing,
and using it is easy.  For my example, I’ll be building a cmdlet to do
Bing Web Search, and output the results as either a string or an
XDocument.

Bing has a simple developer API (see [here for
details](http://www.bing.com/developers)), and for my purposes I’m
planning on using the REST-based XML binding, allowing simple HTTP GET
queries
like [http://api.search.live.net/xml.aspx?Appid=…&query=foo&sources=web](http://api.search.live.net/xml.aspx?Appid=%E2%80%A6&query=foo&sources=web) to
return XML results (obviously, substituting a valid AppID).

Writing these cmdlets and snapins is not that difficult, but can be
eased even further with the help of [Powershell templates for
VS2008](http://psvs2008.codeplex.com/Release/ProjectReleases.aspx?ReleaseId=26356) ([and
some usage
details...](http://www.gangleri.net/2009/04/21/BuildingPowerShellCmdletsWithVisualStudio2008.aspx)).  
Once these are installed, I create my Get-BingWeb cmdlet as follows:

1.  New-\>Project-\>PowershellCmdlet named BingCmdlets
2.  Add-\>New Item…-\>PowershellCmdlet SnapIn named BingCmdletsSnapin
3.  Add-\>New Item…-\>Powershell Cmdlet named BingWebCmdlet (Note: this
    should really be GetBingWebCmdlet, but to make using the template
    easier I'm leaving as-is)
4.  Add-\>New Item…-\>Class named BingUtil
5.  Add Reference…-\>System.Net (for HttpWebRequest/Response)
6.  Add Reference…-\>System.Xml.Linq (for XDocument)

Then I write some source code (I’ll post the full sln as a tarball
sometime soon – right now all I’ve got is a VS2010 Beta version).  This
code, by the way, is not meant to be production quality (or even
particularly good), so if you find problems with it I’ll refuse to be
surprised :).

I won’t even cover BingCmdletsSnapin.cs, since its implementation is
trivial based on the helpful templates linked above.

BingUtil.cs contains utility methods for doing the query (BingAppId has
been redacted - I want folks to get their own and play with it):

```csharp
private const string BingApiUrlForXml = "http://api.search.live.net/xml.aspx";

public string Search(string sourceType, string searchTerm)
{
  string requestUrl = this.BuildUrl(sourceType, searchTerm);
  HttpWebRequest request = (HttpWebRequest)HttpWebRequest.Create(requestUrl);
  HttpWebResponse response = (HttpWebResponse)request.GetResponse();
  if (response.StatusCode == HttpStatusCode.OK) {
    return this.ReadResponse(response);
  }
  
  throw new IOException("Failed to read response from ["+requestUrl+"].  Received status code "+response.StatusCode);
}

private string BuildUrl(string sourceType, string searchTerm)
{
  return string.Format("{0}?Appid={1}&query={2}&sources={3}",
    BingUtil.BingApiUrlForXml,
    BingUtil.BingAppId,
    searchTerm,
    sourceType);
}

private string ReadResponse(HttpWebResponse response)
{
  using (StreamReader reader = new StreamReader(response.GetResponseStream()))
  {
    return reader.ReadToEnd();
  }
}
```

BingWebCmdlet.cs is the cmdlet itself, containing the parameters, and
the all-important ProcessRecord method.  ProcessRecord is called by
Powershell on cmdlet classes to get them to actually do work.  Output
from ProcessRecord to the next phase of the pipeline (or the screen) is
done via the WriteObject method – write whatever you want, and
Powershell will figure it out.  Anyway, here’s what the code looks like:

```csharp
protected override void ProcessRecord()
{
  BingUtil util = new BingUtil();
  string resultStr = util.Search("web", this.SearchTerm);
  if (this.AsXml)
  {
    XDocument doc = XDocument.Parse(resultStr);
    WriteObject(doc);
  }
  else
  {
    WriteObject(resultStr);
  }
}

[Parameter(Mandatory = true, Position = 1, ValueFromPipelineByPropertyName = true)]
public string SearchTerm { get; set; }

[Parameter(Mandatory = false, ValueFromPipelineByPropertyName = true)]
public SwitchParameter AsXml { get; set; }
```

The parameters are defined via Attributes (as is the Cmdlet itself). 
Important things to note in the code above:

-   I’ve set “Position = 1” on the parameter SearchTerm, meaning you can
    call “Get-BingWeb foo” and it will intuit that “foo” is SearchTerm,
    saving you from having to supply –SearchTerm every time.
-   I’ve set “ValueFromPipelineByPropertyName=true” on both parameters,
    meaning that if incoming pipeline objects contain SearchTerm/AsXml
    parameters, those will be used to fill parameters.  I should also
    most likely set ValueFromPipeline=true on SearchTerm, allowing
    incoming pipeline objects to be converted to strings for search
    terms.
-   The return type SwitchParameter on AsXml makes that parameter behave
    as a switch/flag, turned on by its presence.

Now that we’ve written the snapin, we can build, install, and run it! 
So first, build the snapin dll.  I’ve built it as a 32-bit debug DLL –
if you’ve built the 64-bit version instead, you’ll need to use the
Framework64 version of installutil.exe below.

Install your DLL:

```batch
C:\windows\Microsoft.NET\Framework\v2.0.50727\InstallUtil.exe c:\path\to\dll
```

And you should see output similar to the below:

[![image](http://blogs.msdn.com/blogfiles/milanz/WindowsLiveWriter/WritingaPowershellSnapinforBing_E4B7/image_thumb.png "image")](http://blogs.msdn.com/blogfiles/milanz/WindowsLiveWriter/WritingaPowershellSnapinforBing_E4B7/image_2.png)

Make sure your snapin was registered…

```powershell
PS> get-pssnapin –registered
```

[![image](http://blogs.msdn.com/blogfiles/milanz/WindowsLiveWriter/WritingaPowershellSnapinforBing_E4B7/image_thumb_1.png "image")](http://blogs.msdn.com/blogfiles/milanz/WindowsLiveWriter/WritingaPowershellSnapinforBing_E4B7/image_4.png)

And then add it and execute!

```powershell
PS> add-pssnapin BingCmdlets
PS> get-bingweb sushi
```

The output should look roughly like the below:

[![image](http://blogs.msdn.com/blogfiles/milanz/WindowsLiveWriter/WritingaPowershellSnapinforBing_E4B7/image_thumb_2.png "image")](http://blogs.msdn.com/blogfiles/milanz/WindowsLiveWriter/WritingaPowershellSnapinforBing_E4B7/image_6.png)

Obviously this isn’t the format we’d want for the results, so we can run
it again and get the result as XML.  At that point, we can use LINQ to
extract the values we care about, and format them as CSV or whatever we
want.  We need the “web:” namespace to prefix our XML values, so first I
define that for future use….

```powershell
PS> $webns = “{http://schemas.microsoft.com/LiveSearch/2008/04/XML/web}”
PS> $doc = get-bingweb sushi –asxml
PS> $results = $doc.Descendants($webns + ‘WebResult’)
PS> $results | % { $_.Element($webns+'Title').value + "," + $_.Element($webns+'Url').value }
```

[![image](http://blogs.msdn.com/blogfiles/milanz/WindowsLiveWriter/WritingaPowershellSnapinforBing_BC02/image_thumb.png "image")](http://blogs.msdn.com/blogfiles/milanz/WindowsLiveWriter/WritingaPowershellSnapinforBing_BC02/image_2.png)

I hope this has given you an idea both of what’s possible within
Powershell, and what’s possible via the Bing API.  Both are easy to use,
and provide some incredible power.

As a parting note, you could do all of these operations within
Powershell itself – there’s no real need to write the cmdlets.  However,
if you write the cmdlets and factor your utility classes well, your code
will be cleaner and you’ll find yourself using the Bing API in your C\#
programs, your IronRuby scripts, or elsewhere.  And well-written cmdlets
are easier to incorporate into others’ powershells than scripts, meaning
your code will benefit others.

[Update: 2009-June-09]

 I've published my example on codeplex (as a zip, not a tgz,
sorry): [http://bingable.codeplex.com/ ](http://bingable.codeplex.com/ "http://bingable.codeplex.com/")

