set -ex

GDALOPTS="  --with-ogr \
            --with-geos \
            --with-expat \
            --with-python \
            --without-libtool \
            --with-libz=internal \
            --with-libtiff=internal \
            --with-geotiff=internal \
            --without-gif \
            --without-pg \
            --without-grass \
            --without-libgrass \
            --without-cfitsio \
            --without-pcraster \
            --without-netcdf \
            --without-png \
            --with-jpeg=internal \
            --without-gif \
            --without-ogdi \
            --without-fme \
            --without-hdf4 \
            --without-hdf5 \
            --without-jasper \
            --without-ecw \
            --without-kakadu \
            --without-mrsid \
            --without-jp2mrsid \
            --without-bsb \
            --without-grib \
            --without-mysql \
            --without-ingres \
            --without-xerces \
            --without-odbc \
            --without-curl \
            --without-sqlite3 \
            --without-dwgdirect \
            --without-idb \
            --without-sde \
            --without-perl \
            --without-php \
            --without-ruby"

# Create build dir if not exists
if [ ! -d "$GDALBUILD" ]; then
  mkdir $GDALBUILD;
fi

if [ ! -d "$GDALINST" ]; then
  mkdir $GDALINST;
fi

ls -l $GDALINST

if [ ! -d $GDALINST/gdal-2.0.0 ]; then
  cd $GDALBUILD
  wget http://download.osgeo.org/gdal/2.0.0/gdal-2.0.0.tar.gz
  tar -xzf gdal-2.0.0.tar.gz
  cd gdal-2.0.0
  ./configure --prefix=$GDALINST/gdal-2.0.1 $GDALOPTS
  make -s -j 2
  make install
fi

cd