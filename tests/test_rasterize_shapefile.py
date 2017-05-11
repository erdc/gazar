# -*- coding: utf-8 -*-
#
#  test_rasterize_shapefile.py
#  gazar
#
#  Author : Alan D Snow, 2017.
#  License: BSD 3-Clause

from glob import glob
from os import path
import os
import pytest
from shutil import copy

from .conftest import compare_files

from gazar.shape import rasterize_shapefile
import gazar


@pytest.fixture
def get_wkt(request):
    return ('PROJCS["WGS 84 / UTM zone 51N",GEOGCS["WGS 84",'
            'DATUM["WGS_1984",SPHEROID["WGS 84",6378137,'
            '298.257223563,AUTHORITY["EPSG","7030"]],'
            'AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,'
            'AUTHORITY["EPSG","8901"]],UNIT["degree",'
            '0.01745329251994328,AUTHORITY["EPSG","9122"]],'
            'AUTHORITY["EPSG","4326"]],UNIT["metre",1,'
            'AUTHORITY["EPSG","9001"]],'
            'PROJECTION["Transverse_Mercator"],'
            'PARAMETER["latitude_of_origin",0],'
            'PARAMETER["central_meridian",123],'
            'PARAMETER["scale_factor",0.9996],'
            'PARAMETER["false_easting",500000],'
            'PARAMETER["false_northing",0],'
            'AUTHORITY["EPSG","32651"],AXIS["Easting",EAST],'
            'AXIS["Northing",NORTH]]')


class MaskTest:
    def __init__(self, tgrid):
        tgrid.clean()

        self.tgrid = tgrid

        # define global variables
        self.shapefile_path = \
            path.join(tgrid.write,
                      'phillipines_5070115700.shp')

        self.projected_shapefile = \
            path.join(tgrid.write,
                      'phillipines_5070115700_projected.shp')
        self.compare_path = path.join(tgrid.compare,
                                      'gdal_grid')
        # copy shapefile
        shapefile_basename = path.join(tgrid.input,
                                       'gdal_grid',
                                       'phillipines_5070115700.*')

        for shapefile_part in glob(shapefile_basename):
            try:
                copy(shapefile_part,
                     path.join(tgrid.write, path.basename(shapefile_part)))
            except OSError:
                pass

    def compare_masks(self, mask_name):
        """compare mask files"""
        new_mask_grid = path.join(self.tgrid.write, mask_name)
        compare_msk_file = path.join(self.compare_path, mask_name)
        compare_files(compare_msk_file, new_mask_grid, raster=True)


@pytest.fixture
def prep(request, tgrid):
    _mt = MaskTest(tgrid)

    # RUN TEST
    yield _mt

    # BEFORE TEARDOWN
    # make sure cleanup worked (fails on Windows)
    if os.name != 'nt':
        assert not path.exists(_mt.projected_shapefile)


def test_rasterize_num_cells(prep):
    """
    Tests rasterize_shapefile default using num cells
    """
    mask_name = 'mask_50.msk'
    new_mask_grid = path.join(prep.tgrid.write, mask_name)
    rasterize_shapefile(prep.shapefile_path,
                        new_mask_grid,
                        x_num_cells=50,
                        y_num_cells=50)
    # compare msk
    prep.compare_masks(mask_name)


def test_rasterize_num_cells_utm(prep):
    """
    Tests rasterize_shapefile default using num cells and utm
    """
    mask_name = 'mask_50_utm.msk'
    new_mask_grid = path.join(prep.tgrid.write, mask_name)
    rasterize_shapefile(prep.shapefile_path,
                        new_mask_grid,
                        x_num_cells=50,
                        y_num_cells=50,
                        raster_nodata=0,
                        convert_to_utm=True)
    # compare msk
    prep.compare_masks(mask_name)


def test_rasterize_num_cells_wkt(prep, get_wkt):
    """
    Tests rasterize_shapefile default using num cells and wkt
    """
    mask_name = 'mask_50_wkt.msk'
    new_mask_grid = path.join(prep.tgrid.write, mask_name)
    rasterize_shapefile(prep.shapefile_path,
                        new_mask_grid,
                        x_num_cells=50,
                        y_num_cells=50,
                        raster_nodata=0,
                        raster_wkt_proj=get_wkt)
    # compare msk
    prep.compare_masks(mask_name)


def test_rasterize_num_cells_utm_ascii(prep):
    """
    Tests rasterize_shapefile default using num cells and utm to ascii
    """
    mask_name = 'mask_50_utm_ascii.msk'
    new_mask_grid = path.join(prep.tgrid.write, mask_name)
    gr = rasterize_shapefile(prep.shapefile_path,
                             x_num_cells=50,
                             y_num_cells=50,
                             raster_nodata=0,
                             convert_to_utm=True,
                             as_gdal_grid=True)
    gr.to_grass_ascii(new_mask_grid, print_nodata=False)
    # compare msk
    prep.compare_masks(mask_name)


def test_rasterize_num_cells_ascii(prep):
    """
    Tests rasterize_shapefile default using num cells to ascii
    """
    mask_name = 'mask_50_ascii.msk'
    new_mask_grid = path.join(prep.tgrid.write, mask_name)
    gr = rasterize_shapefile(prep.shapefile_path,
                             x_num_cells=50,
                             y_num_cells=50,
                             raster_nodata=0,
                             as_gdal_grid=True)
    gr.to_grass_ascii(new_mask_grid, print_nodata=False)
    # compare msk
    prep.compare_masks(mask_name)


def test_rasterize_num_cells_wkt_ascii(prep, get_wkt):
    """
    Tests rasterize_shapefile default using num cells
    """
    mask_name = 'mask_50_wkt_ascii.msk'
    new_mask_grid = path.join(prep.tgrid.write, mask_name)
    gr = rasterize_shapefile(prep.shapefile_path,
                             x_num_cells=50,
                             y_num_cells=50,
                             raster_nodata=0,
                             raster_wkt_proj=get_wkt,
                             as_gdal_grid=True)
    gr.to_grass_ascii(new_mask_grid, print_nodata=False)
    # compare msk
    prep.compare_masks(mask_name)


def test_rasterize_cell_size_ascii(prep):
    """
    Tests rasterize_shapefile default using cell size to ascii
    """
    mask_name = 'mask_cell_size_ascii.msk'
    new_mask_grid = path.join(prep.tgrid.write, mask_name)
    gr = rasterize_shapefile(prep.shapefile_path,
                             x_cell_size=0.01,
                             y_cell_size=0.01,
                             raster_nodata=0,
                             as_gdal_grid=True)
    gr.to_grass_ascii(new_mask_grid, print_nodata=False)
    # compare msk
    prep.compare_masks(mask_name)


def test_rasterize_cell_size_ascii_utm(prep):
    """
    Tests rasterize_shapefile using cell size to ascii in utm
    """
    gazar.log_to_console(False)
    log_file = path.join(prep.tgrid.write, 'gazar.log')
    gazar.log_to_file(filename=log_file, level='DEBUG')

    mask_name = 'mask_cell_size_ascii_utm.msk'
    new_mask_grid = path.join(prep.tgrid.write, mask_name)
    gr = rasterize_shapefile(prep.shapefile_path,
                             x_cell_size=1000,
                             y_cell_size=1000,
                             raster_nodata=0,
                             as_gdal_grid=True,
                             convert_to_utm=True)
    gr.to_grass_ascii(new_mask_grid, print_nodata=False)

    # compare msk
    prep.compare_masks(mask_name)
    gazar.log_to_file(False)

    # compare log_to_file
    compare_log_file = path.join(prep.tgrid.compare, 'gazar.log')
    with open(log_file) as lgf, open(compare_log_file) as clgf:
        assert lgf.read() == clgf.read()
