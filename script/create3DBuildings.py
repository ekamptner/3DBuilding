##############################
# Created by: Erika Kamptner
# Last Update: 03/11/2019
# Description: Consolidates scripts from ESRI Local 3D Government Scene
#############################

import arcpy
from arcpy.sa import *
import os, subprocess

laz = "C:\Projects\\3DBuilding\data\lidar\laz"
las = "C:\Projects\\3DBuilding\data\lidar\las"
lasd = 'C:\Projects\\3DBuilding\data\lidar\lasd'

originaldem = r"T:\GIS\Projects\LiDAR\Project\QC\data\citywide\citywide_TopoBathy_final\mosaics\Bare_Earth\Topobathymetric_Bare_Earth\\be_NYC.tif"
originaldsm = r"T:\GIS\Projects\LiDAR\Project\QC\data\citywide\citywide_TopoBathy_final\mosaics\Highest_Hit\hh_NYC.tif"
originalbldg = "T:\GIS\Projects\LiDAR\Project\data\Reference datasets\Citywide\Buildings.shp"

clip = "C:\Projects\\3DBuilding\data\lidar\extent\LAS_extent.shp"

dem = r"C:\Projects\\3DBuilding\data\elevationrasters\dem\\nyc_sample_dem.tif"
dsm = r"C:\Projects\\3DBuilding\data\elevationrasters\dsm\\nyc_sample_dsm.tif"
ndsm = r"C:\Projects\\3DBuilding\data\elevationrasters\\ndsm\\nyc_ndsm.tif"
bldg_extent = "C:\Projects\\3DBuilding\data\\buildings\\buildings_exent.shp"
bldg_buffer = "C:\Projects\\3DBuilding\data\\buildings\\buildings_buffer.shp"


demMean = "C:\Projects\\3DBuilding\data\elevationrasters\dem\\nyc_sample_dem_mean.tif"
modDEM = "C:\Projects\\3DBuilding\data\elevationrasters\dem\\nyc_sample_dem_mod.tif"
outIsNull = "C:\Projects\\3DBuilding\data\elevationrasters\\null.tif"

def create_lasdataset(laz, las, lasd):
    # unzip laz files and write to appropriate sub directories
    # create lasdataset (ESRI format) using arcpy

    print('Creating LAS dataset')
    os.chdir(laz)
    subprocess.call("T:/GIS/Projects/LiDAR/Project/tools/laszip *.laz")

    print('Moving las files to las directory')
    call = "move *.las C:\Projects\\3DBuilding\data\lidar\las"
    subprocess.call(call)

    print('Creating LAS Dataset')
    arcpy.CreateLasDataset_management(las, lasd)

    print('Finished!')

def create_elevations(citywide):

    # get project area extent
    if citywide == 0:
        print("Calculating extent of project area...")
        desc = arcpy.Describe(clip)
        Xmin = desc.extent.XMin
        Xmax = desc.extent.XMax
        Ymin = desc.extent.YMin
        Ymax = desc.extent.YMax

        extent = str(Xmin) + " " + str(Ymin) + " " + str(Xmax) + " " + str(Ymax)
        print("Extents: " + extent)
    else:
        extent = " "

    # clip to processing extent
    print("Clipping dem and dsm to project area...")
    arcpy.management.Clip(originaldem, extent, dem, clip, -3.402823e+38, "ClippingGeometry", "NO_MAINTAIN_EXTENT")
    print("dem complete")
    arcpy.management.Clip(originaldsm, extent, dsm, clip, -3.402823e+38, "ClippingGeometry", "NO_MAINTAIN_EXTENT")
    print("dsm complete")

    # create ndsm from existing dem and dsm rasters
    print("Generating ndsm...")
    arcpy.CheckOutExtension("Spatial")
    outRaster = Raster(dsm) - Raster(dem)
    outRaster.save(ndsm)
    arcpy.CheckInExtension("Spatial")
    print("ndsm complete")

def modify_dem():
    # modify ndsm with building footprints -- flatten where footprint exists so buildings sit flat on surface
    arcpy.env.workspace = "C:\Projects\\3DBuilding\data\elevationrasters"

    # clip buildings to project area
    print("Clipping bldgs layer to project area... ")
    arcpy.Clip_analysis(originalbldg, clip, bldg_extent)

    # create small buffer around buildings
    print("Creating buffer around buildings layer")
    arcpy.Buffer_analysis(bldg_extent, bldg_buffer, 1, "FULL")

    # create zonal statistics with mean elevation in building buffer areas
    print("Zonal statistic around bldgs")
    arcpy.CheckOutExtension("Spatial")
    meanRaster = arcpy.sa.ZonalStatistics(bldg_buffer, "BIN", dem, "MEAN", "true")
    meanRaster.save(demMean)

    print("Create null mask...")
    nullMask = arcpy.sa.IsNull(meanRaster)
    nullMask.save(outIsNull)

    print("Creating final modified DEM...")
    outConRaster = arcpy.sa.Con(outIsNull, dem, demMean)
    outConRaster.save(modDEM)

    print("Cleaning up temporary files...")
    arcpy.Delete_management(demMean)
    arcpy.Delete_management(outIsNull)

def segment_roofs(bldg_buffer, dsm):
    arcpy.env.workspace = "C:\Projects\\3DBuilding"
    roofsegment = r"\data\\buildings\nyc_sample_roofsegment.shp"

    print("Import toolbox...")
    arcpy.ImportToolbox("LOD2buildings")

    print("Generating segment roofs")
    arcpy.LOD2buildings.SegmentRoofParts(bldg_buffer, dsm, 12, 12, 538, "3 Meters", False, roofsegment)

    print("LOD2 buildings complete")

    seg_raster = arcpy.sa.SegmentMeanShift(dsm, 12, 12, "3 Meters")
    seg_raster.save(sms_dsm)

    arcpy.RasterToPolygon_conversion(in_raster=sms_dsm, out_polygon_features=sms_poly, simplify='NO_SIMPLIFY')
arcpy.MakeFeatureLayer_management(sms_poly, poly_select, g_ESRI_variable_10)
def create_building():



if __name__ == "__main__":
