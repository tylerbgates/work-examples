# This will only generate water, sewer and project location figures
# this script will be used to generate UIS figures automatically
# the actual maps will need some manual editing due to the nature of UIS figures, but this will make setup a lot easier

# this python script is to be ran out of a toolbox within each map. User will determine if the script will be used for sewer, water or project location.

'''
Needs to do:
create an actual temp geodatabase wherever project is saved to, working on this in 
sewer layout change scripts

Get flow path script working already
'''


import os, sys, arcpy as ap, time

### global variable listing
# map title - text

mTitle = ap.GetParameterAsText(0) # required
# figure due date (month / YYYY)
date = ap.GetParameterAsText(1) # required
# projectLocationShapefile - shapefile
projectLocation = ap.GetParameterAsText(2) # required

# water model inputs
pressureZone = ap.GetParameterAsText(3)
waterExPHD = ap.GetParameterAsText(4)
waterExPHDp = ap.GetParameterAsText(5)
waterExFF = ap.GetParameterAsText(6)
waterExFFp = ap.GetParameterAsText(7)
waterFPHD = ap.GetParameterAsText(8)
waterFPHDp = ap.GetParameterAsText(9)
waterFFF = ap.GetParameterAsText(10)
waterFFFp = ap.GetParameterAsText(11)

# sewer model inputs - all shapefiles
ex_flowpath = ap.GetParameterAsText(12)
fcc_flowpath = ap.GetParameterAsText(13)
pwwfEx = ap.GetParameterAsText(14)
pwwfExp = ap.GetParameterAsText(15)
pwwfF = ap.GetParameterAsText(16)
pwwfFp = ap.GetParameterAsText(17)

# layout type to determine look of data
## value list needs to be defined in parameter created in toolbox setup
figureProjType = ap.GetParameterAsText(18) # required

# used to make new attributes and calc deficiencies for sewer files
def sewerCalcs():
    tic = time.perf_counter()
    # all calcs are in arcade language
    # these will give us the values being used for sewer symbologies
    # will calc REQ_dD
    reqCode = """
    if ($feature.MAX_DEPTH > 1) {
        return 0.75
    }
    else if (1 >= $feature.MAX_DEPTH > 0) {
        return 0.5
    }
    else {
        return 0
}
    """

    # will calc COMP_dD
    compCode = '''
    $feature.REQ_dD - $feature.MXFUL_DEPT
    '''

    #sewerFiles = [pwwfEx,pwwfExp,pwwfF,pwwfF]
    sewerFiles = [pwwfEx]
    for x in sewerFiles:
        ap.management.AddField(x, "REQ_dD", "DOUBLE")
        ap.management.AddField(x, "COMP_dD", "DOUBLE")
        ap.management.CalculateField(x, "REQ_dD", reqCode, "ARCADE")
        ap.management.CalculateField(x, "COMP_dD", compCode, "ARCADE")

        # delete rows with null pressure values to take off of map
        ap.management.SelectLayerByAttribute(x, "NEW_SELECTION", '"ID" IS NULL')
        ap.management.DeleteFeatures(x)
    toc = time.perf_counter()
    ap.AddMessage(f"Sewer Calc Time Elapsed: {toc-tic:0.2f} seconds")

# used to make new fields and calc deficiencies for water shapefiles
def waterCalcs():
    tic = time.perf_counter()
    #waterFilesFF = [waterExFF, waterExFFp, waterFFF, waterFFFp]
    #waterFilesAll = [waterExPHD, waterExPHDp, waterFPHD, waterFPHDp]
    waterFilesFF = [waterExFF]
    waterFilesPHD = [waterExPHD]
    watercalc = '''
    $feature.AVAIL_FLOW - $feature.TOTAL_DEM
    '''

    for x in waterFilesFF:
        ap.management.AddField(x, "Avail_FF", "DOUBLE")
        ap.management.CalculateField(x, "AVAIL_FF", watercalc, "ARCADE")
    toc = time.perf_counter()
    ap.AddMessage(f"Water Calcs Time Elapsed: {toc - tic:0.2f} seconds")

def location_layout_change():
    tic = time.perf_counter()
    aprx = ap.mp.ArcGISProject('CURRENT')
    layout = aprx.listLayouts('Fig1')[0] # only one layout to reference in this figure template
    ap.AddMessage('Layouts found')
    for x in layout.listElements():
        if x.name == "DueDate":
            x.text = date + " 2022"
        elif x.name == "ProjTitle":
            x.text = mTitle + " Utility Impact Study"
    ap.AddMessage("Title and Date Successful")

    # add project location to map, color properly
    ap.AddMessage("Adding and Coloring Project Location")
    map = aprx.listMaps('ProjLocation')[0]
    map.addDataFromPath(projectLocation)
    loc = map.listLayers()[0] # this will always select the first shapefile in the map, which is the project location after it is added
    sym = loc.symbology
    sym.renderer.symbol.color = {'RGB' : [255,115,223,45]} # assign fill color
    sym.renderer.symbol.outlineColor = {'RGB': [230, 0, 169, 45]} # assign outline color
    loc.symbology = sym # assign symbology to proper layer

    toc = time.perf_counter()
    ap.AddMessage(f"Location Layout Change Time Elapsed: {toc-tic:0.2f} seconds")
    return

# generate layouts for all figures
def water_layout_change():
    ap.AddMessage("Beginning Water Layout Change")
    tic = time.perf_counter()
    # reference current arcpro project as workspace
    aprx = ap.mp.ArcGISProject('CURRENT')
    layout = aprx.listLayouts()
    
    mapCount = 0 # keep track of which map we are referencing within our layout
    for page in layout: # go thru each layout page
        ap.AddMessage("Current Page: " + page.name)
        elem = page.listElements()
        
        # set map extents
        ap.AddMessage("Setting Map Extents")
        mf = page.listElements("mapframe_element")[0]
        try:
            m = aprx.listMaps(page.name)[0] # map frame loaded into the current layout
        except:
            ap.AddError("Layout name invalid: " + page.name)
        
        if "1" in pressureZone:
            extLyr = m.listLayers("Water_PZ_1")[0]
            try:
                mf.camera.setExtent(mf.getLayerExtent(extLyr, False, True))
            except:
                ap.AddError("PZ1 Extent Failed")
            mf.camera.scale *= 1.0133
            ap.AddMessage("Map Extent Set for " + page.name)

        elif "2" in pressureZone:
            extLyr = m.listLayers("*PZ_2")[0]
            ap.AddMessage("extent layer title: " + extLyr.name)
            try:
                mf.camera.setExtent(mf.getLayerExtent(extLyr, False, True))
            except:
                ap.AddError("PZ2 Extent Failed")
            mf.camera.scale *= 0.962
            ap.AddMessage("Map Extent Set for " + page.name)

        else:
            ap.AddWarning("No Valid Extent Found")

        ap.AddMessage("Titles Changing")
        # change element names
        for elem in page.listElements(): # go thru each element in each layout page
            # change layout titles and dates
            if elem.name == "Due Date":
                elem.text = date
                ap.AddMessage("Due Date Updated")
            elif elem.name == "Proj Title":
                elem.text = mTitle + " Utility Impact Study"
                ap.AddMessage("Project Title Updated")
            else:
                pass
        ap.AddMessage("Title and Date Successful")
        mapCount += 1 # move on to next layout map reference

    ap.AddMessage("Beginning Water Calcs")
    waterCalcs() # calculate available FireFlow
    ap.AddMessage("Water Calcs Successful")

    ap.AddMessage("Coloring project locations")
    for maps in aprx.listMaps():
        try:
            # pressure zones are already added to map and colored correctly
            maps.addDataFromPath(projectLocation)  # add project location to map
            loc = maps.listLayers()[0]  # this will always select the first shapefile in the map, which is the project location
            sym = loc.symbology
            sym.renderer.symbol.color = {'RGB': [255, 115, 223, 45]}  # assign fill color
            sym.renderer.symbol.outlineColor = {'RGB': [230, 0, 169, 45]}  # assign outline color
            loc.symbology = sym  # assign symbology to proper layer
        except:
            ap.AddError("Project location color failed for " + maps.name)

        # layer template files located in x
        phdlyr = r"file_placeholder"
        # Exiting PHD Map
        try:
            if maps.name == "Fig2_EX_PHD":
                ap.AddMessage("Beginning Ex PHD")
                maps.addDataFromPath(waterExPHD)
                lyr = maps.listLayers(os.path.basename(waterExPHD)[:-4])[0]  # this grabs the name of the layer as it appears in the table of contents


                # delete everything outside of pressure zone
                ap.management.SelectLayerByLocation(lyr, "WITHIN", pressureZone)
                ap.management.SelectLayerByAttribute(lyr, "SWITCH_SELECTION")
                ap.management.DeleteFeatures(lyr)

                # delete nodes with 0 pressure, not relevant in map
                ap.management.SelectLayerByAttribute(lyr, "NEW_SELECTION", 'PRESSURE = 0')
                ap.management.DeleteFeatures(lyr)
                
                try:
                    ap.ApplySymbologyFromLayer(lyr,phdlyr)
                except:
                    ap.AddError("symbology from layer does not work")
                pass

            # Existing PHD w Project
            elif maps.name == "Fig3_EX_PHD_wprj":
                ap.AddMessage("Beginning Ex PHD wProject")
                maps.addDataFromPath(waterExPHDp)
                lyr = maps.listLayers(os.path.basename(waterExPHDp)[:-4])[0]  # this grabs the name of the layer as it appears in the table of contents

                # delete everything outside of pressure zone
                ap.management.SelectLayerByLocation(lyr, "WITHIN", pressureZone)
                ap.management.SelectLayerByAttribute(lyr, "SWITCH_SELECTION")
                ap.management.DeleteFeatures(lyr)

                # delete nodes with 0 pressure, not relevant in map
                ap.management.SelectLayerByAttribute(lyr, "NEW_SELECTION", 'PRESSURE = 0')
                ap.management.DeleteFeatures(lyr)
                pass

            # Existing Fire Flow
            elif maps.name == "Fig4_Ex_MDD_FF":
                ap.AddMessage("Beginning Ex MDD + FF")
                maps.addDataFromPath(waterExFF)
                pass

            # Existing Fire Flow w Project
            elif maps.name == "Fig5_EX_MDD_FF_wprj":
                ap.AddMessage("Beginning Ex MDD + FF w Project")
                maps.addDataFromPath(waterExFFp)
                pass

            # Future PHD
            elif maps.name == "Fig6_FCC_PHD":
                ap.AddMessage("Beginning FCC PHD")
                maps.addDataFromPath(waterFPHD)
                lyr = maps.listLayers(os.path.basename(waterFPHD)[:-4])[0]  # this grabs the name of the layer as it appears in the table of contents

                # delete everything outside of pressure zone
                ap.management.SelectLayerByLocation(lyr, "WITHIN", pressureZone)
                ap.management.SelectLayerByAttribute(lyr, "SWITCH_SELECTION")
                ap.management.DeleteFeatures(lyr)

                # delete nodes with 0 pressure, not relevant in map
                ap.management.SelectLayerByAttribute(lyr, "NEW_SELECTION", 'PRESSURE = 0')
                ap.management.DeleteFeatures(lyr)
                pass

            # Future PHD w Project
            elif maps.name == "Fig7_FCC_PHD_wprj":
                ap.AddMessage("Beginning FCC PHD w Project")
                maps.addDataFromPath(waterFPHDp)
                lyr = maps.listLayers(os.path.basename(waterFPHDp)[:-4])[0]  # this grabs the name of the layer as it appears in the table of contents

                # delete everything outside of pressure zone
                ap.management.SelectLayerByLocation(lyr, "WITHIN", pressureZone)
                ap.management.SelectLayerByAttribute(lyr, "SWITCH_SELECTION")
                ap.management.DeleteFeatures(lyr)

                # delete nodes with 0 pressure, not relevant in map
                ap.management.SelectLayerByAttribute(lyr, "NEW_SELECTION", 'PRESSURE = 0')
                ap.management.DeleteFeatures(lyr)
                pass

            # Future Fire Flow
            elif maps.name == "Fig8_FCC_MDD_FF":
                ap.AddMessage("Beginning FCC MDD + FF")
                maps.addDataFromPath(waterFFF)
                pass
                
            # Future Fire Flow w Project
            elif maps.name == "Fig9_FCC_MDD_FF_wprj":
                ap.AddMessage("Beginning FCC MDD + FF w Project")
                maps.addDataFromPath(waterFFFp)
                pass
                
            else: # if layout is added to project template, nothing should be done
                ap.AddMessage("Unrecognized layout: " + maps.name)
                pass
        except:
            ap.AddError("data failed to add to layout " + maps.name)
    toc = time.perf_counter()
    ap.AddMessage(f"Water Layout Change Timem Elapsed: {toc - tic:0.2f} seconds")
    return

##################################################################################################
########################################################
##################################
######################
#########
####
#

# this function was beingpu tin place to automatically select flowpath pipes from flowpath node files
# I almost got it working but did not end up having time to complete it. Definitely needs to be worked on
## Temporary workspace not working for temp calculation outputs
## SQL expression in selection is not working correctly

# find pipes along flow path of existing or future projects
'''
def flowpath_pipe(sewer_pipe, fp, mapName, tempgdb):
    ap.SetProgressor("step", "Finding Flow Path...")
    aprx = ap.mp.ArcGISProject('CURRENT')

    maps = aprx.listMaps(mapName)[0]

    ap.AddMessage("Map Name: " + maps.name) ######

    # create temp layer from pipes intersecting nodes
    ap.management.SelectLayerByLocation(sewer_pipe,'INTERSECT',fp)
    
    # write selection of pipes to memory as to make it temporary, then clear selection
    memPipe = str(tempgdb+".gdb") + "fpPipeSelect"
    ap.management.CopyFeatures(sewer_pipe, memPipe)
    ap.addDataFromPath(memPipe)
    maps.clearSelection()

    test1 = maps.listLayers() ##########
    for x in test1:
        ap.AddMessage(x.name)

    # from temp pipe layer make line to point at both ends of selected pipes
    pipe_ends = r"memory\fp_pipe_ends"
    ap.management.GeneratePointsAlongLines(memPipe,pipe_ends,'PERCENTAGE','',100,'END_POINTS')

    # select by location, points intersecting w flow points, copy features selected points to memory
    pipe_end_select = r"memory\fp_pipe_ends_select"
    ap.management.SelectLayerByLocation(pipe_ends,'INTERSECT', fp)
    ap.management.CopyFeatures(pipe_ends, pipe_end_select)
    maps.clearSelection()

    # add matching MOID values to list
    match_point_ID = [row[0] for row in ap.da.SearchCursor(pipe_end_select,['MOID'])]
    
    # find MOIDs which occur twice in the list to get unique list of pipes to include in flow path
    match_two_point_ID = []
    [match_two_point_ID.append(x) for x in match_point_ID if match_point_ID.count(x) == 2 and x not in match_two_point_ID]
    ap.AddMessage(match_two_point_ID)
    # for y in mem_pipe, if mem_pipe ID is in match_point_ID, add to selection
    # solution found https://gis.stackexchange.com/questions/29735/selecting-features-by-attribute-if-in-python-list
    query = '"MOID" IN ' + str(tuple(match_two_point_ID))
    ap.management.SelectLayerByAttribute(memPipe,"NEW_SELECTION",query)

    # copy features to actual shapefile, save to project folder, delete temp files
    ap.management.CopyFeatures(memPipe, aprx.filePath[:-5])
    maps.clearSelection()
    ap.management.Delete("memory")

    return
'''
#
#####
####################
##############################################
######################################################################
############################################################################################
##########################################################################################################################

def sewer_layout_change():
    tic = time.perf_counter()
    aprx = ap.mp.ArcGISProject('CURRENT')

    # make temp gdb for calcs
    tempgdb = ap.mp.ArcGISProject('CURRENT').filePath + ".gdb"
    ap.AddMessage("temp gdb: " + tempgdb)

    layout = aprx.listLayouts()
    # change layout titles and dates
    for page in layout:
        for elem in page.listElements():  # go thru each element
            try:
                if elem.name == "DueDate":
                    elem.text = date
                elif elem.name == "ProjTitle":
                    elem.text = mTitle + " Utility Impact Study"
                else:
                    pass
            except:
                ap.AddError("Project Title and Due Date Failed to Change")
    ap.AddMessage("Title and Date Successful")
    ap.AddMessage("Running Sewer Calcs...")
    sewerCalcs() # prep sewer line shapefiles for use in maps
    ap.AddMessage("Sewer Calcs Successful")
    
    for maps in aprx.listMaps():
        # add location shapefiles to all
        try:
            ap.AddMessage("Adding Project Location to " + page.name)
            maps.addDataFromPath(projectLocation) # add project location to map
            loc = maps.listLayers()[0]  # this will always select the first shapefile in the map, which is the project location
            sym = loc.symbology
            sym.renderer.symbol.color = {'RGB': [255, 115, 223, 45]}  # assign fill color
            sym.renderer.symbol.outlineColor = {'RGB': [230, 0, 169, 45]}  # assign outline color
            loc.symbology = sym  # assign symbology to proper layer
            ap.AddMessage("Project Location Added Successfully")
        except:
            ap.AddError("Project Location color failed to change")

        # project-specific shapefiles add to map
        # color and filter the shapefiles as needed
        #pipeSymbol = r"file_placeholder"
        try:
            if maps.name == '2010_PWWF':
                ap.AddMessage("Beginning 2010 PWWF")
                m_name = maps.name
                maps.addDataFromPath(pwwfEx)
                try:
                    loc = maps.listLayers()[0] # most recently added layer
                    sym = loc.symbology
                    sym.renderer.symbol.size = 2
                    sym.renderer.symbol.color = {'RGB': [85,255,0,0]}
                    app.AddMessage("Pipe Color Changed")
                except:
                    ap.AddError(maps.name + " Pipes Color Not Changed")
                ##epipe_lyr = maps.listLayers(os.path.basename(pwwfEx))  # this grabs the name of the layer as it appears in the table of contents
                #epipe_lyr = maps.listLayers()[0]
                #epipe_name = epipe_lyr.name
                #ap.AddMessage("ex_pwwf layer: " + epipe_name)
                maps.addDataFromPath(ex_flowpath)
                #eflowpath = maps.listLayers()[0]
                #eflowpath_name = eflowpath.name
                #ap.AddMessage("ex_flowpath name: " + eflowpath_name)
                #flowpath_pipe(epipe_name, eflowpath_name, m_name, tempgdb)
                try:
                    loc = maps.listLayers()[0] # most recently added layer
                    sym = loc.symbology
                    sym.renderer.symbol.size = 6
                    sym.renderer.symbol.color = {'RGB': [255, 255, 0, 0]}
                    sym.renderer.symbol.outlineColor = {'RGB': [0, 0, 0, 0]}
                    app.AddMessage("Flowpath Node Color Changed")
                except:
                    ap.AddError(maps.name + " Flowpath Color Not Changed")

                '''
                TO DO:
                Remove 0 flow pipes from symbology as a check in case processor did not in model export
                Select all segments whose first and last vertices touch a flow path node

                everything in comments before and after adding flowpath are intended for use with flowpath function
                '''

                ap.AddMessage("EX PWWF Successful")
                pass

            elif maps.name == '2010_PWWF_With_Project':
                ap.AddMessage("Beginning 2010 PWWF wProj")
                maps.addDataFromPath(pwwfExp)
                try:
                    loc = maps.listLayers()[0] # most recently added layer
                    sym = loc.symbology
                    sym.renderer.symbol.size = 2
                    sym.renderer.symbol.color = {'RGB': [85,255,0,0]}
                    app.AddMessage("Pipe Color Changed")
                except:
                    ap.AddError(maps.name + " Pipes Color Not Changed")
                    
                maps.addDataFromPath(ex_flowpath)
                try:
                    loc = maps.listLayers()[0] # most recently added layer
                    sym = loc.symbology
                    sym.renderer.symbol.size = 6
                    sym.renderer.symbol.color = {'RGB': [255, 255, 0, 0]}
                    sym.renderer.symbol.outlineColor = {'RGB': [0, 0, 0, 0]}
                    app.AddMessage("Flowpath Node Color Changed")
                except:
                    ap.AddError(maps.name + " Flowpath Color Not Changed")
                pass
            
            elif maps.name == '2030_PWWF':
                ap.AddMessage("Beginning 2030 PWWF")
                m_name = maps.name
                maps.addDataFromPath(pwwfF)
                try:
                    loc = maps.listLayers()[0] # most recently added layer
                    sym = loc.symbology
                    sym.renderer.symbol.size = 2
                    sym.renderer.symbol.color = {'RGB': [85,255,0,0]}
                    app.AddMessage("Pipe Color Changed")
                except:
                    ap.AddError(maps.name + " Pipes Color Not Changed")
                    
                #fpipe_lyr = maps.listLayers(os.path.basename(pwwfF)[:-4])[0]  # this grabs the name of the layer as it appears in the table of contents
                maps.addDataFromPath(fcc_flowpath)
                try:
                    loc = maps.listLayers()[0] # most recently added layer
                    sym = loc.symbology
                    sym.renderer.symbol.size = 6
                    sym.renderer.symbol.color = {'RGB': [255, 255, 0, 0]}
                    sym.renderer.symbol.outlineColor = {'RGB': [0, 0, 0, 0]}
                    app.AddMessage("Flowpath Node Color Changed")
                except:
                    ap.AddError(maps.name + " Flowpath Color Not Changed")
                #fflowpath = maps.listLayers(os.path.basename(fcc_flowpath)[:-4])[0]
                #flowpath_pipe(fpipe_lyr, fflowpath, m_name, tempgdb)
                pass
            
            elif maps.name == '2030_PWWF_With_Project':
                ap.AddMessage("Beginning 2030 PWWF wProj")
                maps.addDataFromPath(pwwfFp)
                try:
                    loc = maps.listLayers()[0] # most recently added layer
                    sym = loc.symbology
                    sym.renderer.symbol.size = 2
                    sym.renderer.symbol.color = {'RGB': [85,255,0,0]}
                    app.AddMessage("Pipe Color Changed")
                except:
                    ap.AddError(maps.name + " Pipes Color Not Changed")
                    
                maps.addDataFromPath(fcc_flowpath)
                try:
                    loc = maps.listLayers()[0] # most recently added layer
                    ap.AddMessage(loc.name)
                    sym = loc.symbology
                    try:
                        sym.renderer.symbol.size = 6
                    except:
                        ap.AddError("size no change")
                    sym.renderer.symbol.color = {'RGB': [255, 255, 0, 0]}
                    sym.renderer.symbol.outlineColor = {'RGB': [0, 0, 0, 0]}
                    app.AddMessage("Flowpath Node Color Changed")
                except:
                    ap.AddError(maps.name + " Flowpath Color Not Changed")
                pass
            
            else:
                pass
        except:
            ap.AddError("Sewer data failed to add to layout " + maps.name)

    toc = time.perf_counter()
    ap.AddMessage(f"Sewer Layout Change Time Elapsed: {toc-tic:0.2f} seconds")
    return

'''begin working script'''
if figureProjType == "Sewer":
    sewer_layout_change()
    ap.AddMessage("Sewer Changes Successful")
    
elif figureProjType == "Water":
    water_layout_change()
    ap.AddMessage("Water Changes Successful")
    
elif figureProjType == "Location":
    location_layout_change()
    ap.AddMessage("Project Location Changes Successful")
    
else:
    ap.AddWarning("Choose Project Type")
