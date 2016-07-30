import json
import sys
import math
import glob
import os
import subprocess
import time
import datetime

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

def render():
    jsonfilename = "{}/{}.json".format(folder, name)
    pngfilename = "{}/{}-{}".format(folder, name, str(spp))            


    config["camera"]["projectionMode"] = "ODS_LEFT"
    json.dump(config, open(jsonfilename, "w"))


    command = "{} -jar {} -scene-dir {}/ -render {}".format(java, chunky, folder, name)
    subprocess.call(command, shell=True)
    subprocess.call("convert " + pngfilename  + ".png -gravity southeast -stroke '#000C' -strokewidth 2 -annotate 0 \"" + name + "\" -stroke  none -fill white -annotate 0 \"" + name + "\" " + pngfilename + "-ODS_LEFT-annotated.png", shell=True)
    for f in glob.glob(folder + "/" + name + "*.dump"): os.remove(f)
    try:
        os.remove(pngfilename + ".png")
    except:
        pass


    config["camera"]["projectionMode"] = "ODS_RIGHT"
    json.dump(config, open(jsonfilename, "w"))


    command = "{} -jar {} -scene-dir {}/ -render {}".format(java, chunky, folder, name)
    subprocess.call(command, shell=True)
    subprocess.call("convert " + pngfilename  + ".png -gravity southeast -stroke '#000C' -strokewidth 2 -annotate 0 \"" + name + "\" -stroke  none -fill white -annotate 0 \"" + name + "\" " + pngfilename + "-ODS_RIGHT-annotated.png", shell=True)

    subprocess.call("convert " + pngfilename + "-ODS_LEFT-annotated.png " + pngfilename + "-ODS_RIGHT-annotated.png -append " + pngfilename + "-combined-annotated.png", shell=True)

    for f in glob.glob(folder + "/" + name + "*.dump"): os.remove(f)
    try:
        os.remove(pngfilename + ".png")
    except:
        pass

if __name__ == "__main__":


    
    # Other config stuff
    lapse360folder = "./spin-o-lapse"
    chunky = "./ChunkyLaunchernew.jar"
    java = "java"
    res = sys.argv[1].split("x")

    spp = int(sys.argv[2])
    coords = tuple(sys.argv[3:6])
    coordstext = "x" + coords[0] + "y" + coords[1] + "z" + coords[2]
    startdate = sys.argv[6]
    stopdate = sys.argv[7]
    interval = datetime.timedelta(hours=24)
    
    fps = "1"

    subprocess.call("sudo zfs destroy pool/" + coordstext, shell=True)
    print( "Resolution of {} with an spp of {} at {}. Going from {} to {}. {} between frames, every frame displayed {} seconds".format(res, spp, coords, startdate, stopdate, interval, fps))

    # Set 360 pano mode
    panomode = True

    # Spin?
    spin = False


    # Create the folder for all the files
    folder = lapse360folder + "/" + coordstext
    noexists = not os.path.exists(folder)

    if noexists or "regen" in sys.argv:
        if noexists:
            os.makedirs(folder)

        # Load the default skeleton config file
        config = json.load(open("skel.json", "r"))

        # use 0 if you want everything
        distance = 90
        initialangle = 45


        # Set pano stuff
        if panomode:
            config["height"] = int(res[1])
            config["width"] = int(res[0])
            config["sppTarget"] = spp
            config["camera"]["orientation"]["pitch"] = math.radians(90)



            config["camera"]["fov"] = 180
        else:
            pitch = math.radians(50)
            config["camera"]["orientation"]["pitch"] = pitch - math.radians(90)
            fps = "1"

        # set coords if we're not spinning
        if not spin:
            angle = initialangle
            config["camera"]["orientation"]["yaw"] = math.radians(angle)
            config["camera"]["position"]["x"] = int(coords[0])
            config["camera"]["position"]["y"] = int(coords[1])
            config["camera"]["position"]["z"] = int(coords[2])

    
        def frange(startdate, stopdate, interval):
            start = datetime.datetime.strptime(str(startdate), "%Y%m%d%H%M")
            stop = datetime.datetime.strptime(str(stopdate), "%Y%m%d%H%M")
            x = start
            while x < stop:
                yield x
                x += interval


        choppedsnaps = [x for x in get_snaps() if (datetime.datetime.strptime(customsorter(x), "%Y%m%d%H%M") >= datetime.datetime.strptime(str(startdate), "%Y%m%d%H%M") and datetime.datetime.strptime(customsorter(x), "%Y%m%d%H%M") <= datetime.datetime.strptime(str(stopdate), "%Y%m%d%H%M"))]


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

        # Calculate the current chunk based on given coods
        currentchunk = [int(coords[0]) // 16, int(coords[2]) // 16]
        print("The camera is in chunk {}".format(currentchunk))

        chunkradius =  24

        # Generate the list of chunks to load based on chunkradius
        chunklist = [[x, y] for x in xrange(currentchunk[0] - chunkradius, currentchunk[0] + chunkradius + 1)
                     for y in xrange(currentchunk[1] - chunkradius, currentchunk[1] + chunkradius + 1)]
        chunklist = [[c[0], c[1]] for c in chunklist if ((c[0] - currentchunk[0])** 2 + (c[1] - currentchunk[1]) ** 2) <= chunkradius ** 2]

        # Set the chunklist for Chunky
        config["chunkList"] = chunklist


        # How many snapshots are there?
        numsnapshots = len(snapshots)

        # We'll need to keep track of which snapshot is which number
        snapshotenum = enumerate(snapshots)

        # Generate all the frames!

        finalsnaps = list(snapshotenum)
        finalsnapstemp = [finalsnaps[219], finalsnaps[229], finalsnaps[333]]
        finalsnaps = finalsnapstemp
        for snap in finalsnaps:
            # Name it meaningfully
            name = snap[1][0].split("@")[-1] + "." + coordstext + "." + str(snap[0]).rjust(5, "0")
            config["name"] = name
            config["world"]["path"] = "/Volumes/pool/" + coordstext
            # Set the coords so they rotate around the coords given using magic, I mean
            # math
            if spin:
                # Start at a 45 angle cuz it looks cool
                angle = snap[1][1] + initialangle
                config["camera"]["orientation"]["yaw"] = math.radians(angle)
                config["camera"]["position"]["x"] = int(coords[0]) + math.cos(math.radians(angle)) * math.cos(pitch) * distance
                config["camera"]["position"]["y"] = int(coords[1]) + math.sin(pitch) * distance
                config["camera"]["position"]["z"] = int(coords[2]) - math.sin(math.radians(angle)) * math.cos(pitch) * distance
            sunangle = 45 + (float(snap[0]) / numsnapshots * 90)
            az, al = sun(sunangle)
            config["sun"]["azimuth"] = math.radians(az)
            config["sun"]["altitude"] = math.radians(al)
            
            # I want to know if it'll finish befor the heat death of the universe, get a
            # start time
            start = time.time()

            subprocess.call("sudo zfs clone -o readonly=on " + snap[1][0] + " pool/" + coordstext, shell=True)

            render()
            
            subprocess.call("sudo zfs destroy pool/" + coordstext, shell=True)

            
     
            # is the universe over?
            
            stop = time.time()

            elapsed = stop - start

            # tell me how much more coffee I have to dring until it's done
            print("Just finished snapshot {} of {}, {} percent. {} hours left.".format( str(snap[0]), numsnapshots, str(100.0 * (snap[0] + 1)/ numsnapshots), str(elapsed * (numsnapshots - snap[0] + 1)/60/60)))
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



    # Make a video with all the frames
    ffmpegcommand = "ffmpeg -y -framerate " + fps + " -pattern_type glob -i \"" + folder + "/*" + str(spp) + "-combined-annotated.png\" -c:v libx264 -r 30 -pix_fmt yuv420p " + lapse360folder + "/" + coordstext + ".mp4"
    subprocess.call(ffmpegcommand, shell=True)
    
    # scale the video for poor old YouTube
    ffmpegcommand = "ffmpeg -y -i " + lapse360folder + "/" + coordstext + ".mp4" + " -vf scale=3840:2160 " + lapse360folder + "/" + coordstext + "-scaled.mp4"
    subprocess.call(ffmpegcommand, shell=True)

    # Add the 360 youtube metadata to the file
    if panomode:

        metadatacommand = "python /Volumes/TheBigOne/greener/minecraft/spatial-media/spatialmedia -i -s top-bottom " + lapse360folder + "/" + coordstext + "-scaled.mp4 " + lapse360folder + "/" + coordstext + "-scaled-meta.mp4"
        subprocess.call(metadatacommand, shell=True)
