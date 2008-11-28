import os
import re
import urllib2
import urlparse

from pysqlite2 import dbapi2 as sqlite
from BeautifulSoup import BeautifulSoup


ignorewords = set(['the', 'of', 'to', 'and', 'a', 'in', 'is', 'it'])


class crawler:
  def __init__(self, dbname):
    self.con = sqlite.connect(dbname)

  def __del__(self):
    self.con.close()

  def dbcommit(self):
    self.con.commit()

  def getentryid(self, table, field, value, createnew=True):
    """Returns an entry id and creates it if it is not present."""
    return None

  def addtoindex(self, url, soup):
    """Indexes a given page."""
    print 'Indexing', url

  def gettextonly(self, soup):
    """Extracts all text from a html page, i.e. strips the tags."""
    v = soup.string
    if v == None:
      return '\n'.join([self.gettextonly(t) for t in soup.contents])
    else:
      return v.strip()

  def separatewords(self, text):
    """Splits words by non-whitespace characters."""
    splitter = re.compile(r'\W*')
    return [s.lower() for s in splitter.split(text) if s != '']

  def isindexed(self, url):
    return False

  def addlinkref(self, urlfrom, urlto, linktext):
    """Add a link between two pages."""
    pass

  def crawl(self, pages, depth=2):
    """Find pages linked from a root set in BFS order, up to a given depth."""
    for i in range(depth):
      newpages = set()
      for page in pages:
        try:
          print page
          c = urllib2.urlopen(page)
        except urllib2.URLError:
          print 'Could not load', page
          continue

        if c.headers.type not in set(['text/html', 'text/plain']):
          print 'Skipping', page, c.headers.type
          continue

        soup = BeautifulSoup(c.read())
        self.addtoindex(page, soup)

        links = soup.findAll('a')
        for link in links:
          if 'href' in dict(link.attrs):
            url = urlparse.urljoin(page, link['href'])
            if url.find("'") != -1:
              print 'IGNORING', url
              continue
            url = url.split('#')[0]
            if url[0:4] == 'http' and not self.isindexed(url):
              newpages.add(url)
            linktext = self.gettextonly(link)
            self.addlinkref(page, url, linktext)

        self.dbcommit()

      pages = newpages

  def createindextables(self):
    """Create the database tables."""
    self.con.execute('create table urllist(url)')
    self.con.execute('create table wordlist(word)')
    self.con.execute('create table wordlocation(urlid, wordid, location)')
    self.con.execute('create table link(fromid integer, toid integer)')
    self.con.execute('create table linkwords(wordid, linkid)')

    self.con.execute('create index urlidx on urllist(url)')
    self.con.execute('create index wordidx on wordlist(word)')
    self.con.execute('create index wordurlidx on wordlocation(wordid)')
    self.con.execute('create index urlfromidx on link(fromid)')
    self.con.execute('create index urltoidx on link(toid)')
    self.dbcommit()



if __name__ == '__main__':
  crawl = crawler('searchindex.db')

  if not os.path.exists('searchindex.db'):
    crawl.createindextables()

  crawl.crawl(['http://amnoid.de/'], depth=3)