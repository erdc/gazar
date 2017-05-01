# -*- coding: utf-8 -*-
#
#  test_grid_tools.py
#  sloot
#
#  Author : Alan D Snow, 2017.
#  License: BSD 3-Clause

from numpy.testing import assert_almost_equal
from os import path
from osgeo import osr
from pyproj import Proj
import pytest
from shutil import copy

from .conftest import compare_files

from sloot.grid import GDALGrid


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


def test_gdal_grid(prep, tgrid):
    """
    Tests rasterize_shapefile default using num cells
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
