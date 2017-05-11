# -*- coding: utf-8 -*-
#
#  gazar.shape
#
#  Author : Alan D Snow, 2017.
#  License: BSD 3-Clause

"""gazar.shape
This module is a collection of GDAL functions for shapefiles.
Documentation can be found at `_gazar Documentation HOWTO`_.

.. _gazar Documentation HOWTO:
   https://github.com/snowman2/gazar

"""
# default modules
from os import path
# external modules
from osgeo import gdal, ogr, osr
# local modules
from .grid import (GDALGrid, load_raster, project_to_geographic,
                   utm_proj_from_latlon)


def reproject_layer(in_path, out_path, out_spatial_ref):
    """
    Reprojects a shapefile layer.

    Based on: https://pcjericks.github.io/
       py-gdalogr-cookbook/projection.html

    Parameters
    ----------
        in_path: :obj:`str`
            The path to the input shapefile layer.
        out_path: :obj:`str`
            The path to the output shapefile layer.
        out_spatial_ref: :func:`osr.SpatialReference`
            The output spatial reference.

    """
    driver = ogr.GetDriverByName('ESRI Shapefile')

    # get the input layer
    in_data_set = driver.Open(in_path)
    in_layer = in_data_set.GetLayer()

    # input SpatialReference
    in_spatial_ref = in_layer.GetSpatialRef()

    # create the CoordinateTransformation
    coord_trans = osr.CoordinateTransformation(in_spatial_ref,
                                               out_spatial_ref)

    # create the output layer
    output_shapefile = out_path
    if path.exists(output_shapefile):
        driver.DeleteDataSource(output_shapefile)
    out_data_set = driver.CreateDataSource(output_shapefile)
    out_layer = out_data_set.CreateLayer("", geom_type=ogr.wkbMultiPolygon)

    # add fields
    in_layer_defn = in_layer.GetLayerDefn()
    for i in range(0, in_layer_defn.GetFieldCount()):
        field_defn = in_layer_defn.GetFieldDefn(i)
        out_layer.CreateField(field_defn)

    # get the output layer's feature definition
    out_layer_defn = out_layer.GetLayerDefn()

    # loop through the input features
    in_feature = in_layer.GetNextFeature()
    while in_feature:
        # get the input geometry
        geom = in_feature.GetGeometryRef()
        # reproject the geometry
        geom.Transform(coord_trans)
        # create a new feature
        out_feature = ogr.Feature(out_layer_defn)
        # set the geometry and attribute
        out_feature.SetGeometry(geom)
        for i in range(0, out_layer_defn.GetFieldCount()):
            out_feature.SetField(out_layer_defn.GetFieldDefn(i).GetNameRef(),
                                 in_feature.GetField(i))
        # add the feature to the shapefile
        out_layer.CreateFeature(out_feature)
        # dereference the features and get the next input feature
        out_feature = None
        in_feature = in_layer.GetNextFeature()

    # Save and close the shapefiles
    in_data_set = None
    out_data_set = None

    # write projection
    shapefile_basename = path.splitext(out_path)[0]
    projection_file_name = "{shapefile_basename}.prj" \
                           .format(shapefile_basename=shapefile_basename)
    with open(projection_file_name, 'w') as prj_file:
        prj_file.write(out_spatial_ref.ExportToWkt())
        prj_file.close()


def rasterize_shapefile(shapefile_path,
                        out_raster_path=None,
                        shapefile_attribute=None,
                        x_cell_size=None,
                        y_cell_size=None,
                        x_num_cells=None,
                        y_num_cells=None,
                        match_grid=None,
                        raster_wkt_proj=None,
                        convert_to_utm=False,
                        raster_dtype=gdal.GDT_Int32,
                        raster_nodata=-9999,
                        as_gdal_grid=False):
    """
    Convert shapefile to raster from specified attribute

    Parameters
    ----------
        shapefile_path : :obj:`str`
            Path to shapefile.
        out_raster_path : :obj:`str`, optional
            Path to raster to be generated.
        shapefile_attribute: :obj:`str`, optional
            Attribute to be rasterized.
        x_cell_size: float, optional
            Longitude cell size in output projection.
        y_cell_size: float, optional
            Latitude cell size in output projection.
        x_num_cells: int, optional
            Number of cells in latitude.
        y_num_cells: int, optional
            Number of cells in longitude.
        match_grid: str or :func:`gdal.Dataset` or :func:`~GDALGrid`, optional
            Grid to match for output.
        raster_wkt_proj: :obj:`str`, optional
            WKT projections string for output grid.
        convert_to_utm: bool, optional
            Convert grid to UTM automatically. Default is False.
        raster_dtype: :func:`osgeo.gdalconst`
            Output grid datatype (GDT). Default is gdal.GDT_Int32.
        raster_nodata: float or int, optional
            No data value for output raster. Default is -9999,
        as_gdal_grid: bool, optional
            Return as :func:`~GDALGrid`. Default is False.

    Returns
    -------
    None or :func:`~GDALGrid`
        It will return :func:`~GDALGrid` if `as_gdal_grid` is True.
        Otherwise, it will not return anything.


    Example Default::

        from gloot.grid import rasterize_shapefile

        shapefile_path = 'shapefile.shp'
        new_grid = 'new_grid.tif'
        rasterize_shapefile(shapefile_path,
                            new_grid,
                            x_num_cells=50,
                            y_num_cells=50,
                            raster_nodata=0,
                            )

    Example GDALGrid to ASCII with UTM::

        from gazar.grid import rasterize_shapefile

        shapefile_path = 'shapefile.shp'
        new_grid = 'new_grid.asc'
        gr = rasterize_shapefile(shapefile_path,
                                 x_num_cells=50,
                                 y_num_cells=50,
                                 raster_nodata=0,
                                 convert_to_utm=True,
                                 as_gdal_grid=True,
                                 )
        gr.to_grass_ascii(new_grid, print_nodata=False)

    """
    if as_gdal_grid:
        raster_driver = gdal.GetDriverByName('MEM')
        out_raster_path = ''
    elif out_raster_path is not None:
        raster_driver = gdal.GetDriverByName('GTiff')
    else:
        raise ValueError("Either out_raster_path or as_gdal_grid "
                         "need to be set ...")

    # open the data source
    shapefile = ogr.Open(shapefile_path)
    source_layer = shapefile.GetLayer(0)

    x_min, x_max, y_min, y_max = source_layer.GetExtent()
    shapefile_spatial_ref = source_layer.GetSpatialRef()
    reprojected_layer = None
    # determine UTM projection from centroid of shapefile
    if convert_to_utm:
        # Make sure projected into global projection
        lon_min, lat_max = project_to_geographic(x_min, y_max,
                                                 shapefile_spatial_ref)
        lon_max, lat_min = project_to_geographic(x_max, y_min,
                                                 shapefile_spatial_ref)

        # get UTM projection for watershed
        raster_wkt_proj = utm_proj_from_latlon((lat_min + lat_max) / 2.0,
                                               (lon_min + lon_max) / 2.0,
                                               as_wkt=True)
    # reproject shapefile to new projection
    if raster_wkt_proj is not None:
        shapefile_basename = path.splitext(shapefile_path)[0]
        reprojected_layer = "{shapefile_basename}_projected.shp" \
            .format(shapefile_basename=shapefile_basename)
        out_spatial_ref = osr.SpatialReference()
        out_spatial_ref.ImportFromWkt(raster_wkt_proj)
        reproject_layer(shapefile_path, reprojected_layer, out_spatial_ref)
        reprojected_shapefile = ogr.Open(reprojected_layer)
        source_layer = reprojected_shapefile.GetLayer(0)

        x_min, x_max, y_min, y_max = source_layer.GetExtent()
        shapefile_spatial_ref = source_layer.GetSpatialRef()

    if match_grid is not None:
        # grid to match
        match_ds, match_proj = load_raster(match_grid)
        match_geotrans = match_ds.GetGeoTransform()
        x_num_cells = match_ds.RasterXSize
        y_num_cells = match_ds.RasterYSize

    elif x_cell_size is not None and y_cell_size is not None:
        # caluclate nuber of cells in extent
        x_num_cells = int((x_max - x_min) / x_cell_size)
        y_num_cells = int((y_max - y_min) / y_cell_size)
        match_geotrans = (x_min, x_cell_size, 0, y_max, 0, -y_cell_size)
        match_proj = shapefile_spatial_ref.ExportToWkt()

    elif x_num_cells is not None and y_num_cells is not None:
        x_cell_size = (x_max - x_min) / float(x_num_cells)
        y_cell_size = (y_max - y_min) / float(y_num_cells)
        match_geotrans = (x_min, x_cell_size, 0, y_max, 0, -y_cell_size)
        match_proj = shapefile_spatial_ref.ExportToWkt()

    else:
        raise ValueError("Invalid parameters for output grid entered ...")

    # geotiff
    target_ds = raster_driver.Create(out_raster_path,
                                     x_num_cells,
                                     y_num_cells,
                                     1,
                                     raster_dtype)

    target_ds.SetGeoTransform(match_geotrans)
    target_ds.SetProjection(match_proj)
    band = target_ds.GetRasterBand(1)
    band.SetNoDataValue(raster_nodata)

    # rasterize
    if shapefile_attribute is not None:
        err = gdal.RasterizeLayer(target_ds, [1], source_layer,
                                  options=["ATTRIBUTE={0}"
                                           .format(shapefile_attribute)])
    else:
        err = gdal.RasterizeLayer(target_ds, [1], source_layer,
                                  burn_values=[1])

    if err != 0:
        raise Exception("Error rasterizing layer: %s" % err)

    if raster_wkt_proj is not None and raster_wkt_proj != match_proj:
        # from http://gis.stackexchange.com/questions/139906/
        #    replicating-result-of-gdalwarp-using-gdal-python-bindings"""
        error_threshold = 0.125  # use same value as in gdalwarp
        resampling = gdal.GRA_NearestNeighbour

        # Call AutoCreateWarpedVRT() to fetch default values
        # for target raster dimensions and geotransform
        target_ds = gdal.AutoCreateWarpedVRT(target_ds,
                                             None,
                                             raster_wkt_proj,
                                             resampling,
                                             error_threshold)
        if not as_gdal_grid:
            # Create the final warped raster
            target_ds = gdal.GetDriverByName('GTiff') \
                .CreateCopy(out_raster_path, target_ds)

    # clean up
    if reprojected_layer is not None:
        driver = ogr.GetDriverByName("ESRI Shapefile")
        if path.exists(reprojected_layer):
            driver.DeleteDataSource(reprojected_layer)

    if as_gdal_grid:
        return GDALGrid(target_ds)
