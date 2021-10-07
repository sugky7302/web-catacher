# CHANGELOG

## 1.0.0.5 - 2021-10-07 - release

### Fixed:
- **[downloader]** fix a problem of calling wrong function name.

## 0.2.0.4 - 2021-09-28 - optimize

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