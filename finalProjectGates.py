# tyler gates; tbgates
# city file = shapefile
# crime = csv file
# crime field = crime descriptor in crim csv
# type of crime described in crime field - must match exactly
# x + y name - lon / lat fields in crime csv file
# geodatabase - self-explanatory
# points - colocation point file of interest

import arcpy, os, sys, math
def runAnalysis(city, crime, crimeField, crimeType, xname, yname, geodatabase, points):
    arcpy.env.workspace = geodatabase
    arcpy.env.overwriteOutput = True # enable file overwrite
    
    fc = arcpy.ListFeatureClasses()
    crimeIn = str(crime[:-4])
    
    # all pre-analysis data checks
    if os.path.exists(geodatabase) == False: # check to see if database exists
        return "geodatabase does not exist"
    else:
        print("geodatabase found")
    if os.path.exists(crime) == False: # check to see if crime table exists
        return "crime table not found"
    else:
        print("crime table found")
    print("crime table importing...")
    arcpy.TableToTable_conversion(crime, geodatabase, crimeIn) # import crime table into geodatabase
    lCheck = arcpy.ListTables()
    if crimeIn in lCheck: # check if import worked
        print("table import successful")             
    else:
        return "table import failed"
    if city not in fc:
        return city + " not found in the geodatabase"
    else:
        print(city + " found")
        if points not in fc:
            return points + " not found"
        else:
            print(points + " found")

    # check for fields
    cField = arcpy.ListFields(crimeIn)
    fcheck = []
    for c in cField:
        n = c.name
        fcheck.append(n)
    if xname not in fcheck:
        return "x field not found"
    else:
        print("x field found")
        if yname not in fcheck:
            return "y field not found"
        else:
            print("y field found")
            if crimeField not in fcheck:
                return "crime type field not found"
            else:
                print("crime type field found")
    fcheck = 0 # delete list components to free memory
    
    # clip features to city bounds if found
    outname = points + "Clip"
    arcpy.Clip_analysis(points, city, outname)
    fc = arcpy.ListFeatureClasses()
    if outname not in fc:
        return points + " clip failed"
    else:
        print(points + " clip successful") 
    
    # create point shp from csv lat/lon
    sRef = arcpy.SpatialReference("WGS 1984")
    arcpy.MakeXYEventLayer_management(crimeIn, xname, yname, crimeIn + "Temp", sRef) # temp xy point feature
    arcpy.FeatureToPoint_management(crimeIn + "Temp", crimeIn + "XY") # convert temp layer to permanent layer
    arcpy.Delete_management(crimeIn + "Temp")
    
    # check xy points
    fc = arcpy.ListFeatureClasses()
    if crimeIn + "XY" not in fc:
        return "table to point failed"
    else:
        print("table to point successful")
        
    # select specific crimetype and export selected points a sseparate layer
    where = str(crimeField) + " = \'" + crimeType + "'" # SQL clause to select features
    arcpy.MakeFeatureLayer_management(crimeIn + "XY", crimeType + "Temp", where, geodatabase) # make temp layer from selected features
    arcpy.FeatureToPoint_management(crimeType + "Temp", crimeType + "Points") # turn temp layer into points
    arcpy.Delete_management(crimeType + "Temp")
    
    # check new feature
    fc = arcpy.ListFeatureClasses()
    if crimeType + "Points" not in fc:
        return "selected crime type point feature creation failed"
    else:
        curs = arcpy.da.UpdateCursor(crimeType + "Points", ["Primary_Type", "Community_Area"])
        for r in curs:
            if r[0] != crimeType:
                return "crime type selection incorrect"
            del r
        del curs
        print("selected crime type point feature creation success")
    
    # colocation analysis
    colResult = "colocationPts"
    arcpy.stats.ColocationAnalysis("DATASETS_WITHOUT_CATEGORIES", crimeType + "Points", colResult, "", "", "", points, "", "", "", "DISTANCE_BAND", "", "1000 FEET", "", "", "", "", "GAUSSIAN")
    ''' 
    Tests whether features of neighboring categroy are more/less present in neighborhood of category of interest
    compared to  overall spatial distribution of categories
    LCLQ value == 1 means more likely to have category of interest as neighbor
    LCLQ value == <1 means less likely to have category of interest as neighbor
    This wording might be reversed, description on arcpro is somewhat confusing
    '''
    
    # check to see if analysis worked
    fc = arcpy.ListFeatureClasses()
    if colResult not in fc:
        return "colocation analysis failed"
    else:
        print("colocation analysis successful")
        arcpy.Delete_management(crimeType + "Points") # delete original crime type poitn file
        
        # check to see if there are significant outcomes in analysis
        with arcpy.da.UpdateCursor(colResult, ["LCLQTYPE"]) as curs:
            # all unique colocation results in output
            cCheck = sorted({r[0] for r in curs})
        if "Colocated - Significant" not in cCheck:
            return "no significant colocation present"
        else:
            print("significant colocation present")
            
            origCount = str(arcpy.GetCount_management(colResult))
            origCountNum = int(origCount)
            # export high colocation points to separate point file
            cWhere =  "LCLQBIN = 0"
            arcpy.MakeFeatureLayer_management(colResult, colResult + "temp", cWhere, geodatabase) # make temp layer from selected features
            cCount = int(arcpy.GetCount_management(colResult + "Temp").getOutput(0))
            cCountNum = int(cCount)
    
    # find percentage of points with high colocation measurement
    totPer = (cCount / origCountNum) * 100
    print("_________________________________")
    print("% of " + crimeType + " Points that are significantly \ncorrelated with " + points + ": " + str(totPer))
    print("_________________________________")
    
    # spatial stats on city neighborhoods -> count of significantly colocated points in each neighborhood
    arcpy.AddField_management(city, "colPCount", "SHORT")
    arcpy.SpatialJoin_analysis(city, colResult + "Temp" , crimeType + "Liklihood", "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "COMPLETELY_CONTAINS")
    fc = arcpy.ListFeatureClasses()
    if crimeType + "Liklihood" not in fc:
        return "spatial join failed"
    else:
        print("spatial join successful")
    
    print("colPCount == liklihood that the neighborhood will have an \n" + crimeType + " crime occur near a " + points + " location")
    
    return "analysis complete"
