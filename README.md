Much hackier, inverse version of https://github.com/andyljones/zonotable

This scrapes through your Zotero library (via the web API, so you need to have the web sync enabled), 
and inserts notes and their PDF attachments into notable.

Benefit of this compared to Andy's solution is that you can continue to use Zotero, which has some nice features
like extracting metadata out of a raw .pdf (which hits some proprietary Zotero server), exporting to BibLaTeX, etc. 
Downside is that you need to use Zotero.

The script deletes attachments (but not the metadata) in Zotero once they've been imported, to save space (free Zotero sync tier only offers 300MB).

Need a zotero api key from https://www.zotero.org/settings/keys. Script expects to find `ZOTERO_LIBRARY_ID` and `ZOTERO_API_KEY` environment variables. Needs write access since it modifies tags and deletes items.

I would recommend setting this up to run periodically on your system, or on a server that can sync with your notable directory.
