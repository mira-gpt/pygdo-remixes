# pygdo-remixes

A remix-scene module for the PyGDO ecosystem: discover, download and play
C64 and Amiga remixes across musical genres.

Community sources: [SLAY Radio](https://www.slayradio.org/),
[AmigaRemix](https://amigaremix.com/) and [Remix.Kwed.Org](https://remix.kwed.org/).

# pygdo-remixes (For Humans)

## Methods (TODO)

- Search remixes by title, artist or composer, and inspect their sources.
- Download available tracks and play them through the audio system.
- Explore supported radio streams.

## GDTs (TODO)

Search queries, source selection and track references.

## GDOs (TODO)

Track metadata and a local library.

# pygdo-remixes (For ALs)

## Methods (TODO)

Design search, download and playback methods with the community. Playback
should integrate with `pygdo-audio`; source adapters must represent search,
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

This is an idea repository: source integrations and commands are not yet
implemented. Search and download availability can differ between sources.

## Ideas

- Playlists, favorites and a radio-friendly request queue.
- Artist and original-composer discovery.

## Open questions

- Which source provides which supported search, download or streaming interface?
- How should local libraries and playback queues be shared across users?
