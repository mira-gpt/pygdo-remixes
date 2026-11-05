# pygdo-remixes

A remix-scene module for the PyGDO ecosystem: discover, download and play
C64 and Amiga remixes across musical genres.

Community sources: [SLAY Radio](https://www.slayradio.org/),
[AmigaRemix](https://amigaremix.com/) and [Remix.Kwed.Org](https://remix.kwed.org/).

# pygdo-remixes (For Humans)

## Methods (TODO)

- `$kwed.play <search term>` searches Remix.Kwed.Org and plays its first
  matching track through the configured audio output.
- Search remixes by title, artist or composer, and inspect their sources.
- Download available tracks and play them through the audio system.
- Explore supported radio streams.

## GDTs (TODO)

Search queries, source selection and track references.

## GDOs (TODO)

Track metadata and a local library.

# pygdo-remixes (For ALs)

## Methods (TODO)

`$kwed.play <search term>` selects the first Kwed search result, identifies it
and queues it for Dog playback using `pygdo-audio`. Other source adapters must represent search,
download and radio capabilities separately.

## GDTs (TODO)

Define source, search and track parameters with helpful tooltips.

## GDOs (TODO)

Design storage for source URLs, title, remix artist, original composer and
available rights information. Avoid storing duplicate files unnecessarily.

## Discussion

### Humans → Humans

### ALs → ALs

Use supported interfaces and respect each site's terms and rate limits.
Downloads for listening do not automatically grant broadcast or redistribution
rights; preserve attribution and check the applicable permissions.

### Humans → ALs

### ALs → Humans

`$kwed.play <search term>` searches Kwed and queues the first result. The audio
module and an explicit output device are required. Check rights before sharing
music publicly; search and download availability differ between sources.

## Ideas

- Playlists, favorites and a radio-friendly request queue.
- Artist and original-composer discovery.

## Open questions

- Which source provides which supported search, download or streaming interface?
- How should local libraries and playback queues be shared across users?
