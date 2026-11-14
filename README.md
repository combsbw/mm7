# Math Mammoth Grade 7 — Learning Hub (installable app)

This folder is the Learning Hub as an app. Once it has been opened one time with a connection, it works with **no internet at all**,
and everything a student does is saved **on that device**. Nothing is sent anywhere: there are no accounts and no tracking.

Build: `c65cbe0239`

## Install from GitHub Pages (the easy way to get https)

This repository is the app itself, ready to serve. Turn on GitHub Pages once:

1. On GitHub, open the repository → **Settings** → **Pages**.
2. Under **Build and deployment**, choose **Deploy from a branch**, branch **main**, folder **/ (root)**, then **Save**.
3. After a minute the site is live at **https://combsbw.github.io/mm7/**. Open that address in Safari on the iPhone or iPad
   (with a connection), then **Share → Add to Home Screen**. Open the new icon once while still online so it can finish
   saving itself; after that it runs with no connection.

GitHub Pages is public for a public repository (anyone with the address can open it). A private repository can use Pages only
on a paid GitHub plan.

To update the app later: replace these files with a newer build and push. The installed app notices the next time it is
opened online and shows **A new version is ready — Reload**. The student's saved work is not touched by an update.

No GitHub? See **LOCAL_HTTPS_IOS.md** for serving it from a computer at home with your own certificate.

## Try it on this computer (two minutes)

1. Open a terminal in this folder and run: `python3 serve.py`
2. The Hub opens at <http://localhost:8000>. In Chrome or Edge, the address bar shows an **Install** icon; or open Settings in the Hub
   and press **Install**.

Leave the terminal window open while you use it from the browser; after it has been installed, the installed app opens on its own,
even with the terminal closed and the computer offline.

## Put it online (so phones and tablets can install it)

A phone needs the folder served over **https**, which any static host does for free. Upload this whole folder, as it is, to one of:

- **Netlify** — drag the folder onto the "Netlify Drop" page.
- **Cloudflare Pages** or **GitHub Pages** — create a site from the folder.

Use the address the host gives you, open it once with a connection, and install it:

| Device | How to install |
|---|---|
| Android (Chrome) | Menu (⋮) → **Install app**, or the Install button in the Hub's Settings |
| iPhone or iPad (Safari) | **Share** → **Add to Home Screen** |
| Windows, Mac, Chromebook (Chrome or Edge) | the **Install** icon in the address bar |

**Install first, then start working.** On iPhone and iPad (and in some browsers) the installed app keeps its own saved record, separate
from the same address opened in a browser tab. If a student has already started in a tab, move the record: in the tab open
**Settings → Export**, then in the installed app open **Settings → Import**.

## Where the work is saved

In the browser's own database on the device (IndexedDB). The Hub asks the browser to keep it permanently; Settings → **On this device**
says whether the browser agreed. Two things still apply to any web app:

- **Clearing the browser's "site data" erases the record.** So does Reset in the Hub's Settings.
- **Export now and then.** Settings → **Export** saves one JSON file with everything (every Path, Review, Exam and the Hub's own record).
  It is the backup, the way to move to a new device, and a file a parent can read. **Import** puts it back.

The Hub you may have opened by double-clicking `MM7_Learning_Hub.html` keeps its own, separate record. To bring that work across,
**Export** there and **Import** here. A file exported from any earlier version imports into this one.

## Updating

When a newer build is put in the same place, the app notices the next time it is opened with a connection and shows
"**A new version is ready — Reload**". Nothing changes until that button is pressed, so no one is switched in the middle of a problem.
The saved record is not touched by an update.

## What is in this folder

| File | What it is |
|---|---|
| `index.html` | the Hub, with every chapter Path, Review and Exam inside it |
| `sw.js` | the service worker: keeps a copy of the files below on the device so the Hub opens offline |
| `manifest.webmanifest`, `icons/` | the name, colours and icon the device uses when it is installed |
| `fonts/` | the typeface (Atkinson Hyperlegible, SIL Open Font License), so it looks the same offline |
| `serve.py` | runs the folder on your own computer |
| `_headers` | tells Netlify or Cloudflare Pages to re-check `sw.js` every time, so updates are found |

## The Dojo

The **Dojo** tab is the practice arena. It brings skills back when they are due, strengthens weak ones and mixes in new
ground, and nothing in it is locked.

- **Blob Roll**: quick reps with friendly numbers against a clock that drains; right answers pour seconds back.
- **Quest**: a ridiculous story along a winding route of energy wells; each stop uses the answer of the stop before.
- **Superlative**: three full-strength problems that each use several skills, with a multiplier.

Every answer goes into the same learner record as the Paths and Reviews, and appears in History. Easy-number reps refresh
memory in full and fill a skill up to 4 of its 10 blobs; the rest comes from full-strength problems.


## Skills & Tactics

Every chapter has a **Skills & Tactics** tab: a chapter sheet with the highest-value tactics, a formula bank and two tools,
followed by one card for every level of the Path (what to do, an example, what to watch for). The tools are a
words → symbols decoder and a triangle that works for any "a = b · c" relationship (distance = speed · time,
part = percent · whole, C = π · d, and nine more): tap the letter you want and the formula for it appears. A level's card
also shows in its level drawer and at the start of its Dojo warm-up. The tab has a Print button for a paper copy.

## On the Mac, with autosave to a file (optional)

`mm7_helper.py` runs this same app on the Mac and saves everything to one SQLite file as it happens.

1. Double-click **Start Learning Hub.command** (the first time: right-click it, choose Open, then Open), or run `python3 mm7_helper.py`.
2. The Hub opens at <http://localhost:8377>. Leave the helper's window open while working.

- Data: `~/Documents/MM7 Data/mm7.sqlite` (the learner record and one row per problem answered). Backups: `~/Documents/MM7 Data/backups/`.
- The address `localhost:8377` and the GitHub Pages address are separate apps to the browser. Move a record between them, or to a
  tablet, with Settings → Export and Import. Import replaces the record on that device, so always export from the device with the latest work.
- Needs Python 3.6 or newer and nothing else. Works with no internet.
