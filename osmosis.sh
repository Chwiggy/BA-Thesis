wget https://github.com/openstreetmap/osmosis/releases/download/0.49.2/osmosis-0.49.2.tar
mkdir osmosis
mv osmosis-latest.tgz osmosis
cd osmosis
tar xvfz osmosis-latest.tgz
rm osmosis-latest.tgz
chmod a+x bin/osmosis
bin/osmosis