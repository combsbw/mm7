#!/usr/bin/env python3
"""The Learning Hub helper: serves the Hub on this computer and saves everything to one SQLite file.

  usage:  python3 mm7_helper.py                 then the Hub opens at http://localhost:8377
          python3 mm7_helper.py --data "~/Documents/MM7 Data" --port 8377 --no-open

What it does
  * Serves this folder (the installable Hub) to this computer only (127.0.0.1). Works with no internet connection.
  * Autosave: every change the Hub makes is written at once to  <data>/mm7.sqlite
        kv        the learner record, exactly the keys the Hub's own export holds
        problems  one row per problem answered: where it came from, its skills, the result, the text, the answer given,
                  the right answer, and the whole problem as shown (HTML) with its worked steps
  * Backups, made as the record changes (at most one every few minutes):
        <data>/backups/MM7_Learner_Record_YYYY-MM-DD.json   importable in the Hub (Settings, Import) on any device
        <data>/backups/mm7_YYYY-MM-DD.sqlite                a copy of the database
    The newest 30 of each are kept.
  * If the browser's own storage is ever cleared, the Hub is restored from the file the next time it opens here.

Reading the data yourself
  sqlite3 "<data>/mm7.sqlite" "select date_local, section, ok, question_text from problems order by t desc limit 10"
  pandas:  import sqlite3, pandas as pd; df = pd.read_sql("select * from problems", sqlite3.connect("mm7.sqlite"))

Needs Python 3.6 or newer and nothing else. Stop it with Ctrl+C; nothing is lost (every write is already on disk)."""
import argparse, datetime, glob, http.server, json, os, socketserver, sqlite3, sys, threading, time, urllib.parse, webbrowser

VERSION = 1
HERE = os.path.dirname(os.path.abspath(__file__))
MAX_BODY = 64 * 1024 * 1024
BACKUP_EVERY = 300          # seconds between backups while the record is changing
KEEP = 30
PCOLS = ['id', 't', 'date_local', 'time_local', 'source', 'section', 'where_in_section', 'chapter', 'skills', 'ok', 'credit', 'seconds',
         'used_help', 'error_tag', 'tier', 'question_text', 'student_answer', 'correct_answer', 'problem_html', 'steps_json', 'saved']


class Store:
    def __init__(self, data_dir):
        self.dir = data_dir
        os.makedirs(os.path.join(data_dir, 'backups'), exist_ok=True)
        self.file = os.path.join(data_dir, 'mm7.sqlite')
        self.lock = threading.RLock()
        self.db = sqlite3.connect(self.file, check_same_thread=False)
        self.db.execute('pragma journal_mode=wal')
        self.db.execute('pragma synchronous=normal')
        self.db.executescript('''
            create table if not exists kv (key text primary key, value text not null, updated real not null);
            create table if not exists problems (
                id text primary key, t real, date_local text, time_local text, source text, section text, where_in_section text,
                chapter integer, skills text, ok integer, credit real, seconds real, used_help integer, error_tag text, tier integer,
                question_text text, student_answer text, correct_answer text, problem_html text, steps_json text, saved real);
            create index if not exists problems_t on problems (t);
            create index if not exists problems_source on problems (source, chapter);
            create table if not exists meta (key text primary key, value text);
        ''')
        self.db.execute("insert or ignore into meta values ('created', ?)", (datetime.datetime.now().isoformat(timespec='seconds'),))
        self.db.execute("insert or replace into meta values ('helper_version', ?)", (str(VERSION),))
        self.db.commit()
        self.dirty_since = None
        self.last_backup = 0

    # ---- the learner record
    def kv_all(self):
        with self.lock:
            return {k: v for k, v in self.db.execute('select key, value from kv')}

    def kv_write(self, sets, dels):
        now = time.time()
        with self.lock:
            for k, v in sets.items():
                if isinstance(k, str) and isinstance(v, str):
                    self.db.execute('insert or replace into kv (key, value, updated) values (?, ?, ?)', (k, v, now))
            for k in dels:
                if isinstance(k, str):
                    self.db.execute('delete from kv where key = ?', (k,))
            self.db.commit()
            if self.dirty_since is None:
                self.dirty_since = now
        self.maybe_backup()

    # ---- problems: a row keeps what it has; new non-empty fields are added (the app writes the whole problem, the Hub its facts)
    def problems_merge(self, rows):
        now = time.time()
        n = 0
        with self.lock:
            for r in rows:
                if not isinstance(r, dict) or not isinstance(r.get('id'), str):
                    continue
                t = r.get('t')
                loc = time.localtime(t / 1000.0) if isinstance(t, (int, float)) and t > 0 else None
                skills = r.get('skills')
                steps = r.get('steps')
                vals = {
                    'id': r['id'], 't': t, 'date_local': time.strftime('%Y-%m-%d', loc) if loc else None, 'time_local': time.strftime('%H:%M:%S', loc) if loc else None,
                    'source': r.get('source') or None, 'section': r.get('section') or None, 'where_in_section': r.get('where') or None, 'chapter': r.get('chapter'),
                    'skills': ';'.join(skills) if isinstance(skills, list) and skills else None, 'ok': r.get('ok'), 'credit': r.get('credit'),
                    'seconds': round(r['ms'] / 1000.0, 1) if isinstance(r.get('ms'), (int, float)) and r.get('ms') else None, 'used_help': r.get('help'), 'error_tag': r.get('tag') or None, 'tier': r.get('tier'),
                    'question_text': r.get('q') or None, 'student_answer': r.get('entry') if r.get('entry') not in (None, '') else None, 'correct_answer': r.get('show') if r.get('show') not in (None, '') else None,
                    'problem_html': r.get('qh') or None, 'steps_json': json.dumps(steps) if isinstance(steps, list) and steps else None, 'saved': now}
                # (written without UPSERT so the SQLite that ships with an older macOS works)
                self.db.execute('insert or ignore into problems (id) values (?)', (vals['id'],))
                cols = [c for c in PCOLS if c != 'id']
                self.db.execute('update problems set %s where id = ?' % ', '.join('%s = coalesce(?, %s)' % (c, c) for c in cols), [vals[c] for c in cols] + [vals['id']])
                n += 1
            self.db.commit()
        return n

    def problem_row(self, pid):
        with self.lock:
            cur = self.db.execute('select %s from problems where id = ?' % ', '.join(PCOLS), (pid,))
            r = cur.fetchone()
        if not r:
            return None
        d = dict(zip(PCOLS, r))
        return {'id': d['id'], 't': d['t'], 'source': d['source'], 'section': d['section'], 'where': d['where_in_section'], 'chapter': d['chapter'],
                'skills': d['skills'].split(';') if d['skills'] else [], 'ok': d['ok'], 'credit': d['credit'], 'ms': int(d['seconds'] * 1000) if d['seconds'] else 0, 'help': d['used_help'],
                'tag': d['error_tag'] or '', 'tier': d['tier'], 'q': d['question_text'] or '', 'entry': d['student_answer'] or '', 'show': d['correct_answer'] or '',
                'qh': d['problem_html'] or '', 'steps': json.loads(d['steps_json']) if d['steps_json'] else None}

    def problem_ids(self):
        with self.lock:
            return [r[0] for r in self.db.execute('select id from problems')]

    def problems_clear(self):
        with self.lock:
            self.db.execute('delete from problems')
            self.db.commit()

    def counts(self):
        with self.lock:
            return {'keys': self.db.execute('select count(*) from kv').fetchone()[0], 'problems': self.db.execute('select count(*) from problems').fetchone()[0],
                    'whole_problems': self.db.execute('select count(*) from problems where problem_html is not null').fetchone()[0]}

    # ---- backups
    def maybe_backup(self, force=False):
        now = time.time()
        with self.lock:
            if not force and (self.dirty_since is None or now - self.last_backup < BACKUP_EVERY):
                return None
            self.last_backup = now
            self.dirty_since = None
            day = datetime.date.today().isoformat()
            keys = self.kv_all()
            if not keys:
                return None
            bdir = os.path.join(self.dir, 'backups')
            rec = os.path.join(bdir, 'MM7_Learner_Record_%s.json' % day)
            tmp = rec + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump({'format': 'mm7-learner-record', 'version': 1, 'exported': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'by': 'mm7_helper', 'keys': keys}, f)
            os.replace(tmp, rec)
            dbc = os.path.join(bdir, 'mm7_%s.sqlite' % day)
            try:
                dst = sqlite3.connect(dbc + '.tmp')
                self.db.backup(dst)                      # Python 3.7+
                dst.close()
                os.replace(dbc + '.tmp', dbc)
            except Exception:
                try:
                    os.remove(dbc + '.tmp')
                except OSError:
                    pass
            for pat in ('MM7_Learner_Record_*.json', 'mm7_*.sqlite'):
                for old in sorted(glob.glob(os.path.join(bdir, pat)))[:-KEEP]:
                    try:
                        os.remove(old)
                    except OSError:
                        pass
            return rec


def make_handler(store, app_dir, port):
    allowed_hosts = {'localhost:%d' % port, '127.0.0.1:%d' % port, '[::1]:%d' % port}

    class Handler(http.server.SimpleHTTPRequestHandler):
        extensions_map = dict(http.server.SimpleHTTPRequestHandler.extensions_map, **{'.webmanifest': 'application/manifest+json', '.js': 'text/javascript', '.woff2': 'font/woff2'})

        def translate_path(self, path):          # serve the app folder whatever the working directory is
            rel = urllib.parse.unquote(urllib.parse.urlsplit(path).path).lstrip('/')
            full = os.path.normpath(os.path.join(app_dir, rel))
            return full if full.startswith(app_dir) else app_dir

        def log_message(self, *a):
            pass

        def end_headers(self):
            if self.path.split('?')[0].endswith('sw.js'):
                self.send_header('Cache-Control', 'no-cache')
            super().end_headers()

        def _json(self, obj, code=200):
            body = json.dumps(obj).encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)

        def _local(self):      # only pages this helper served may talk to it (guards against other sites and DNS tricks)
            if self.headers.get('Host', '') not in allowed_hosts:
                return False
            origin = self.headers.get('Origin')
            return origin is None or urllib.parse.urlsplit(origin).netloc in allowed_hosts

        def do_GET(self):
            u = urllib.parse.urlsplit(self.path)
            if '/api/' not in u.path:
                return super().do_GET()
            if not self._local():
                return self._json({'error': 'forbidden'}, 403)
            name = u.path.split('/api/', 1)[1]
            if name == 'ping':
                return self._json(dict({'app': 'mm7-helper', 'version': VERSION, 'file': store.file}, **store.counts()))
            if name == 'kv':
                return self._json({'keys': store.kv_all()})
            if name == 'problems/ids':
                return self._json({'ids': store.problem_ids()})
            if name == 'problems/get':
                q = urllib.parse.parse_qs(u.query)
                return self._json({'row': store.problem_row((q.get('id') or [''])[0])})
            return self._json({'error': 'not found'}, 404)

        def do_POST(self):
            u = urllib.parse.urlsplit(self.path)
            if '/api/' not in u.path or not self._local():
                return self._json({'error': 'forbidden'}, 403)
            try:
                n = int(self.headers.get('Content-Length') or 0)
                if n < 0 or n > MAX_BODY:
                    return self._json({'error': 'too large'}, 413)
                body = json.loads(self.rfile.read(n).decode('utf-8') or '{}')
            except Exception:
                return self._json({'error': 'bad request'}, 400)
            name = u.path.split('/api/', 1)[1]
            if name == 'kv':
                sets = body.get('set') if isinstance(body.get('set'), dict) else {}
                dels = body.get('del') if isinstance(body.get('del'), list) else []
                store.kv_write(sets, dels)
                return self._json({'ok': True, 'set': len(sets), 'del': len(dels)})
            if name == 'problems':
                rows = body.get('rows') if isinstance(body.get('rows'), list) else []
                return self._json({'ok': True, 'n': store.problems_merge(rows)})
            if name == 'problems/clear':
                store.problems_clear()
                return self._json({'ok': True})
            if name == 'backup':
                return self._json({'ok': True, 'file': store.maybe_backup(force=True)})
            return self._json({'error': 'not found'}, 404)

    return Handler


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    ap = argparse.ArgumentParser(description='Serve the Learning Hub on this computer and save everything to a SQLite file.')
    ap.add_argument('--port', type=int, default=8377)
    ap.add_argument('--data', default=os.path.join('~', 'Documents', 'MM7 Data'), help='folder for mm7.sqlite and backups (default: ~/Documents/MM7 Data)')
    ap.add_argument('--app', default=HERE, help='folder holding index.html (default: the folder this script is in)')
    ap.add_argument('--no-open', action='store_true', help='do not open the browser')
    a = ap.parse_args()
    app_dir = os.path.abspath(os.path.expanduser(a.app))
    if not os.path.exists(os.path.join(app_dir, 'index.html')):
        sys.exit('No index.html in %s. Keep mm7_helper.py inside the Learning Hub folder, or pass --app.' % app_dir)
    store = Store(os.path.abspath(os.path.expanduser(a.data)))
    try:
        srv = Server(('127.0.0.1', a.port), make_handler(store, app_dir, a.port))
    except OSError as e:
        sys.exit('Port %d is in use (%s). Is the helper already running? Otherwise try --port %d.' % (a.port, e, a.port + 1))
    url = 'http://localhost:%d/' % a.port
    c = store.counts()
    print('The Learning Hub is at %s' % url)
    print('Saving to %s  (%d records, %d problems so far)' % (store.file, c['keys'], c['problems']))
    print('Leave this window open while you work. Ctrl+C stops it; nothing is lost.')
    if not a.no_open:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        store.maybe_backup(force=True)
        print('\nStopped. Everything is in %s' % store.file)


if __name__ == '__main__':
    main()
