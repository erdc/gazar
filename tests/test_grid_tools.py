# -*- coding: utf-8 -*-
#
#  test_grid_tools.py
#  gazar
#
#  Author : Alan D Snow, 2017.
#  License: BSD 3-Clause

from numpy.testing import assert_almost_equal
import numpy as np
from os import path
from osgeo import osr
from pyproj import Proj
import pytest
from shutil import copy

from .conftest import compare_files

from gazar.grid import ArrayGrid, GDALGrid, utm_proj_from_latlon
import gazar
gazar.log_to_console(level='DEBUG')


@pytest.fixture
def prep(request, tgrid):
    base_input_raster = path.join(tgrid.input,
                                  'gdal_grid',
                                  'gmted_elevation.tif')

    input_raster = path.join(tgrid.write,
                             'test_grid.tif')

    compare_path = path.join(tgrid.compare,
                             'gdal_grid')

    try:
        copy(base_input_raster, input_raster)
    except OSError:
        pass

    return input_raster, compare_path


def test_gdal_grid_projection(prep, tgrid):
    """
    Tests test_gdal_grid_projection
    """
    input_raster, compare_path = prep
    compare_projection_file = path.join(compare_path, 'test_projection.prj')
    ggrid = GDALGrid(input_raster, compare_projection_file)

    # check properties
    assert_almost_equal(ggrid.geotransform,
                        (120.99986111111112,
                         0.008333333333333333,
                         0.0,
                         16.008194444444445,
                         0.0,
                         -0.008333333333333333))
    assert ggrid.x_size == 120
    assert ggrid.y_size == 120
    assert ggrid.num_bands == 1
    assert ggrid.wkt == ('GEOGCS["WGS 84",DATUM["WGS_1984",'
                         'SPHEROID["WGS 84",6378137,298.257223563,'
                         'AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG",'
                         '"6326"]],PRIMEM["Greenwich",0],UNIT["degree",'
                         '0.0174532925199433],AUTHORITY["EPSG","4326"]]')
    assert ggrid.proj4 == '+proj=longlat +datum=WGS84 +no_defs '


def test_gdal_grid(prep, tgrid):
    """
    Tests test_gdal_grid
    """
    input_raster, compare_path = prep
    ggrid = GDALGrid(input_raster)

    # check properties
    assert_almost_equal(ggrid.geotransform,
                        (120.99986111111112,
                         0.008333333333333333,
                         0.0,
                         16.008194444444445,
                         0.0,
                         -0.008333333333333333))
    assert ggrid.x_size == 120
    assert ggrid.y_size == 120
    assert ggrid.num_bands == 1
    assert ggrid.wkt == ('GEOGCS["WGS 84",DATUM["WGS_1984",'
                         'SPHEROID["WGS 84",6378137,298.257223563,'
                         'AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG",'
                         '"6326"]],PRIMEM["Greenwich",0],UNIT["degree",'
                         '0.0174532925199433],AUTHORITY["EPSG","4326"]]')
    assert ggrid.proj4 == '+proj=longlat +datum=WGS84 +no_defs '
    assert isinstance(ggrid.proj, Proj)
    assert ggrid.epsg == '4326'
    sp_ref = osr.SpatialReference()
    sp_ref.ImportFromEPSG(32651)

    latitude, longitude = ggrid.latlon
    assert latitude.shape == (120, 120)
    assert longitude.shape == (120, 120)
    assert_almost_equal(latitude[20:22, 20:22],
                        [[15.83736111, 15.83736111],
                         [15.82902778, 15.82902778]])
    assert_almost_equal(longitude[20:22, 20:22],
                        [[121.17069444, 121.17902778],
                         [121.17069444, 121.17902778]])
    # check functions
    assert_almost_equal(ggrid.bounds(),
                        (120.99986111111112,
                         121.99986111111112,
                         15.008194444444445,
                         16.008194444444445))
    assert_almost_equal(ggrid.bounds(as_geographic=True),
                        (120.99986111111112,
                         121.99986111111112,
                         15.008194444444445,
                         16.008194444444445))
    assert_almost_equal(ggrid.bounds(as_utm=True),
                        (284940.2424665766,
                         393009.70510977274,
                         1659170.2715823832,
                         1770872.3212051827))
    assert_almost_equal(ggrid.bounds(as_projection=sp_ref),
                        (284940.2424665766,
                         393009.70510977274,
                         1659170.2715823832,
                         1770872.3212051827))
    x_loc, y_loc = ggrid.pixel2coord(5, 10)
    assert_almost_equal((x_loc, y_loc),
                        (121.04569444444445, 15.920694444444445))

    assert ggrid.coord2pixel(x_loc, y_loc) == (5, 10)
    lon, lat = ggrid.pixel2lonlat(5, 10)
    assert_almost_equal((lon, lat),
                        (121.04569444444445, 15.920694444444445))
    assert ggrid.lonlat2pixel(lon, lat) == (5, 10)

    with pytest.raises(IndexError):
        x_loc, y_loc = ggrid.pixel2coord(500000, 10)

    with pytest.raises(IndexError):
        x_loc, y_loc = ggrid.pixel2coord(5, 10000000)

    with pytest.raises(IndexError):
        x_coord, y_coord = ggrid.coord2pixel(1870872, 1669170)

    with pytest.raises(IndexError):
        x_coord, y_coord = ggrid.coord2pixel(284940, 10000000)

        # check write functions
    projection_name = 'test_projection.prj'
    out_projection_file = path.join(tgrid.write, projection_name)
    ggrid.write_prj(out_projection_file)
    compare_projection_file = path.join(compare_path, projection_name)
    compare_files(compare_projection_file, out_projection_file)

    tif_name = 'test_tif.tif'
    out_tif_file = path.join(tgrid.write, tif_name)
    ggrid.to_tif(out_tif_file)
    compare_tif_file = path.join(compare_path, tif_name)
    compare_files(out_tif_file, compare_tif_file, raster=True)

    tif_prj_name = 'test_tif_32651.tif'
    out_tif_file = path.join(tgrid.write, tif_prj_name)
    proj_grid = ggrid.to_projection(sp_ref)
    proj_grid.to_tif(out_tif_file)
    compare_tif_file = path.join(compare_path, tif_prj_name)
    compare_files(out_tif_file, compare_tif_file, raster=True)

    grass_name = 'test_grass_ascii.asc'
    out_grass_file = path.join(tgrid.write, grass_name)
    ggrid.to_grass_ascii(out_grass_file)
    compare_grass_file = path.join(compare_path, grass_name)
    compare_files(out_grass_file, compare_grass_file, raster=True)

    arc_name = 'test_arc_ascii.asc'
    out_arc_file = path.join(tgrid.write, arc_name)
    ggrid.to_arc_ascii(out_arc_file)
    compare_arc_file = path.join(compare_path, arc_name)
    compare_files(out_arc_file, compare_arc_file, raster=True)


def test_array_grid(prep):
    """
    Test array grid
    """
    input_raster, compare_path = prep
    ggrid = GDALGrid(input_raster)

    arrg = ArrayGrid(in_array=ggrid.np_array(masked=True),
                     wkt_projection=ggrid.wkt,
                     geotransform=ggrid.geotransform)

    assert_almost_equal(ggrid.geotransform,
                        arrg.geotransform)
    assert ggrid.x_size == arrg.x_size
    assert ggrid.y_size == arrg.y_size
    assert ggrid.proj4 == arrg.proj4
    assert (ggrid.np_array() == arrg.np_array()).all()


def test_array_grid_nodata(prep):
    """
    Test array grid with nodata
    """
    input_raster, compare_path = prep
    ggrid = GDALGrid(input_raster)
    gnodata = ggrid.dataset.GetRasterBand(1).GetNoDataValue()
    arrg = ArrayGrid(in_array=ggrid.np_array(),
                     wkt_projection=ggrid.wkt,
                     geotransform=ggrid.geotransform,
                     nodata_value=gnodata)

    anodata = arrg.dataset.GetRasterBand(1).GetNoDataValue()
    assert gnodata == anodata
    assert_almost_equal(ggrid.geotransform,
                        arrg.geotransform)
    assert ggrid.x_size == arrg.x_size
    assert ggrid.y_size == arrg.y_size
    assert ggrid.proj4 == arrg.proj4
    assert (ggrid.np_array() == arrg.np_array()).all()


def test_array_grid3d(prep):
    """
    Test array grid 3d version
    """
    input_raster, compare_path = prep
    ggrid = GDALGrid(input_raster)
    orig_array = ggrid.np_array(masked=True)
    grid_array = np.array([orig_array, 5 * orig_array, 4 * orig_array])
    arrg = ArrayGrid(in_array=grid_array,
                     wkt_projection=ggrid.wkt,
                     geotransform=ggrid.geotransform)

    assert_almost_equal(ggrid.geotransform,
                        arrg.geotransform)
    assert ggrid.x_size == arrg.x_size
    assert ggrid.y_size == arrg.y_size
    assert ggrid.proj4 == arrg.proj4
    assert arrg.num_bands == 3
    assert (arrg.np_array(band='all') == grid_array).all()


def test_array_grid3d_nodata(prep):
    """
    Test array grid 3d version with nodata
    """
    input_raster, compare_path = prep
    ggrid = GDALGrid(input_raster)
    gnodata = ggrid.dataset.GetRasterBand(1).GetNoDataValue()
    orig_array = ggrid.np_array(masked=True)
    grid_array = np.array([orig_array, 5 * orig_array, 4 * orig_array])
    arrg = ArrayGrid(in_array=grid_array,
                     wkt_projection=ggrid.wkt,
                     geotransform=ggrid.geotransform,
                     nodata_value=gnodata)

    assert_almost_equal(ggrid.geotransform,
                        arrg.geotransform)
    assert ggrid.x_size == arrg.x_size
    assert ggrid.y_size == arrg.y_size
    assert ggrid.proj4 == arrg.proj4
    assert arrg.num_bands == 3
    assert (arrg.np_array(band='all') == grid_array).all()

    for band_id in range(1, arrg.num_bands + 1):
        anodata = arrg.dataset.GetRasterBand(band_id).GetNoDataValue()
        assert gnodata == anodata


def test_utm_from_latlon():
    """
    Test retrieving a UTM projection from a latitude and longitude
    """
    assert utm_proj_from_latlon(-25.2744, 133.7751) == \
        '+proj=utm +zone=53 +south +datum=WGS84 +units=m +no_defs '
