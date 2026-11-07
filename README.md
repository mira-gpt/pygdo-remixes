# pygdo-remixes

A remix-scene module for the PyGDO ecosystem: discover, download and play
C64 and Amiga remixes across musical genres.

Community sources: [SLAY Radio](https://www.slayradio.org/), [HVSC](https://hvsc.c64.org/)
[AmigaRemix](https://amigaremix.com/) and [Remix.Kwed.Org](https://remix.kwed.org/).

SID playback requires the `sidplayfp` executable and FFmpeg; these are system
dependencies, not Python packages. On Debian/Ubuntu install `sidplayfp ffmpeg`
with the system package manager. Availability alone does not verify the audio
route or permission to broadcast individual tracks.

# pygdo-remixes (For Humans)

## Methods (TODO)

- `$kwed.play <search term>` searches Remix.Kwed.Org and plays its first
  matching track through the configured audio output.
- Search remixes by title, artist or composer, and inspect their sources.
- Download available tracks and play them through the audio system.
- Explore supported radio streams.
- `$remixes.sid <search term>` searches HVSC paths and SID title/author
  headers and stores the first 25 numbered results in the current PyGDO
  session. `$remixes.sid <number>` queues a result for playback; use
  `--search=1` to search for a numeric term. Select a subtune with
  `$remixes.sid --subtune=2 <number>` (default: 1). `$remixes.sidlike <number>`
  likes a result from the current session. Search numbers are session-scoped
  and are replaced by the next SID search in that session.
- Playback streams `sidplayfp`'s selected subtune through a temporary named
  WAV pipe (up to three minutes) and FFmpeg to the configured
  audio sink. The play counter increments once when FFmpeg reports positive
  output progress; this does not prove the sound reached a listener. Queueing,
  failed decoding, and failure before output do not increment the counter.
  Installing/updating the module schema is required for SID records and likes.

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
