import os
import sys
import csv
import glob

import exifread
import exifread as e
import arcpy as ap

'''
Filetype default is .jpg if using raw images from camera
This script will scrape gopro images for x/y locations and will generate a shapefile
    using image names to map out where they are located
I have no clue how accurate GoPro GPS is but it's probably pretty garbage, and this
    tool is only going to be as accurate as the metadata is.
Requires Python 3.x
'''


def exif_scrape():
    # get the file locations
    pic_location = raw_input(r"Where are the GoPro images at: ")
    #meta_export = raw_input(r"Where do you wan the files to go: ")

    # check if file locations are real
    isInFolder = os.path.isdir(pic_location)
    #isOutFolder = os.path.isdir(meta_export)

    if isInFolder == True: #and isOutFolder == True:
        print("Directory " + pic_location + " found")
        #print("Directory " + meta_export + " found")
    else:
        print("In folder: " + pic_location + str(isInFolder))
        #print("Out folder: " + meta_export + str(isOutFolder))
        print("Check folders, one or both don't exist")
        exif_scrape()

    # change directory to where all images are located
    os.chdir(pic_location)

    # begin reading in only .jpg files
    # we using glob in here to find all the relevant files
    # create csv file to write to
    with open('gopro_geodata.csv', 'w') as gpsf:
        writer = csv.writer(gpsf) # will begin writing to file
        writer.writerow(["photoID", "lat", "lon"]) # write headers to file
        for img in glob.glob("*.JPG"):
            print("Scraping file " + img)

            with open(img, 'rb') as img_file: # open the image's metadata to read into csv file
                tags = e.process_file(img_file, stop_tag='GPSLatitude') # grab all metadata from selected image
                '''
                for tag in tags.keys(): # go thru tags and pull out GPS tag values
                    print(tag)
                '''
                print(tags)
    return

exif_scrape()