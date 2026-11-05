#!/usr/bin/env python3
"""Offline Procmon CSV process-tree reconstruction. Python standard library only.

Usage:
    python procmon_tree_viewer.py import capture.csv [--db capture.sqlite]
    python procmon_tree_viewer.py view capture.sqlite

Import the complete Procmon CSV (All events) for best results. The original PML
must be preserved; the CSV and reconstructed tree are derived evidence.
"""
import argparse
from bisect import bisect_right
from collections import defaultdict
import csv
import os
import re
import sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

PID_FIELD = re.compile(r'(?<![\w])(?:PID|Process ID|Process Id)\s*:\s*(\d+)', re.I)
PARENT_FIELD = re.compile(r'(?:Parent PID|Parent Process ID|Parent Process Id)\s*:\s*(\d+)', re.I)
CMD_FIELD = re.compile(r'Command\s*[Ll]ine\s*:\s*(.*?)(?=,\s*(?:Current directory|Environment|Parent PID|Integrity|PID|User|Image path)\s*:|$)', re.I | re.S)
PATH_FIELD = re.compile(r'Image\s*[Pp]ath\s*:\s*(.*?)(?=,\s*(?:Command line|Parent PID|PID|Current directory)\s*:|$)', re.I | re.S)

def getval(row, *names):
    for name in names:
        if row.get(name):
            return str(row[name]).strip()
    return ''

def find_pid(detail):
    m = PID_FIELD.search(detail or '')
    return int(m.group(1)) if m else None

def import_csv(csv_path, db_path):
    if os.path.abspath(csv_path) == os.path.abspath(db_path):
        raise ValueError('CSV and database paths must differ')
    conn = sqlite3.connect(db_path)
    conn.executescript('''
      CREATE TABLE IF NOT EXISTS processes (
        node_id INTEGER PRIMARY KEY, pid INTEGER NOT NULL, parent_pid INTEGER,
        parent_node INTEGER, name TEXT, start_time TEXT, end_time TEXT,
        command TEXT, image_path TEXT, source TEXT NOT NULL,
        first_seq INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
      CREATE INDEX IF NOT EXISTS idx_pid ON processes(pid);
    ''')
    conn.execute('DELETE FROM processes')
    conn.execute('DELETE FROM meta')
    # Procmon Process Create: event PID identifies parent; Detail PID identifies child.
    # Also consider Process Start records for processes already present at capture start.
    creates = []
    starts = []
    ends = []
    with open(csv_path, 'r', encoding='utf-8-sig', errors='replace', newline='') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError('Empty CSV')
        count = 0
        for row in reader:
            count += 1
            op = getval(row, 'Operation')
            if op not in ('Process Create', 'Process Start', 'Process Exit'):
                continue
            parent_event_pid = getval(row, 'PID', 'Process ID')
            try: event_pid = int(parent_event_pid)
            except (TypeError, ValueError): continue
            name = getval(row, 'Process Name')
            when = getval(row, 'Time of Day', 'Time', 'Date & Time')
            detail = getval(row, 'Detail')
            path = getval(row, 'Path')
            if op == 'Process Create':
                child_pid = find_pid(detail)
                if child_pid is None: continue
                cmd_m = CMD_FIELD.search(detail)
                img_m = PATH_FIELD.search(detail)
                creates.append((count, child_pid, event_pid, path.rsplit('\\', 1)[-1] if path else '', when,
                                cmd_m.group(1).strip() if cmd_m else '',
                                img_m.group(1).strip() if img_m else path, 'Process Create'))
            elif op == 'Process Start':
                p = PARENT_FIELD.search(detail)
                cmd_m = CMD_FIELD.search(detail)
                starts.append((count, event_pid, int(p.group(1)) if p else None, name, when,
                               cmd_m.group(1).strip() if cmd_m else '', path, 'Process Start'))
            elif op == 'Process Exit':
                ends.append((count, event_pid, when))
    # Use starts where possible, enriched from corresponding creates. PID reuse is
    # resolved by sequence order; no parent invented where source doesn't support it.
    creates_by_pid = defaultdict(list)
    for i, c in enumerate(creates):
        creates_by_pid[c[1]].append((c[0], i, c))
    nodes = []
    used_create = set()
    for s in starts:
        seq, pid, parent_pid, name, when, cmd, path, source = s
        eligible = creates_by_pid.get(pid, [])
        pos = bisect_right(eligible, (seq, float('inf'), ())) - 1
        if pos >= 0:
            _, idx, c = eligible[pos]
            used_create.add(idx)
            parent_pid = parent_pid if parent_pid is not None else c[2]
            cmd = cmd or c[5]
            path = path or c[6]
            name = name or c[3]
            when = c[4] or when
            seq = c[0]
            source = 'Process Create + Start'
        nodes.append([seq, pid, parent_pid, name, when, '', cmd, path, source])
    for i, c in enumerate(creates):
        if i not in used_create:
            seq, pid, ppid, name, when, cmd, path, source = c
            nodes.append([seq, pid, ppid, name, when, '', cmd, path, source])
    nodes.sort(key=lambda r: r[0])
    # Linear-ish matching via grouped PID instances to avoid O(processes^2) on large captures.
    exit_by_pid = defaultdict(list)
    for seq, pid, when in ends:
        exit_by_pid[pid].append((seq, when))
    nodes_by_pid = defaultdict(list)
    for i, n in enumerate(nodes, 1):
        nodes_by_pid[n[1]].append((n[0], i))
    for pid, instances in nodes_by_pid.items():
        exits_for_pid = exit_by_pid.get(pid, [])
        exit_seq = [x[0] for x in exits_for_pid]
        for idx, (seq, nodeid) in enumerate(instances):
            upper = instances[idx + 1][0] if idx + 1 < len(instances) else float('inf')
            pos = bisect_right(exit_seq, seq - 1)
            if pos < len(exits_for_pid) and exits_for_pid[pos][0] < upper:
                nodes[nodeid-1][5] = exits_for_pid[pos][1]
    rows = []
    latest_seen_pid = {}
    for i, (seq, pid, ppid, name, start, end, cmd, path, source) in enumerate(nodes, 1):
        parent_node = latest_seen_pid.get(ppid)
        rows.append((i, pid, ppid, parent_node, name, start, end, cmd, path, source, seq))
        latest_seen_pid[pid] = i
    conn.executemany('INSERT INTO processes VALUES (?,?,?,?,?,?,?,?,?,?,?)', rows)
    conn.execute('INSERT INTO meta VALUES (?,?)', ('csv_source', os.path.abspath(csv_path)))
    conn.execute('INSERT INTO meta VALUES (?,?)', ('total_events', str(count)))
    conn.commit()
    conn.close()
    return count, len(rows)

class Viewer:
    def __init__(self, root, db_path):
        self.root = root
        self.root.title('Procmon Offline Process Tree | Read-only derived evidence')
        self.root.geometry('1250x780')
        self.conn = sqlite3.connect(f'file:{os.path.abspath(db_path)}?mode=ro', uri=True)
        self.records = self.conn.execute('SELECT * FROM processes ORDER BY first_seq').fetchall()
        self.byid = {r[0]: r for r in self.records}
        self.query = tk.StringVar()
        bar = ttk.Frame(root, padding=8); bar.pack(fill='x')
        ttk.Label(bar, text='Search process name / PID / command: ').pack(side='left')
        search = ttk.Entry(bar, textvariable=self.query, width=52); search.pack(side='left', padx=4)
        search.bind('<Return>', lambda _: self.populate())
        ttk.Button(bar, text='Find', command=self.populate).pack(side='left')
        ttk.Button(bar, text='Show all', command=lambda: (self.query.set(''), self.populate())).pack(side='left', padx=5)
        ttk.Label(bar, text=f'Processes: {len(self.records)}  |  CSV events inspected: ' +
                  str(self.conn.execute("SELECT value FROM meta WHERE key='total_events'").fetchone()[0])).pack(side='right')
        mid = ttk.Frame(root); mid.pack(fill='both', expand=True)
        cols = ('pid', 'ppid', 'start', 'end', 'source')
        self.tree = ttk.Treeview(mid, columns=cols, show='tree headings', selectmode='browse')
        self.tree.heading('#0', text='Process tree / Name')
        self.tree.column('#0', width=420)
        for col, label, width in [('pid','PID',80),('ppid','Parent PID',100),('start','Start Time',190),('end','End Time',190),('source','Evidence source',170)]:
            self.tree.heading(col, text=label); self.tree.column(col, width=width)
        yscroll = ttk.Scrollbar(mid, orient='vertical', command=self.tree.yview)
        xscroll = ttk.Scrollbar(mid, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.grid(row=0, column=0, sticky='nsew'); yscroll.grid(row=0, column=1, sticky='ns')
        xscroll.grid(row=1, column=0, sticky='ew')
        mid.columnconfigure(0, weight=1); mid.rowconfigure(0, weight=1)
        self.tree.bind('<<TreeviewSelect>>', self.selected)
        ttk.Label(root, text='Selected process evidence (CSV-derived; absent fields are not inferred):', padding=(8,4)).pack(anchor='w')
        self.info = tk.Text(root, height=9, wrap='word')
        self.info.pack(fill='x', padx=8, pady=(0,8))
        self.populate()

    def populate(self):
        q = self.query.get().strip().lower()
        if q:
            match = {r[0] for r in self.records if q in f'{r[1]} {r[4]} {r[7]} {r[8]}'.lower()}
            wanted = set(match)
            for node in list(match):
                seen = set()
                while node in self.byid and node not in seen:
                    seen.add(node)
                    parent = self.byid[node][3]
                    if parent is None: break
                    wanted.add(parent); node = parent
        else: wanted = set(self.byid)
        for item in self.tree.get_children(): self.tree.delete(item)
        pending = [r for r in self.records if r[0] in wanted]
        # Iteratively insert parents first, fallback to root if evidence/tree is incomplete.
        remaining = {r[0]: r for r in pending}
        while remaining:
            progressed = False
            for node_id, r in list(remaining.items()):
                parent = r[3]
                if parent not in remaining:
                    parent_iid = str(parent) if parent in wanted and self.tree.exists(str(parent)) else ''
                    self.tree.insert(parent_iid, 'end', iid=str(node_id), text=r[4] or '(unknown)',
                                     values=(r[1], r[2] if r[2] is not None else '', r[5], r[6], r[9]),
                                     open=(q != ''))
                    del remaining[node_id]; progressed = True
            if not progressed:
                for node_id, r in remaining.items():
                    self.tree.insert('', 'end', iid=str(node_id), text=r[4] or '(unknown)',
                                     values=(r[1], r[2], r[5], r[6], r[9]))
                break

    def selected(self, _=None):
        sel = self.tree.selection()
        if not sel: return
        r = self.byid[int(sel[0])]
        self.info.delete('1.0', tk.END)
        self.info.insert('1.0', '\n'.join([
            f'Process: {r[4]} | PID: {r[1]} | Parent PID: {r[2]}',
            f'Start: {r[5]} | End: {r[6]}', f'Image path: {r[8]}',
            f'Command line: {r[7]}', f'Derived from: {r[9]} | Source event sequence: {r[10]}',
            'Note: missing processes/parents can result from capture gaps, filtering or PID reuse.'
        ]))

def main():
    parser = argparse.ArgumentParser(description='View Procmon CSV process tree offline (standard library)')
    sub = parser.add_subparsers(dest='action', required=True)
    imp = sub.add_parser('import', help='Import Procmon CSV into SQLite')
    imp.add_argument('csv'); imp.add_argument('--db')
    view = sub.add_parser('view', help='View saved SQLite')
    view.add_argument('db')
    args = parser.parse_args()
    if args.action == 'import':
        target = args.db or os.path.splitext(args.csv)[0] + '.sqlite'
        print('Reading Procmon CSV (do not modify source)...', flush=True)
        events, processes = import_csv(args.csv, target)
        print(f'Imported {events:,} events; reconstructed {processes:,} process instances. DB: {target}')
        print(f'Open using: python "{os.path.abspath(__file__)}" view "{os.path.abspath(target)}"')
    else:
        root = tk.Tk(); Viewer(root, args.db); root.mainloop()

if __name__ == '__main__':
    try: main()
    except (ValueError, sqlite3.Error, OSError) as exc:
        print(f'Error: {exc}', file=sys.stderr); sys.exit(1)
