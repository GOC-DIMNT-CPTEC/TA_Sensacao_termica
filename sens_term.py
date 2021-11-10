#!/usr/bin/env python
# coding: utf-8

from siphon.catalog import TDSCatalog
from datetime import datetime, timedelta
from xarray.backends import NetCDF4DataStore
import numpy as np
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cf
import matplotlib.pyplot as plt
import cartopy.io.shapereader as shpreader
import cartopy.feature as cfeature


gfs = TDSCatalog('http://thredds.ucar.edu/thredds/catalog/grib/NCEP/GFS/Global_0p25deg/catalog.xml?dataset=grib/NCEP/GFS/Global_0p25deg/Best')


## dataset de interesse:
best_ds = list(gfs.datasets.values())[0]
ncss = best_ds.subset()
query = ncss.query()
dtime = datetime.utcnow() 
query.lonlat_box(north=-19.43,south=-36.14,east=320,west=300).time(dtime)
query.accept('netcdf4')
query.variables('Temperature_surface','Relative_humidity_height_above_ground','u-component_of_wind_height_above_ground','v-component_of_wind_height_above_ground') # ou todas 'all'
data = ncss.get_data(query)

#Carregando os dados
data = xr.open_dataset(NetCDF4DataStore(data))

#selecionando váriaveis 
t = data['Temperature_surface'][:]
ur = data['Relative_humidity_height_above_ground'][:]
u = data['u-component_of_wind_height_above_ground'][:]
v = data['v-component_of_wind_height_above_ground'][:]

time=t.time.values
time=str(time)

#Removendo as dimensões

ur=ur.squeeze(dim='time', drop=False, axis=None)
ur=ur.squeeze(dim='height_above_ground', drop=False, axis=None)

t=t.squeeze(dim='time', drop=False, axis=None)
t = t-273.15

u=u.squeeze(dim='time', drop=False, axis=None)
v=v.squeeze(dim='time', drop=False, axis=None)

u10 = u[0,:,:]
v10 = v[0,:,:]
t_2m = t.values
u_2m = ur.values

#Selecionando lat e lon
x = t.lon
y = t.lat

#Função para pressão de vapor 
def e(UR,T):
    e = (UR/100)*6.105*np.exp((17.27*T)/(237.7+T))
    return e
#Função para calcular vento
def ven(U,V):
    ve = np.hypot(U,V)
    return ve
#Função para calcular temperatura aparente
def te(T,e,ve):
    te = T+0.33*e-0.70*ve-4.00
    return te

#Calcular o vento usando função ---- ok 
ven_s=ven(u10,v10)
#Calcular a pressão de vapor usando função
e = e(ur,t)
#Calcular temperatura aparente
temp_ap = te(t,e,ven_s)

br = shpreader.Reader('estados.shp')
mun = list(br.geometries())

#Visualização dos dados
fig=plt.figure(figsize=(9,8), dpi= 80)
ax = plt.axes(projection=ccrs.PlateCarree())
mun_data = cfeature.ShapelyFeature(mun, ccrs.PlateCarree())
da=ax.contourf(x, y,temp_ap, 100, cmap='jet') 
ax.add_feature(mun_data, edgecolor='black',alpha=0.2,linestyle='-')
plt.title('Sensação térmica---'+time)
fig.colorbar(da,orientation="vertical",extendrect=True,fraction=0.030, pad=0.01,spacing='proportional')
ax.coastlines()
plt.show()

