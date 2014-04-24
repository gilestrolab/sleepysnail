sleepysnail
===========

Video capture
---------------------

In the terminal:

* Open `coriander`. Set **all** camera to greyscale and close it (you only need to do that if you unplug/replug cameras).
* Use our program called `capture`. You should see one window for each camera.
* Start recording by pressing *space bar* (you should read confirmation messages).
* Use escape to quit (you may need to be click on one of the capture windows for it to work).


By default, videos are saved in `/data/sleepysnail/raw/DATE_N/`.

Where `DATE` is a date such as `20140424-115305`and `N` is the index (#) of the
camera (starts at 0, not one).

Inside each `/data/DATE_N/`, there will be many "chunks" of videos such as:

`/data/sleepysnail/raw/DATE_N/DATE_N_I`.

Where `I` is the index of each chunk (starts at 000).

So, to watch a video, you could do something like:

```
mplayer /data/sleepysnail/raw/DATE_N/DATE_N_I.avi
```

Experiment description
---------------------
Inside each capture directory (`/data/sleepysnail/raw/DATE_N/`) these **should** be a csv file in a dataframe format
with, at least, the column field `tube`.
For example, it could be:

```
tube, species, light_hours, weight,
0, Cn, 16, 4.3
1, Cn, 16, 5.0
2, Cn, 16, 4.6
3, Ha, 16, 10.3
4, Ha, 16, 12.1
...
17, Ha, 16, 15.7
```

The file *should* be saved as `DATE_N.csv`.
Therefore in the in it would be at `/data/sleepysnail/raw/DATE_N/DATE_N.csv`
