sleepysnail
===========

Video capture:

In the terminal:

* Open `coriander`. Set all camera to greyscale and close it.
* Use our program called `capture`. You should see one window for each camera.
* Start recording by pressing *space bar* (you should read confirmation messages).
* Use escape to quit (you may need to be click on one of the capture windows for it to work).


By default, videos are saved in `/data/DATE_N/`.

Where `DATE` is a date such as `20141025`and `N` is the index (#) of the 
camera (starts at 0, not one).

Inside each `/data/DATE_N/`, there will be many "chunks" of videos such as:

`/data/DATE_N/DATE_N_I`.

where `I` is the index of each chunk (starts at 0).


So, to watc a video, you could do something like:

```
mplayer /data/DATE_N/DATE_N_I
```
