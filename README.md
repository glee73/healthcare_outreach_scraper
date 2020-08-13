INTRODUCTION:

This webscraper was written for homelessshelterdirectory.org. I was leading part 
of a project at GetUsPPE.org where I needed a centralized database for all of the
homeless shelters in the US. For one, we were conducting a risk analysis in 
ArcGIS that needed the addresses of the shelters in a CSV. My team also needed 
a more time-efficient way to compile a shelter call list.

TECHNOLOGIES: 

BeautifulSoup, Pandas, Numpy

OVERVIEW:

My approach to web scraping the site as quite naive, but it was unavoidable 
because there was no rhyme or reason to the URL addresses. The website was 
structured so that each state had a page with all of its cities, and then each 
city itself had a page full of shelter listings. I iterated through each state, 
scraping the city URLs, then went through the cities and extracted the shelter 
URLs into a set (there were always duplicate listings in many of the cities, 
sometimes even ones in neighboring states). Then, I parsed the names, addresses,
and contact info of each shelter into a global list, which I would eventually 
turn into a dataframe, remove remaining duplicates, and clean the information into
the appropriate columns. I used the requests package to access the URLs, as well 
as sleep from the time package to avoid overwhelming the server.

BUGS/SHORTCOMINGS:

This was my first time working with real-life data, so I did not anticipate it
to be so messy. I should have taken a look at more of the data before moving
on to run my program on the entire website. If that had been the case, I would
have caught special cases earlier and created an output file with cleaner data.
But at the end of the day, this served our purposes quite well!

Next time I write a web scraper, I will also look into multithreading because
this was really slow.
