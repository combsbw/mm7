/* MM7 Learning Hub service worker.
   Job: after the first visit, the whole Hub (the page, the icons, the fonts) is on the device, so it opens with no network.
   It touches nothing else: it never sees IndexedDB, never caches a response from anywhere but this folder, and never makes
   a request of its own beyond fetching these files. The learner record is not here.
   Updating: a new build installs quietly beside the old one and WAITS. The page offers "reload"; the new version takes over
   only when the person says so, so nobody is switched mid-problem. */
'use strict';
var VERSION = 'ab3b05a5e5';                       // a hash of every file below: a new build is a new worker
var CACHE = 'mm7-hub-' + VERSION;
var ASSETS = ["index.html", "manifest.webmanifest", "icons/apple-touch-icon.png", "icons/favicon-32.png", "icons/icon-192.png", "icons/icon-512.png", "icons/icon-maskable-512.png", "icons/icon.svg", "fonts/atkinson-hyperlegible-mono-latin-400-normal.woff2", "fonts/atkinson-hyperlegible-mono-latin-500-normal.woff2", "fonts/atkinson-hyperlegible-next-latin-400-normal.woff2", "fonts/atkinson-hyperlegible-next-latin-500-normal.woff2", "fonts/atkinson-hyperlegible-next-latin-700-normal.woff2", "fonts/fonts.css"];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) {
    // one request each, bypassing the HTTP cache so a half-updated host cannot give us a mixed set
    return Promise.all(ASSETS.map(function (u) { return c.add(new Request(u, { cache: 'reload' })); }));
  }));
});

self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (ks) {
    return Promise.all(ks.filter(function (k) { return k.indexOf('mm7-hub-') === 0 && k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener('message', function (e) {
  if (e.data === 'SKIP_WAITING') self.skipWaiting();
  else if (e.data === 'VERSION' && e.ports && e.ports[0]) e.ports[0].postMessage(VERSION);
});

self.addEventListener('fetch', function (e) {
  var r = e.request;
  if (r.method !== 'GET') return;
  var u = new URL(r.url);
  if (u.origin !== self.location.origin) return;                 // another site: not ours to touch
  e.respondWith(caches.open(CACHE).then(function (c) {
    // every page load, whatever the #hash, is the Hub
    if (r.mode === 'navigate') return c.match('./index.html').then(function (m) { return m || fetch(r); });
    return c.match(r, { ignoreSearch: true }).then(function (m) { return m || fetch(r); });
  }));
});
