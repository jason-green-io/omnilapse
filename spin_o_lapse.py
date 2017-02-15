import json
import sys
import math
import glob
import os
import subprocess
import time
import datetime
import argparse


lapse360folder = "./spin-o-lapse"
chunky = "./ChunkyLaunchernew.jar"
java = "java"






def customsorter(snap):
    """
    sort on the name of the snapshot
    """
    return snap[0].split("@")[-1]


def get_snaps():
    """
    go get the list of snapshots from zfs
    """
    
    snaps = subprocess.check_output("sudo zfs list -t snapshot", shell=True).split("\n")
    snaps.remove("")
    snaps = [[x.split()[0], x.split()[4]] for x in snaps if "barlynaland" in x]


    finalsnaps = sorted(snaps, key=customsorter)
    print(finalsnaps[0], finalsnaps[-1])
    return finalsnaps


def sun(angle):
    """
    return the azimuth and altitude components when given a 0-180 degree arc
    """
    az = 0 if angle <= 90 else 180
    al = angle if angle <= 90 else 180 - angle
    return (az, al)

def render(args):
    x = args.coords[0]
    y = args.coords[1]
    z = args.coords[2]
    coordstext = "x{}y{}z{}".format(x, y, z)

    res = args.res.split("x")
    mode = args.mode
    spp = args.ssp

    folder = lapse360folder + "/" + coordstext
    files = glob.glob(folder + "/*.json")
    filesenum = enumerate(files)
    numfiles = len(files)
    subprocess.call("sudo zfs destroy pool2/" + coordstext, shell=True)            
    for f in filesenum:
        print(f)
        start = time.time()

        # load the json, change it, and dump it again
        with open(f[1], "r") as scenefile:
            config = json.load(scenefile)

        config["sppTarget"] = spp
        config["height"] = int(res[1])
        config["width"] = int(res[0])

        snap = config["zfssnapshot"]
        name = f[1].split("/")[-1].rsplit(".", 1)[0]
        notexist = not os.path.exists(folder + "/" + name + ".octree")

        if notexist:
            subprocess.call("sudo zfs clone -o readonly=on " + snap + " pool2/" + coordstext, shell=True)

        pngfilename = "{}/{}-{}".format(folder, name, str(spp))            

        if mode == "2d":
            json.dump(config, open(f[1], "w"))
            
            command = "{} -jar {} -scene-dir {}/ -render {}".format(java, chunky, folder, name)
            subprocess.call(command, shell=True)
            subprocess.call("convert " + pngfilename  + ".png -gravity southeast -stroke '#000C' -strokewidth 2 -annotate 0 \"" + name + "\" -stroke  none -fill white -annotate 0 \"" + name + "\" " + pngfilename + "-annotated.png", shell=True)

            for each in glob.glob(folder + "/" + name + "*.dump"): os.remove(each)

            try:
                os.remove(pngfilename + ".png")
            except:
                pass

            
        if mode == "3d":

            config["camera"]["projectionMode"] = "ODS_LEFT"
            json.dump(config, open(f[1], "w"))


            command = "{} -jar {} -scene-dir {}/ -render {}".format(java, chunky, folder, name)
            subprocess.call(command, shell=True)
            subprocess.call("convert " + pngfilename  + ".png -gravity southeast -stroke '#000C' -strokewidth 2 -annotate 0 \"" + name + "\" -stroke  none -fill white -annotate 0 \"" + name + "\" " + pngfilename + "-ODS_LEFT-annotated.png", shell=True)

            for each in glob.glob(folder + "/" + name + "*.dump"): os.remove(each)

            try:
                os.remove(pngfilename + ".png")
                os.remvoe(pngfilename + "-ODS_LEFT-annotated.png")
            except:
                pass


            config["camera"]["projectionMode"] = "ODS_RIGHT"
            json.dump(config, open(f[1], "w"))


            command = "{} -jar {} -scene-dir {}/ -render {}".format(java, chunky, folder, name)
            subprocess.call(command, shell=True)
            subprocess.call("convert " + pngfilename  + ".png -gravity southeast -stroke '#000C' -strokewidth 2 -annotate 0 \"" + name + "\" -stroke  none -fill white -annotate 0 \"" + name + "\" " + pngfilename + "-ODS_RIGHT-annotated.png", shell=True)

            for each in glob.glob(folder + "/" + name + "*.dump"): os.remove(each)
            try:
                os.remove(pngfilename + ".png")
                os.remvoe(pngfilename + "-ODS_RIGHT-annotated.png")
            except:
                pass

            subprocess.call("convert " + pngfilename + "-ODS_LEFT-annotated.png " + pngfilename + "-ODS_RIGHT-annotated.png -append " + pngfilename + "-combined-annotated.png", shell=True)

            
        if notexist:
            subprocess.call("sudo zfs destroy pool2/" + coordstext, shell=True)            

        stop = time.time()
        elapsed = stop - start



        # tell me how much more coffee I have to dring until it's done
        print("Just finished snapshot {} of {}, {} percent. {} hours left.".format( f[0] + 1, numfiles, 100.0 * (f[0] + 1) / numfiles, elapsed * (numfiles - f[0] + 1)/60/60))


    
def genjson(args):
    x = args.coords[0]
    y = args.coords[1]
    z = args.coords[2]
    coordstext = "x{}y{}z{}".format(x, y, z)
    mode = args.mode

    startdate = args.timeframe[0]
    stopdate = args.timeframe[1]
    interval = datetime.timedelta(hours=args.interval)
    spin = args.spin

    folder = lapse360folder + "/" + coordstext
    
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Load the default skeleton config file
    config = json.load(open("skel.json", "r"))

    # use 0 if you want everything
    distance = 120
    initialangle = 45


    # Set pano stuff

    #config["height"] = int(res[1])
    #config["width"] = int(res[0])
    #config["sppTarget"] = spp

    if mode == "3d":
        config["camera"]["orientation"]["pitch"] = math.radians(90)
        config["camera"]["fov"] = 180

    if mode == "2d":
        pitch = math.radians(50)
        config["camera"]["orientation"]["pitch"] = pitch - math.radians(90)


    # set coords if we're not spinning
    if not spin:
        angle = initialangle
        config["camera"]["orientation"]["yaw"] = math.radians(angle)
        config["camera"]["position"]["x"] = x
        config["camera"]["position"]["y"] = y
        config["camera"]["position"]["z"] = z

    # Calculate which snapshots to render
    
    def frange(startdate, stopdate, interval):
        start = datetime.datetime.strptime(str(startdate), "%Y%m%d%H%M")
        stop = datetime.datetime.strptime(str(stopdate), "%Y%m%d%H%M")
        blah = start
        while blah < stop:
            yield blah
            blah += interval


    choppedsnaps = [asnap for asnap in get_snaps() if (datetime.datetime.strptime(customsorter(asnap), "%Y%m%d%H%M") >= datetime.datetime.strptime(str(startdate), "%Y%m%d%H%M") and datetime.datetime.strptime(customsorter(asnap), "%Y%m%d%H%M") <= datetime.datetime.strptime(str(stopdate), "%Y%m%d%H%M"))]


    print("There's {} snapshots to pick from in the timespan given".format(len(choppedsnaps)))

   
    snapshots = []

    index = 0
    maxlen = len(choppedsnaps)

    for each in frange(startdate, stopdate, interval):
        if each <= datetime.datetime.strptime(customsorter(choppedsnaps[index]), "%Y%m%d%H%M"):
            snapshots.append(choppedsnaps[index])
            # print(each,choppedsnaps[index])
        else:
            while index < maxlen - 1:
                index += 1
                if each < datetime.datetime.strptime(customsorter(choppedsnaps[index]), "%Y%m%d%H%M"):
                    index -= 1
                    break
            snapshots.append(choppedsnaps[index])
            # print(each,choppedsnaps[index])

        
    print("First snapshot {}\nLast snapshot {}".format(snapshots[0], snapshots[-1]))




        
    # calculate the chunks to load


    # Calculate the current chunk based on given coods
    print(x, z)
    currentchunk = [x // 16, z // 16]
    print("The camera is in chunk {}".format(currentchunk))

    chunkradius =  24

    # Generate the list of chunks to load based on chunkradius
    chunklist = [[cx, cy] for cx in xrange(currentchunk[0] - chunkradius, currentchunk[0] + chunkradius + 1) for cy in xrange(currentchunk[1] - chunkradius, currentchunk[1] + chunkradius + 1)]
    chunklist = [[c[0], c[1]] for c in chunklist if ((c[0] - currentchunk[0])** 2 + (c[1] - currentchunk[1]) ** 2) <= chunkradius ** 2]

    # Set the chunklist for Chunky
    config["chunkList"] = chunklist


    # How many snapshots are there?
    numsnapshots = len(snapshots)

    # We'll need to keep track of which snapshot is which number
    snapshotenum = enumerate(snapshots)

    # Generate all the frames!

    finalsnaps = list(snapshotenum)
    #finalsnapstemp = [finalsnaps[219], finalsnaps[229], finalsnaps[333]]
    #finalsnaps = finalsnapstemp

    for snap in finalsnaps:
        # Name it meaningfully
        print(snap)
        name = snap[1][0].split("@")[-1] + "." + coordstext + "." + str(snap[0]).rjust(5, "0")
        config["name"] = name
        config["world"]["path"] = "/Volumes/pool2/" + coordstext
        config["zfssnapshot"] = snap[1][0]
        # Set the coords so they rotate around the coords given using magic, I mean
        # math
        if spin:
            # Start at a 45 angle cuz it looks cool
            angle = snap[0] + initialangle
            config["camera"]["orientation"]["yaw"] = math.radians(angle)
            config["camera"]["position"]["x"] = x + math.cos(math.radians(angle)) * math.cos(pitch) * distance
            config["camera"]["position"]["y"] = y + math.sin(pitch) * distance
            config["camera"]["position"]["z"] = z - math.sin(math.radians(angle)) * math.cos(pitch) * distance
        sunangle = 45 + (float(snap[0]) / numsnapshots * 90)
        az, al = sun(sunangle)
        config["sun"]["azimuth"] = math.radians(az)
        config["sun"]["altitude"] = math.radians(al)
        jsonfilename = "{}/{}.json".format(folder, name)
        json.dump(config, open(jsonfilename, "w"))
'''        
    else:
        files = glob.glob(folder + "/*.json")
        filesenum = enumerate(files)
        numfiles = len(files)

        for f in filesenum:
            start = time.time()

            # load the json, change it, and dump it again
            with open(f[1], "r") as scenefile:
                config = json.load(scenefile)
            config["sppTarget"] = spp
            config["height"] = int(res[1])
            config["width"] = int(res[0])
            
            name = f[1].split("/")[-1].rsplit(".", 1)[0]

            render()

            stop = time.time()
            elapsed = stop - start



            # tell me how much more coffee I have to dring until it's done
            print("Just finished snapshot {} of {}, {} percent. {} hours left.".format( str(f[0]), numfiles, str(100.0 * (f[0] + 1)/ numfiles), str(elapsed * (numfiles - f[0] + 1)/60/60)))

'''
def genvideo(args):
    x = args.coords[0]
    y = args.coords[1]
    z = args.coords[2]
    coordstext = "x{}y{}z{}".format(x, y, z)
    mode = args.mode
    fps = args.fps
    folder = lapse360folder + "/" + coordstext
    
    # Make a video with all the frames
    ffmpegcommand = "ffmpeg -y -framerate " + str(fps) + " -pattern_type glob -i \"" + folder + "/*-annotated.png\" -c:v libx264 -r 30 -pix_fmt yuv420p " + lapse360folder + "/" + coordstext + ".mp4"
    subprocess.call(ffmpegcommand, shell=True)

    if mode == "3d":

        # scale the video for poor old YouTube
        ffmpegcommand = "ffmpeg -y -i " + lapse360folder + "/" + coordstext + ".mp4" + " -vf scale=3840:2160 " + lapse360folder + "/" + coordstext + "-scaled.mp4"
        subprocess.call(ffmpegcommand, shell=True)

        # Add the 360 youtube metadata to the file


        metadatacommand = "python /Volumes/TheBigOne/greener/minecraft/spatial-media/spatialmedia -i -s top-bottom " + lapse360folder + "/" + coordstext + "-scaled.mp4 " + lapse360folder + "/" + coordstext + "-scaled-meta.mp4"
        subprocess.call(metadatacommand, shell=True)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generate cool timelapses using ZFS snapshots and Chunky")

    subparsers = parser.add_subparsers(help='sub-command help')

    parsergenvideo = subparsers.add_parser("genvideo", help="")
    parsergenjson = subparsers.add_parser("genjson", help="")
    parserrender = subparsers.add_parser("render", help="")

    #common
    parser.add_argument('--coords', nargs=3, required=True, type=int)
    parser.add_argument('--mode', default="2d", choices=["2d", "3d"]) #2d or 3d

    #genjson
    parsergenjson.add_argument('--spin', action='store_true')
    parsergenjson.add_argument('--timeframe', nargs=2)
    parsergenjson.add_argument('--interval', default=24, type=float)
    parsergenjson.set_defaults(func=genjson)

    #render
    parserrender.add_argument('--ssp', default=1, type=int)
    parserrender.add_argument('--res', default='200x100')
    parserrender.set_defaults(func=render)
    #genvideo
    parsergenvideo.add_argument('--fps', default=1, type=int)
    parsergenvideo.set_defaults(func=genvideo)

    args = parser.parse_args()
    print(args)
    args.func(args)
