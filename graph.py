import apsw
import datetime
import matplotlib.pyplot as plt
import pandas as pd
from pprint import pprint
connection = apsw.Connection("osm-torrent-stats.sqlite", flags=apsw.SQLITE_OPEN_READONLY)
data_dict = {}
dates = []
vals=[]
test = {}
testdates = {}
filenames=[]
def draw_single_torrent(hash_id, filename):
    print(f'Parsing for hash_id {hash_id}')
    for x in connection.execute('select peers, seeds, datetime(timestamp, "unixepoch") from torrent_stats where tracker_id=1 and hash_id = ?', (hash_id,)):
        try:
            temp=test[filename]
        except:
            test[filename]=[]
        try:
            temp=testdates[filename]
        except:
            testdates[filename]=[]
        print(x)
        test[filename].append(x[0]+x[1])
        testdates[filename].append(x[2])
        vals.append(x[0]+x[1])
        dates.append(x[2])
    
    
fig,ax = plt.subplots()

for row in connection.execute("select id, filename from hashes"):
    draw_single_torrent(row[0], row[1])
    filenames.append(row[1])
pprint(test)
pprint(testdates)
for filename in filenames:
    #df = pd.DataFrame({filename: test[filename]}, index=testdates[filename])
    df = pd.DataFrame({'date': testdates[filename], 'filename': filename, 'val': test[filename]})
    """df.set_index(testdates[filename], inplace=True)
    df.plot()"""
    ax.plot(df[df.date==testdates[filename]].date, df[df.val==test[filename]].val, label=filename)
ax.set_xlabel("year")
ax.set_ylabel("weight")
ax.legend(loc='best')
#plot = dtf.plot()
fig.savefig("output.png")
print(type(ax))
