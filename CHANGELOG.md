# Changelog

All notable changes to ScanSnack are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

New entries go under *Unreleased*. When a release is made, the *Create Release* workflow turns
*Unreleased* into the new version's section and uses it as the release notes.

## [Unreleased]

### Added

- Fix to try: *#24: Double feeds go unnoticed* (iX1500). Double feeds are detected, and after a double feed
  or a jam while a page is read the scan waits as it does with ScanSnap Home: put the sheets back and press
  *Scan* on the scanner to continue, or *Finish* to end the scan (pages scanned before are kept). The status
  line says what the scanner is waiting for; without an answer the scan ends after 5 minutes. A double-fed
  sheet is kept only if *Finish* is followed by saving the image on the scanner. Network scans (AirScan)
  end at once. A crumpled sheet can be reported as a double feed too.
- iX1500 (library): a computer can have several touch panel profiles, each with its own icon and colour,
  and the client can ask which one was tapped for a press. The client can also be told when the scanner
  has powered on.
- iX1500 protocol notes: double feed and jam sequences and how the batch is held and continued, more C2
  status bits with SANE's names, sense 3/80/02 (cover open), the color/300 block for all color modes,
  the boot notice, which profile was tapped, button notifications after the session has closed, and
  the touch panel's profile icons and colours.

### Changed

- iX1500: the client listens for the Scan button while it connects, not only once connected, so a press
  can be received while the connection is still being set up.
- iX1500: "Document – Color" (color/300) scans use the parameter block ScanSnap Home sent for a 300 dpi
  color scan, so `scansnap scan --mode color --dpi 300` no longer warns that it is not backed by captures.

### Fixed

- iX1500: a sheet that jams while it is being read is reported as a paper jam, instead of as an
  "unexpected chunk header" error.
- iX1500: when a scan stops with an error and the scanner cannot be released afterwards, the original
  error is reported, not the failed release.
- iX1500: a press on the touch panel is no longer ignored when the scanner was switched off and on and the
  press got the same number as the last one before.

## [0.6.2] - 2026-11-19

### Added

- iX500: when the scanner does not accept its Wi-Fi password, the app now asks for it and remembers it,
  instead of failing on every start. The message says whether the factory password (the last four digits
  of the serial number) was tried or whether the scanner's name hides the serial number.

### Fixed

- Error reports no longer show the iX500 password setting as `<private> default`.

## [0.6.1] - 2026-11-08

### Changed

- iX500: when another computer is using the scanner over Wi-Fi or USB, the error now says so, names that
  computer's address if the scanner reports it, and explains what to do instead of "unknown reason". A
  wrong scanner password is reported as such.

## [0.6.0] - 2026-11-03

### Added

- Error reports: after an unexpected scan error, or any time from *Help → Send Error Report …*, the app
  shows a detailed report (app version, system, scanner model and state, error and recent log) with
  personal data removed. You can check and edit it, then send it to scansnack@posteo.de with your mail
  program in one click, copy it or save it.
- New *Fixes* menu: switch on fixes that are still being tested, each labelled with its issue number.
  The previous behaviour stays the default until a fix is confirmed.
- Fix to try: *#19: Scan hangs on “Processing”* (iX1500). When setting up the app's user on the scanner
  fails (for example with the error "conn_user"), the app always ends pairing, so the touch panel no longer
  hangs on "Processing" until the scanner is switched off, and the error says what the scanner replied.

### Fixed

- `scansnap status` no longer fails when the scanner's user list has no `conn_user`; it also prints the
  keys of the reply.

## [0.5.0] - 2026-11-01

### Added

- Native Windows 11 ARM64 app downloads, including automatic updates, for PCs such as Snapdragon laptops.

## [0.4.2] - 2026-11-01

### Fixed

- When an update is available at startup and no scanner is connected, the update window and the
  *Connect Scanner* window no longer open together and block each other: the update is offered first,
  and *Connect Scanner* follows once that window is closed.

## [0.4.1] - 2026-11-01

### Fixed

- *Search Network* finds the scanner even while it is connected (to the app, ScanSnap Home or another
  computer): such a scanner ignores the search, so the app now asks the entered address directly.
- Running the test suite no longer overwrites the app's saved scanner IP address with a sample address.

## [0.4.0] - 2026-11-01

### Added

- ScanSnap iX500 support in the app and on the command line (`scansnap ix500`): the app recognizes the
  model on its own; discovery, device info with page and roller counters, scans at 150 to 600 dpi with page
  size and multifeed detection, and scanning on the scanner's Scan button.
- With an iX500, the Scan button shows "Load paper" and is dimmed while the feeder is empty.
- Protocol write-up for the iX500 Wi-Fi dialect in `docs/protocol-ix500.md`.
- A list of all ScanSnap models and whether ScanSnack supports them (`docs/models.md`, also on the website).

### Changed

- The protocol docs now have one write-up per model: the iX1500 write-up moved to `docs/protocol-ix1500.md`,
  and `docs/protocol.md` is an overview of the models, what they share and where they differ.
- The disclaimer and the iX500 write-up name all sources of the iX500 findings, including the static
  analysis of ScanSnap Home for interoperability.

## [0.3.2] - 2026-10-30

### Fixed

- The Windows download is built again; the release build failed while reading the project version.

## [0.3.1] - 2026-10-30

### Added

- A changelog: this page, also on the website, and in the release notes of every new version.
- A guide to the AirScan bridge, on the website and in `docs/airscan.md`: how to start it, how to scan
  from Image Capture (*Digitale Bilder*) and Preview, supported options, limitations and
  troubleshooting. The bridge is also listed among the features.

### Changed

- The README and the website call the project ScanSnack throughout.
- The command line, log output and error messages are now in English throughout, as are the code
  comments and developer docs.

## [0.3.0] - 2026-10-29

### Added

- **Updates with one click**: on start the app checks GitHub for a new release and offers to install
  it, then restarts as the new version. *Later* asks again next time, *Skip This Version* waits for the
  next one, and the check can be turned off in the *Help* menu.
- Releases carry a `SHA256SUMS` file; the app checks every download against it.
- The website has an app page with screenshots, the feature list and download buttons for the latest
  release.

## [0.2.0] - 2026-10-29

First release with ready-made apps.

### Added

- Desktop app "ScanSnack" for macOS (Apple Silicon and Intel), Windows and Linux: scan over Wi-Fi,
  profiles, double-sided, remove blank pages and background, every scan saved right away as a PDF,
  document list with page editing, help for paper problems, light and dark mode.
- The *Scan* button on the scanner's touch panel starts a scan in the app.
- Protocol client and command line tool `scansnap` (claim, scan, eSCL/AirScan bridge for the macOS
  scan dialog).
- Protocol write-up, disclaimer and website on GitHub Pages.

[Unreleased]: https://github.com/elte0/scansnack/compare/v0.6.2...HEAD
[0.6.2]: https://github.com/elte0/scansnack/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/elte0/scansnack/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/elte0/scansnack/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/elte0/scansnack/compare/v0.4.2...v0.5.0
[0.4.2]: https://github.com/elte0/scansnack/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/elte0/scansnack/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/elte0/scansnack/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/elte0/scansnack/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/elte0/scansnack/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/elte0/scansnack/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/elte0/scansnack/releases/tag/v0.2.0
