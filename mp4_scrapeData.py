# this script will scrape mp4 video files for xyz coordinates, filename, filepath, time and date of collection
# this will feed the attributes into a .csv file for later use in ArcGIS Pro to ID pipes and other utilities
# this code should work with both mp4 and 360 videos since ffmpeg recognizes them as the same
# wish me luck

# you'll need git downloaded and added to path, ffmpeg, ffprobe, os, and csv packages

import os, csv, ffprobe, exifread as ef

def scrape_mp4():
    # get inputs
    folderpath = input("This script will scrape every single mp4 video in the folder. \nInsert filepath to all mp4 videos: ")

    # check to see if folder is real
    if os.path.isdir(folderpath):
        print("directory found")

        # go thru all files in folder
        for vid in os.listdir(folderpath):
            # check to see if the file is proper format to do stuff with
            if vid.endswith(".MP4") or vid.endswith(".360"):
                print(vid  + " scraping it up")
                # this is where we get started doing our scraping
                address = folderpath+vid # this is complete filepath to video
                # will hold filename, xy (single non-separated value), and creation time (YYYY-MM-DDTHH:MM:SS.SSSSSZ)
                # and read into csv line
                tempHolding = [3]
                tags = ef.process_file(vid)
                lat = tags.get('GPS GPSLatitudeRef')
                lon = tags.get('GPS GPSLongitudeRef')


                # reset tempholding list
                tempHolding = [3]
            else:
                # if the filetype isn't a video in the right format
                pass
    else:
        print("folder path does not exist, try again")
        scrape_mp4()
        return

scrape_mp4()