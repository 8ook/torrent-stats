#!/usr/bin/python3
# started Matija Nalis <mnalis-git@voyager.hr> GPLv3+ 2020-12-11
# logs OpenStreetMap bittorrent statistics to sqlite3 DB

import libtorrent as lt
from scraper import scrape
import time
import apsw
from sys import argv

DBFILE='osm-torrent-stats.sqlite'

print ('OSM bittorrent scrape test')

connection=apsw.Connection(DBFILE)
sql=connection.cursor()

sql.execute ('PRAGMA foreign_keys = ON')

sql.execute("""
  CREATE TABLE IF NOT EXISTS trackers (
    id integer PRIMARY KEY AUTOINCREMENT,
    announce_url varchar(255),
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (announce_url) )
""")

sql.execute('INSERT OR IGNORE INTO trackers (announce_url) VALUES (?)', ('udp://tracker.opentrackr.org:1337/announce',))
sql.execute('INSERT OR IGNORE INTO trackers (announce_url) VALUES (?)', ('udp://tracker-udp.gbitt.info:80/announce',))
sql.execute('INSERT OR IGNORE INTO trackers (announce_url) VALUES (?)', ('udp://tracker.torrent.eu.org:451',))

sql.execute("""
  CREATE TABLE IF NOT EXISTS hashes (
    id integer PRIMARY KEY AUTOINCREMENT,
    hash char(40) NOT NULL,
    filename varchar(255),
    scrape integer NOT NULL DEFAULT 1,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (hash) )
""")


sql.execute(""" 
  CREATE TABLE IF NOT EXISTS torrent_stats (
    tracker_id integer NOT NULL,
    hash_id integer NOT NULL,
    timestamp integer NOT NULL,
    peers integer,
    seeds integer,
    complete integer,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hash_id, timestamp, tracker_id),
    FOREIGN KEY (tracker_id) REFERENCES trackers (id),
    FOREIGN KEY (hash_id) REFERENCES hashes (id) )
""")

hashes = [];

# initialize current time here, as we need it to be constant for ALL trackers/hashes in this program run!
_now = int(time.time())


# ex.scrape: {'D84256FCBF807BA6B1257798176DF4CEB3056504': {'peers': 25, 'seeds': 4, 'complete': 9}, '049C08A4934C8A2EACE7E92A1F3F01F35B045660': {'peers': 2, 'seeds': 13, 'complete': 31}}

# FIXME: try/except in case scraping of one client fails
def do_tracker (tracker_id, announce_url):
    #print ('scraping tracker:', announce_url)
    try:
        scr = scrape (announce_url, hashes)
        #print (' scrape:', scr,"\n")
        for hash in scr:
            stats = scr[hash]
            print ('  hash=',hash, ' --- stats=',stats)
            hash_id, = [h[0] for h in sql.execute ('SELECT id FROM hashes WHERE hash=?', (hash,))]
            #print ("hashid=", hash_id)
            sql.execute ('INSERT INTO torrent_stats (tracker_id, hash_id, timestamp, peers, seeds, complete) VALUES (?, ?, ?, ?, ?, ?)', (tracker_id, hash_id, _now, stats['peers'], stats['seeds'], stats['complete']))
    except:
        print ('  --- scraping FAILED, skipping');
    
def do_all_trackers():
    tr_sql = connection.cursor()
    for tracker_id, announce_url in tr_sql.execute ('SELECT id, announce_url FROM trackers'):
        do_tracker (tracker_id, announce_url)

def add_hash(hash):
    sql.execute ('INSERT OR IGNORE INTO hashes (hash, scrape) VALUES (?, ?)', (hash.lower(), 1))

# find new torrent files from cmdline (if specified) and add them to the list
for torrent_filename in argv[1:]:
    info = lt.torrent_info(torrent_filename)
    add_hash (str(info.info_hash()))

# get a list of all hashes to scrape
h_sql = connection.cursor()
hashes = [h[0] for h in h_sql.execute ('SELECT hash FROM hashes WHERE scrape=1')]
print ("sql Hashes=", hashes);


# update status of all trackers (for all infohashes)
print ('IPv4/mixed:')
do_all_trackers()


# FIXME - IPv6 does not work! check not only connceting, but different datasctructure, and share back via PR.
#print ('IPv6 only:')
#b = do_tracker ('udp://tracker.datacenterlight.ch:6969/announce')
