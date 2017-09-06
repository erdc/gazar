# -*- coding: utf-8 -*-
#
#  conftest.py
#  gazar
#
#  Author : Alan D Snow, 2017.
#  License: BSD 3-Clause

import os

from numpy import array
from numpy.testing import assert_almost_equal
import pytest
from osgeo import gdal, ogr
from shutil import rmtree

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))


def compare_files(original, new, raster=False, shapefile=False,
                  precision=7):
    """Compare the contents of two files"""
    if raster:
        ds_o = gdal.Open(original)
        ds_n = gdal.Open(new)

        # compare data
        r_o = array(ds_o.ReadAsArray())
        r_n = array(ds_n.ReadAsArray())
        assert_almost_equal(r_o, r_n, decimal=precision)

        # compare geotransform
        assert_almost_equal(ds_o.GetGeoTransform(),
                            ds_n.GetGeoTransform(),
                            decimal=9)

        # compare band counts
        assert ds_o.RasterCount == ds_n.RasterCount
        # compare nodata
        for band_id in range(1, ds_o.RasterCount + 1):
            assert (ds_o.GetRasterBand(band_id).GetNoDataValue() ==
                    ds_n.GetRasterBand(band_id).GetNoDataValue())
    elif shapefile:
        driver = ogr.GetDriverByName('ESRI Shapefile')

        # get the input layer
        orig_data_set = driver.Open(original)
        orig_layer = orig_data_set.GetLayer()
        orig_layer_def = orig_layer.GetLayerDefn()

        new_data_set = driver.Open(new)
        new_layer = new_data_set.GetLayer()
        new_layer_def = new_layer.GetLayerDefn()

        # make sure fields the same
        assert orig_layer_def.GetFieldCount() == new_layer_def.GetFieldCount()

        for fid in range(orig_layer_def.GetFieldCount()):
            assert orig_layer_def.GetFieldDefn(fid).GetName() == \
                new_layer_def.GetFieldDefn(fid).GetName()

            assert orig_layer_def.GetFieldDefn(fid).GetType() == \
                new_layer_def.GetFieldDefn(fid).GetType()

        # make sure feature count the same
        assert orig_layer.GetFeatureCount() == new_layer.GetFeatureCount()

        # make sure features are the same
        for orig_feat, new_feat in zip(orig_layer, new_layer):
            for fid in range(0, orig_layer_def.GetFieldCount()):
                assert orig_feat.GetField(fid) == new_feat.GetField(fid)

        # make sure extent the same
        assert_almost_equal(orig_layer.GetExtent(), new_layer.GetExtent(),
                            decimal=precision)

        # make sure the projection the same
        assert orig_layer.GetSpatialRef().ExportToProj4() == \
            new_layer.GetSpatialRef().ExportToProj4()

    else:
        with open(original) as file_o:
            contents_o = file_o.read()
            lines_o = contents_o.strip().split()

        with open(new) as file_n:
            contents_n = file_n.read()
            lines_n = contents_n.strip().split()

        for line_o, line_n in zip(lines_o, lines_n):
            try:
                val_o = [float(line_o)]
                val_n = [float(line_n)]
                assert_almost_equal(val_o, val_n, decimal=precision)
            except ValueError:
                assert lines_o == lines_n


class TestDirectories(object):
    input = os.path.join(SCRIPT_DIR, 'input')
    compare = os.path.join(SCRIPT_DIR, 'compare')
    write = os.path.join(SCRIPT_DIR, 'output')

    def clean(self):
        """
        Clean out test directory
        """
        os.chdir(self.write)

        # Clear out directory
        file_list = os.listdir(self.write)

        for afile in file_list:
            if not afile.endswith('.gitignore'):
                path = os.path.join(self.write, afile)
                if os.path.isdir(path):
                    rmtree(path)
                else:
                    os.remove(path)


@pytest.fixture(scope="module")
def tgrid(request):
    _td = TestDirectories()
    _td.clean()

    yield _td

    _td.clean()
