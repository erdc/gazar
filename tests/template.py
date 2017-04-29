# -*- coding: utf-8 -*-
#
#  template.py
#  sloot
#
#  Author : Alan D Snow, 2017.
#  License: BSD 3-Clause

import itertools
from netCDF4 import Dataset
from numpy import array
from numpy.testing import assert_almost_equal
import os
from osgeo import gdal
from shutil import rmtree
import unittest

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))


class TestGridTemplate(unittest.TestCase):
    # Define workspace
    inputDirectory = os.path.join(SCRIPT_DIR, 'input')
    compareDirectory = os.path.join(SCRIPT_DIR, 'compare')
    writeDirectory = os.path.join(SCRIPT_DIR, 'output')

    def _compare_files(self, original, new, raster=False, precision=7):
        '''
        Compare the contents of two files
        '''
        if raster:
            dsO = gdal.Open(original)
            dsN = gdal.Open(new)

            # compare data
            rO = array(dsO.ReadAsArray())
            rN = array(dsN.ReadAsArray())
            assert_almost_equal(rO, rN, decimal=precision)

            # compare geotransform
            assert_almost_equal(dsO.GetGeoTransform(), dsN.GetGeoTransform(),
                                decimal=10)

            # compare band counts
            assert dsO.RasterCount == dsN.RasterCount
            # compare nodata
            for band_id in range(1, dsO.RasterCount+1):
                assert (dsO.GetRasterBand(band_id).GetNoDataValue()
                        == dsN.GetRasterBand(band_id).GetNoDataValue())

        else:
            with open(original) as fileO:
                contentsO = fileO.read()
                linesO = contentsO.strip().split()

            with open(new) as fileN:
                contentsN = fileN.read()
                linesN = contentsN.strip().split()

            for lineO, lineN in zip(linesO, linesN):
                try:
                    valO = float(lineO)
                    valN = float(lineN)
                    assert_almost_equal(valO, valN)
                except ValueError:
                    self.assertEqual(linesO, linesN)

    def _compare_directories(self, dir1, dir2, ignore_file=None, raster=False, precision=7):
        '''
        Compare the contents of the files of two directories
        '''

        for afile in os.listdir(dir2):
            if not os.path.basename(afile).startswith(".")\
               and not afile == ignore_file:

                # Compare files with same name
                try:
                    self._compare_files(os.path.join(dir1, afile),
                                        os.path.join(dir2, afile),
                                        raster=raster,
                                        precision=precision)
                except AssertionError:
                    print(os.path.join(dir1, afile))
                    print(os.path.join(dir2, afile))
                    raise

    def _list_compare(self, listone, listtwo):
        for one, two in itertools.izip(listone, listtwo):
            self.assertEqual(one, two)

    def _before_teardown(self):
        '''
        Method to execute at beginning of tearDown
        '''
        return

    def tearDown(self):
        '''
        Method to cleanup after tests
        '''
        self._before_teardown()

        os.chdir(SCRIPT_DIR)

        # Clear out directory
        fileList = os.listdir(self.writeDirectory)

        for afile in fileList:
            if not afile.endswith('.gitignore'):
                path = os.path.join(self.writeDirectory, afile)
                if os.path.isdir(path):
                    rmtree(path)
                else:
                    os.remove(path)
