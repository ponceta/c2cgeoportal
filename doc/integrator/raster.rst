.. _integrator_raster:

Digital Elevation Tools
=======================

c2cgeoportal applications include web services for getting
`DEM <http://en.wikipedia.org/wiki/Digital_elevation_model>`_ information.
The ``raster`` web service allows getting information for points.
The ``profile`` web service allows getting information for lines.

To configure these web services you need to set the ``raster`` variable in the
application config (``vars.yaml``).  For example:

.. code:: yaml

    raster:
        cache_size: 21
        mns:
            file: /var/sig/altimetrie/mns.vrt
            type: gdal
            round: 1
        mnt:
            file: /var/sig/altimetrie/mnt.vrt
            type: gdal
            round: 1

``raster`` is a list of "DEM layers". There are only two entries in this example, but there could be more.

``cache_size`` is the number of DEM files to keep in cache. Default is 10.

``file`` provides the path to the shape index that references the raster files.
The raster files should be in the Binary Terrain (BT/VTP .bt 1.3) format.
One may use GDAL/OGR to convert data to such a format.

``type`` ``shp_index`` (default) for Mapserver shape index, or ``gdal`` for all supported GDAL sources.
We recommand to use a `vrt <https://www.gdal.org/gdal_vrttut.html>`_ file built with
`gdalbuildvrt <https://www.gdal.org/gdalbuildvrt.html>`_.

``round`` specifigdalbuildvrtes how the result values should be rounded.
For instance '1': round to the unit, '0.01': round to the hundredth, etc.
