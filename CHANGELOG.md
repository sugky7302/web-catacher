# CHANGELOG

## Todo:
- [x] add some mechanisms to prevent in-debug.
  - [x] headers
  - [x] proxy
  - [x] random delay time
  - [x] referer
  - [x] user-agent
- [ ] add downloader_config.json to set keywords of common websites.
- [ ] expand to a genreal downloader and restruct the code.

## 0.2.0.2 - 2021-09-26 - optimize

### Added:
- add a new class Requests, which wraps requests, to prevent to be hampered by websites.
- add searchAll to find all videos of assigned pages.

### Changed:
- rewrite the code by beautifulsoup.
- use Thread to accelerate the efficiency of download.
- the function of search is changed to find assigned page.

### Fixed:
- fix always to download the same page.
- page will be no longer bigger than the max_page.
- fix requesting too quickly lead to no response.

## 0.1.0.0 - 2021-09-25 - init
- realize a simple url catcher of pornhub.