self.addEventListener('install', (e) => self.skipWaiting());
self.addEventListener('fetch', (e) => {}); // no-op is enough to make the page installable
