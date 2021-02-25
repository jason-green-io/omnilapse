# omnilapse

An omnilapse is a time lapse that uses a server's world backups. This allows anywhere in a world to be timelapsed, at any point in time in the future. The granularity of the time lapse depends on the frequency of the server's backups. Ideally, you'd want the backups to be daily and use some form of copy-on-write filesystem that implements snapshots. This allows many daily backups to be taken using the least amount of disk space.


## 1st step - genjson

Chunky JSON scene files are generated for each frame, descriping the location, chunks to be loaded, sun position and other options. See Chunky for details on what it does. By default the sun is moved across the sky to show the passage of time.

## 2nd step- render

Each frame is rendered with a configurable SSP (quality) and resolution.

## 3rd step - genvideo

Each frame is combined into a video.


## primary use case

Assume you're planning out a very large build that will span months to complete. You ensure the server is backing up to an aformentioned storage system. You build. After you're done, you create a time lapse of the process using the backups generated while you were building. No need to run any client side mods, no need to take screenshots. Just login and build.


## modes

### 2d

2D mode keeps the camera static. The camera is set 45 degree angle looking down.

### 3d

3D mode create a 360 degree stereoscopic video of the area.

### spinning

Spinning will rotate around a fixed point. This can be combined with 2D or 3D modes.

## examples

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/qT51o1d4hUo/0.jpg)](https://www.youtube.com/watch?v=qT51o1d4hUo)
