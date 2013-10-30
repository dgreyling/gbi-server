GeoBox-Server
=============

This is a server for the GeoBox infrastructure (GBI). The GBI allows you to download, synchronize and use raster and vector data on remote/offline clients.

GeoBox-Server is a web application that allows users to log in, view available WMTS services and to edit vector data via WFS.

It implements all APIs for the GeoBox-Client (context documents, tile authentication, CouchDB replication and access logging).

GeoBox-Client is written in Python, Apache 2.0 licensed and it builds on a number of other open source packages, including: CouchDB, GeoCouch, MapProxy, libproj, GDAL/OGR, GEOS, ...

