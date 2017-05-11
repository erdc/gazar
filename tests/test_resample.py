import os

from .conftest import compare_files

from gazar.grid import resample_grid


def test_resample_grid(tgrid):
    """
    Test resampling grid
    """
    new_mask_grid = os.path.join(tgrid.input, 'v_mask.tif')
    era_grid = os.path.join(tgrid.input, 'era_raw.tif')
    resampled_grid = os.path.join(tgrid.write, 'resampled.tif')
    resample_grid(original_grid=era_grid,
                  match_grid=new_mask_grid,
                  to_file=resampled_grid)

    compare_resampled_grid = os.path.join(tgrid.write, 'resampled.tif')
    compare_files(resampled_grid, compare_resampled_grid, raster=True)


def test_resample_grid_as_gdal(tgrid):
    """
    Test resampling grid
    """
    new_mask_grid = os.path.join(tgrid.input, 'v_mask.tif')
    era_grid = os.path.join(tgrid.input, 'era_raw.tif')
    resampled_grid = os.path.join(tgrid.write, 'resampled.tif')
    rs_gdal_grid = resample_grid(original_grid=era_grid,
                                 match_grid=new_mask_grid,
                                 as_gdal_grid=True)
    rs_gdal_grid.to_tif(resampled_grid)

    compare_resampled_grid = os.path.join(tgrid.write, 'resampled.tif')
    compare_files(resampled_grid, compare_resampled_grid, raster=True)
