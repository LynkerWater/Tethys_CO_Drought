from django.shortcuts import render, reverse, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import MapView, Button, ToggleSwitch, TextInput, DatePicker, SelectInput, DataTableView, MVDraw, MVLegendClass, MVLegendGeoServerImageClass, MVLegendImageClass, MVView, MVLayer, EMView, EMLayer, ESRIMap 
import datetime
import json
from .model import add_new_dam, get_all_dams

## calculate date info necessary for some mapserver data requests
today = datetime.datetime.now()
yearnow = today.year
monthnow = today.month
prevmonth = (today.replace(day=1) - datetime.timedelta(days=1)).month
if len(str(prevmonth)) == 1:
    prevmonth = '0' + str(prevmonth)
if len(str(monthnow)) == 1:
    monthnow = '0' + str(monthnow)
        
############################## Drought Map Main ############################################
@login_required()
def drought_map(request):
    """
    Controller for the app drought map page.
    """
           
    view_center = [-105.2, 39.0]
    view_options = MVView(
        projection='EPSG:4326',
        center=view_center,
        zoom=7.0,
        maxZoom=12,
        minZoom=5
    )

    # TIGER state/county mapserver
    tiger_boundaries = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer'},
        legend_title='States & Counties',
        layer_options={'visible':True,'opacity':0.8},
        legend_extent=[-112, 36.3, -98.5, 41.66])    
    
    ##### WMS Layers - Ryan
    usdm_legend = MVLegendImageClass(value='Drought Category',
                             image_url='http://ndmc-001.unl.edu:8080/cgi-bin/mapserv.exe?map=/ms4w/apps/usdm/service/usdm_current_wms.map&version=1.3.0&service=WMS&request=GetLegendGraphic&sld_version=1.1.0&layer=usdm_current&format=image/png&STYLE=default')
    usdm_current = MVLayer(
            source='ImageWMS',
            options={'url': 'http://ndmc-001.unl.edu:8080/cgi-bin/mapserv.exe?',
                     'params': {'LAYERS':'usdm_current','FORMAT':'image/png','VERSION':'1.1.1','STYLES':'default','MAP':'/ms4w/apps/usdm/service/usdm_current_wms.map'}},
            layer_options={'visible':True,'opacity':0.25},
            legend_title='USDM',
            legend_classes=[usdm_legend],
            legend_extent=[-126, 24.5, -66.2, 49])
            
    usdm_kml = MVLayer(
        source='KML',
        options={'url': '/static/tethys_gizmos/data/usdm_current.kml'},
        layer_options={'visible':True,'opacity':0.5},
        legend_title='USDM',
        legend_classes=[usdm_legend],
        legend_extent=[-126, 24.5, -66.2, 49])
    
    ww_legend = MVLegendImageClass(value='Current Streamflow',
                             image_url='https://edcintl.cr.usgs.gov/geoserver/qdriwaterwatchshapefile/ows?service=WMS&request=GetLegendGraphic&format=image%2Fpng&width=20&height=20&layer=water_watch_today')   
    water_watch = MVLayer(
            source='ImageWMS',
            options={'url': 'https://edcintl.cr.usgs.gov/geoserver/qdriwaterwatchshapefile/wms?',
                     'params': {'LAYERS': 'water_watch_today'},
                   'serverType': 'geoserver'},
            layer_options={'visible':False,'opacity':0.5},
            legend_title='USGS Water Watch',
            legend_classes=[ww_legend],
            legend_extent=[-126, 24.5, -66.2, 49])
   
    # USGS Rest server for HUC watersheds        
    watersheds = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer'},
        legend_title='HUC Watersheds',
        layer_options={'visible':False,'opacity':0.4},
        legend_extent=[-112, 36.3, -98.5, 41.66])

    # Define SWSI KML Layer
    swsi_legend = MVLegendImageClass(value='SWSI',
                             image_url='/static/tethys_gizmos/data/swsi_legend.PNG')
    SWSI_kml = MVLayer(
        source='KML',
        options={'url': '/static/tethys_gizmos/data/SWSI_2018Apr.kml'},
        legend_title='SWSI',
        layer_options={'visible':False,'opacity':0.7},
        feature_selection=True,
        legend_classes=[swsi_legend],
        legend_extent=[-110, 36, -101.5, 41.6])
    
    # NOAA Rest server for NWM streamflow      
    nwm_stream = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://mapservice.nohrsc.noaa.gov/arcgis/rest/services/national_water_model/NWM_Stream_Analysis/MapServer',
                'params': {'LAYERS': 'show:1,2,3,4,5,12'}},
        legend_title='NWM Streamflow',
        layer_options={'visible':False,'opacity':1.0},
        legend_extent=[-112, 36.3, -98.5, 41.66])
    nwm_stream_anom = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://mapservice.nohrsc.noaa.gov/arcgis/rest/services/national_water_model/NWM_Stream_Analysis/MapServer',
                'params': {'LAYERS': 'show:7,8,9,10,11,12'}},
        legend_title='NWM Flow Anamaly',
        layer_options={'visible':True,'opacity':1.0},
        legend_extent=[-112, 36.3, -98.5, 41.66])
        
    # NOAA NOHRSC snow products
    snodas_swe = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Observations/NOHRSC_Snow_Analysis/MapServer',
                'params': {'LAYERS': 'show:7'}},
        legend_title='SNODAS Model SWE (in)',
        layer_options={'visible':False,'opacity':0.7},
        legend_extent=[-112, 36.3, -98.5, 41.66])

    # NOAA Rest server for NWM soil moisture
    nwm_soil_legend = MVLegendGeoServerImageClass(value='test', style='green', layer='rivers',
                         geoserver_url='https://mapservice.nohrsc.noaa.gov/arcgis/rest/services/national_water_model/NWM_Land_Analysis/MapServer/legend?f=pjson')   
    nwm_soil = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://mapservice.nohrsc.noaa.gov/arcgis/rest/services/national_water_model/NWM_Land_Analysis/MapServer'},
        legend_title='NWM Soil Moisture',
        layer_options={'visible':False,'opacity':0.5},
        legend_classes=[nwm_soil_legend],
        legend_extent=[-112, 36.3, -98.5, 41.66])
        
    # Define GeoJSON layer
    with open(r'C:\Users\Lynker1\tethys\src\tethys_gizmos\static\tethys_gizmos\data\cartodb-query.geojson') as f:
        data = json.load(f)
        
    coco_geojson = MVLayer(
        source='GeoJSON',
        options=data,
        legend_title='Condition Monitor',
        legend_extent=[-112, 36.3, -98.5, 41.66],
        feature_selection=True,
        legend_classes=[MVLegendClass('point', 'point', fill='#696969')],
        layer_options={'style': {'image': {'circle': {'radius': 5,'points':3,'fill': {'color':  '#696969'},'stroke': {'color': '#ffffff', 'width': 1},}}}})
        #layer_options={'style': 'flickrStyle'})
        
#    SWSI_json = MVLayer(
#        source='GeoJSON',
#        options={'url': '/static/tethys_gizmos/data/SWSI_2017Dec.geojson', 'featureProjection': 'EPSG:3857'},
#        legend_title='SWSI',
#        layer_options={'visible':True,'opacity':0.4},
#        feature_selection=True,
#        legend_extent=[-110, 36, -101.5, 41.6])  
                
    # Define map view options
    drought_map_view_options = MapView(
            height='630px',
            width='100%',
            controls=['ZoomSlider', 'Rotate', 'ScaleLine', 'FullScreen',
                      {'MousePosition': {'projection': 'EPSG:4326'}},
                      {'ZoomToExtent': {'projection': 'EPSG:4326', 'extent': [-130, 22, -65, 54]}}],
            layers=[tiger_boundaries,nwm_stream,nwm_stream_anom,nwm_soil,snodas_swe,water_watch,SWSI_kml,coco_geojson,usdm_current,watersheds],
            view=view_options,
            basemap='OpenStreetMap',
            legend=True
        )

    context = {
        'drought_map_view_options':drought_map_view_options,
    }

    return render(request, 'co_drought/drought.html', context)
##################### End Drought Main Map #############################################
##################### Start Drought Map - NWM Forecast #############################################
@login_required()
def drought_map_nwmforecast(request):
    """
    Controller for the app drought map page.
    """
           
    view_center = [-105.2, 39.0]
    view_options = MVView(
        projection='EPSG:4326',
        center=view_center,
        zoom=7.0,
        maxZoom=12,
        minZoom=5
    )

    # TIGER state/county mapserver
    tiger_boundaries = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer'},
        legend_title='States & Counties',
        layer_options={'visible':True,'opacity':0.8},
        legend_extent=[-112, 36.3, -98.5, 41.66])    
    
    # USGS Rest server for HUC watersheds        
    watersheds = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer'},
        legend_title='HUC Watersheds',
        layer_options={'visible':False,'opacity':0.4},
        legend_extent=[-112, 36.3, -98.5, 41.66])

    # NOAA Rest server for NWM streamflow      
    nwm_stream = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://mapservice.nohrsc.noaa.gov/arcgis/rest/services/national_water_model/NWM_Stream_Analysis/MapServer',
                'params': {'LAYERS': 'show:1,2,3,4,5,12'}},
        legend_title='NWM Streamflow',
        layer_options={'visible':False,'opacity':1.0},
        legend_classes=[
            MVLegendClass('line', '> 1.25M', stroke='rgba(75,0,115,0.9)'),
            MVLegendClass('line', '500K - 1.25M', stroke='rgba(176,28,232,0.9)'),
            MVLegendClass('line', '100K - 500K', stroke='rgba(246,82,213,0.9)'),
            MVLegendClass('line', '50K - 100K', stroke='rgba(254,7,7,0.9)'),
            MVLegendClass('line', '25K - 50K', stroke='rgba(252,138,23,0.9)'),
            MVLegendClass('line', '10K - 25K', stroke='rgba(45,108,183,0.9)'),
            MVLegendClass('line', '5K - 10K', stroke='rgba(27,127,254,0.9)'),
            MVLegendClass('line', '2.5K - 5K', stroke='rgba(79,169,195,0.9)'),
            MVLegendClass('line', '250 - 2.5K', stroke='rgba(122,219,250,0.9)'),
            MVLegendClass('line', '0 - 250', stroke='rgba(206,222,251,0.9)'),
            MVLegendClass('line', 'No Data', stroke='rgba(195,199,201,0.9)')],
        legend_extent=[-112, 36.3, -98.5, 41.66])
    nwm_stream_anom = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://mapservice.nohrsc.noaa.gov/arcgis/rest/services/national_water_model/NWM_Stream_Analysis/MapServer',
                'params': {'LAYERS': 'show:7,8,9,10,11,12'}},
        legend_title='NWM Flow Anamaly',
        layer_options={'visible':True,'opacity':1.0},
        legend_classes=[
            MVLegendClass('line', 'High', stroke='rgba(176,28,232,0.9)'),
            MVLegendClass('line', '', stroke='rgba(61,46,231,0.9)'),
            MVLegendClass('line', '', stroke='rgba(52,231,181,0.9)'),
            MVLegendClass('line', 'Moderate', stroke='rgba(102,218,148,0.9)'),
            MVLegendClass('line', '', stroke='rgba(241,156,77,0.9)'),
            MVLegendClass('line', '', stroke='rgba(175,62,44,0.9)'),
            MVLegendClass('line', 'Low', stroke='rgba(241,42,90,0.9)'),
            MVLegendClass('line', 'No Data', stroke='rgba(195,199,201,0.9)')],
        legend_extent=[-112, 36.3, -98.5, 41.66])

    # NOAA Rest server for NWM soil moisture
    nwm_soil_legend = MVLegendGeoServerImageClass(value='test', style='green', layer='NWM_Land_Analysis',
                         geoserver_url='https://mapservice.nohrsc.noaa.gov/arcgis/rest/services/national_water_model/NWM_Land_Analysis/MapServer/legend?f=pjson')   
    nwm_soil = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://mapservice.nohrsc.noaa.gov/arcgis/rest/services/national_water_model/NWM_Land_Analysis/MapServer'},
        legend_title='NWM Soil Moisture (%)',
        layer_options={'visible':True,'opacity':0.5},
        legend_classes=[
            MVLegendClass('polygon', '0.95 - 1.0', fill='rgba(49,56,148,0.5)'),
            MVLegendClass('polygon', '0.85 - 0.95', fill='rgba(97,108,181,0.5)'),
            MVLegendClass('polygon', '0.75 - 0.85', fill='rgba(145,180,216,0.5)'),
            MVLegendClass('polygon', '0.65 - 0.75', fill='rgba(189,225,225,0.5)'),
            MVLegendClass('polygon', '0.55 - 0.65', fill='rgba(223,240,209,0.5)'),
            MVLegendClass('polygon', '0.45 - 0.55', fill='rgba(225,255,191,0.5)'),
            MVLegendClass('polygon', '0.35 - 0.45', fill='rgba(255,222,150,0.5)'),
            MVLegendClass('polygon', '0.25 - 0.35', fill='rgba(255,188,112,0.5)'),
            MVLegendClass('polygon', '0.15 - 0.25', fill='rgba(235,141,81,0.5)'),
            MVLegendClass('polygon', '0.05 - 0.15', fill='rgba(201,77,58,0.5)'),
            MVLegendClass('polygon', '0 - 0.05', fill='rgba(166,0,38,0.5)')],
        legend_extent=[-112, 36.3, -98.5, 41.66])
        

    # Define map view options
    drought_nwmfx_map_view_options = MapView(
            height='630px',
            width='100%',
            controls=['ZoomSlider', 'Rotate', 'ScaleLine', 'FullScreen',
                      {'MousePosition': {'projection': 'EPSG:4326'}},
                      {'ZoomToExtent': {'projection': 'EPSG:4326', 'extent': [-112, 36.3, -98.5, 41.66]}}],
            layers=[tiger_boundaries,nwm_stream_anom,nwm_stream,nwm_soil,watersheds],
            view=view_options,
            basemap='OpenStreetMap',
            legend=True
        )
    
    toggle_switch = ToggleSwitch(display_text='Defualt Toggle',
                             name='toggle1')

    context = {
        'drought_nwmfx_map_view_options':drought_nwmfx_map_view_options,
        'toggle_switch': toggle_switch,
    }

    return render(request, 'co_drought/drought_nwmfx.html', context)
########################### End drought_nwmfx map #######################################
######################### Start Drought Map - Outlook ######################################
@login_required()
def drought_map_outlook(request):
    """
    Controller for the app drought map page.
    """
           
    view_center = [-105.2, 39.0]
    view_options = MVView(
        projection='EPSG:4326',
        center=view_center,
        zoom=7.0,
        maxZoom=12,
        minZoom=5
    )

    # TIGER state/county mapserver
    tiger_boundaries = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer'},
        legend_title='States & Counties',
        layer_options={'visible':True,'opacity':0.8},
        legend_extent=[-112, 36.3, -98.5, 41.66])    
    
    # USGS Rest server for HUC watersheds        
    watersheds = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer'},
        legend_title='HUC Watersheds',
        layer_options={'visible':False,'opacity':0.4},
        legend_extent=[-112, 36.3, -98.5, 41.66])
        
    ww_legend = MVLegendImageClass(value='Current Streamflow',
                             image_url='https://edcintl.cr.usgs.gov/geoserver/qdriwaterwatchshapefile/ows?service=WMS&request=GetLegendGraphic&format=image%2Fpng&width=20&height=20&layer=water_watch_today')   
    water_watch = MVLayer(
            source='ImageWMS',
            options={'url': 'https://edcintl.cr.usgs.gov/geoserver/qdriwaterwatchshapefile/wms?',
                     'params': {'LAYERS': 'water_watch_today'},
                   'serverType': 'geoserver'},
            layer_options={'visible':False,'opacity':0.5},
            legend_title='USGS Water Watch',
            legend_classes=[ww_legend],
            legend_extent=[-126, 24.5, -66.2, 49])
        
    # NCEP Climate Outlook MapServer
    ncep_month_outlook = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Climate_Outlooks/cpc_drought_outlk/MapServer',
                'params': {'LAYERS': 'show:0'}},
        legend_title='NCEP Monthly Drought Outlook',
        layer_options={'visible':True,'opacity':0.7},
        legend_classes=[
            MVLegendClass('polygon', 'Persistence', fill='rgba(155,113,73,0.7)'),
            MVLegendClass('polygon', 'Improvement', fill='rgba(226,213,192,0.7)'),
            MVLegendClass('polygon', 'Removal', fill='rgba(178,173,105,0.7)'),
            MVLegendClass('polygon', 'Development', fill='rgba(255,222,100,0.7)')],
        legend_extent=[-112, 36.3, -98.5, 41.66])
    ncep_seas_outlook = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Climate_Outlooks/cpc_drought_outlk/MapServer',
                'params': {'LAYERS': 'show:1'}},
        legend_title='NCEP Seasonal Drought Outlook',
        layer_options={'visible':False,'opacity':0.7},
        legend_classes=[
            MVLegendClass('polygon', 'Persistence', fill='rgba(155,113,73,0.7)'),
            MVLegendClass('polygon', 'Improvement', fill='rgba(226,213,192,0.7)'),
            MVLegendClass('polygon', 'Removal', fill='rgba(178,173,105,0.7)'),
            MVLegendClass('polygon', 'Development', fill='rgba(255,222,100,0.7)')],
        legend_extent=[-112, 36.3, -98.5, 41.66])
        
    # CPC Wildfire/Drought forecast
    cpc_37_outlook = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Climate_Outlooks/cpc_weather_hazards/MapServer',
                'params': {'LAYERS': 'show:7'}},
        legend_title='CPC 3-7 Day WildFire/Drought',
        layer_options={'visible':False,'opacity':0.7},
        legend_classes=[
            MVLegendClass('polygon', 'Wildfire Risk', fill='rgba(130,130,130,0.7)'),
            MVLegendClass('polygon', 'Severe Drought', fill='rgba(207,181,151,0.7)')],
        legend_extent=[-112, 36.3, -98.5, 41.66])

    # NOAA WPC QPF forecast
    WPC_5day_QPF = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Forecasts_Guidance_Warnings/wpc_qpf/MapServer',
                'params': {'LAYERS': 'show:10'}},
        legend_title='WPC 5-day QPF',
        layer_options={'visible':True,'opacity':0.3},
        legend_extent=[-112, 36.3, -98.5, 41.66])

    # Define map view options
    drought_outlook_map_view_options = MapView(
            height='630px',
            width='100%',
            controls=['ZoomSlider', 'Rotate', 'ScaleLine', 'FullScreen',
                      {'MousePosition': {'projection': 'EPSG:4326'}},
                      {'ZoomToExtent': {'projection': 'EPSG:4326', 'extent': [-112, 36.3, -98.5, 41.66]}}],
            layers=[tiger_boundaries,water_watch,ncep_month_outlook,ncep_seas_outlook,WPC_5day_QPF,cpc_37_outlook,watersheds],
            view=view_options,
            basemap='OpenStreetMap',
            legend=True
        )

    context = {
        'drought_outlook_map_view_options':drought_outlook_map_view_options,
    }

    return render(request, 'co_drought/drought_outlook.html', context)
########################### End drought_outlook map #######################################
########################## Start drought_index Map#########################################
@login_required()
def drought_index_map(request):
    """
    Controller for the app drought map page.
    """
           
    view_center = [-105.2, 39.0]
    view_options = MVView(
        projection='EPSG:4326',
        center=view_center,
        zoom=7.0,
        maxZoom=12,
        minZoom=5
    )

    # TIGER state/county mapserver
    tiger_boundaries = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer'},
        legend_title='States & Counties',
        layer_options={'visible':True,'opacity':0.8},
        legend_extent=[-112, 36.3, -98.5, 41.66]) 

    # NCDC Climate Divisions
    climo_divs = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://gis.ncdc.noaa.gov/arcgis/rest/services/backgrounds/MapServer',
                 'params': {'LAYERS': 'show:1'}},
        legend_title='Climate Divisions',
        layer_options={'visible':False,'opacity':0.8},
        legend_extent=[-112, 36.3, -98.5, 41.66]) 
        
    # USGS Rest server for HUC watersheds        
    watersheds = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer'},
        legend_title='HUC Watersheds',
        layer_options={'visible':False,'opacity':0.4},
        legend_extent=[-112, 36.3, -98.5, 41.66])
    
    ##### WMS Layers - Ryan
    usdm_legend = MVLegendImageClass(value='Drought Category',
                             image_url='http://ndmc-001.unl.edu:8080/cgi-bin/mapserv.exe?map=/ms4w/apps/usdm/service/usdm_current_wms.map&version=1.3.0&service=WMS&request=GetLegendGraphic&sld_version=1.1.0&layer=usdm_current&format=image/png&STYLE=default')
    usdm_current = MVLayer(
            source='ImageWMS',
            options={'url': 'http://ndmc-001.unl.edu:8080/cgi-bin/mapserv.exe?',
                     'params': {'LAYERS':'usdm_current','FORMAT':'image/png','VERSION':'1.1.1','STYLES':'default','MAP':'/ms4w/apps/usdm/service/usdm_current_wms.map'}},
            layer_options={'opacity':0.3},
            legend_title='USDM',
            legend_classes=[usdm_legend],
            legend_extent=[-126, 24.5, -66.2, 49])
            
    usdm_kml = MVLayer(
        source='KML',
        options={'url': '/static/tethys_gizmos/data/usdm_current.kml'},
        layer_options={'visible':True,'opacity':0.5},
        legend_title='USDM',
        feature_selection=False,
        legend_classes=[usdm_legend],
        legend_extent=[-126, 24.5, -66.2, 49])
            
    # ESI Data from USDA
    esi_1 = MVLayer(
            source='ImageWMS',
            options={'url': 'https://hrsl.ba.ars.usda.gov/wms.esi.2012?',
                     'params': {'LAYERS': 'ESI_current_1month', 'VERSION':'1.1.3', 'CRS':'EPSG:4326'}},
            layer_options={'visible':False,'opacity':0.5},
            legend_title='ESI - 1 month',
            legend_extent=[-126, 24.5, -66.2, 49])

    # Define SWSI KML Layer
    swsi_legend = MVLegendImageClass(value='',
                             image_url='/static/tethys_gizmos/data/swsi_legend.PNG')
    SWSI_kml = MVLayer(
        source='KML',
        options={'url': '/static/tethys_gizmos/data/SWSI_2018Apr.kml'},
        legend_title='SWSI',
        layer_options={'visible':True,'opacity':0.7},
        feature_selection=True,
        legend_classes=[swsi_legend],
        legend_extent=[-110, 36, -101.5, 41.6])
        
    # NCDC/NIDIS precip index
    ncdc_pindex = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://gis.ncdc.noaa.gov/arcgis/rest/services/cdo/indices/MapServer',
                'params': {'LAYERS': 'show:1'}},
        legend_title='Precipitation Index',
        layer_options={'visible':False,'opacity':0.7},
        legend_extent=[-112, 36.3, -98.5, 41.66])
        
    # NCDC/NIDIS palmer drought severity index
    # NOTE: MONTH LOOKUP IS HARDCODED RIGHT NOW
    ncdc_pdsi = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://gis.ncdc.noaa.gov/arcgis/rest/services/cdo/indices/MapServer',
                'params': {'LAYERS': 'show:2','layerDefs':'{"2":"YEARMONTH='+str(yearnow)+str(prevmonth)+'"}'}},
        legend_title='PDSI',
        layer_options={'visible':False,'opacity':0.7},
        legend_extent=[-112, 36.3, -98.5, 41.66])
        
    # NCDC/NIDIS palmer drought severity index
    # NOTE: MONTH LOOKUP IS HARDCODED RIGHT NOW
    ncdc_palmz = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://gis.ncdc.noaa.gov/arcgis/rest/services/cdo/indices/MapServer',
                'params': {'LAYERS': 'show:8','layerDefs':'{"8":"YEARMONTH='+str(yearnow)+str(prevmonth)+'"}'}},
        legend_title='Palmer Z',
        layer_options={'visible':False,'opacity':0.7},
        legend_extent=[-112, 36.3, -98.5, 41.66])
        
    # NCDC/NIDIS standardized precip index
    ncdc_spi_1 = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://gis.ncdc.noaa.gov/arcgis/rest/services/cdo/indices/MapServer',
                'params': {'LAYERS': 'show:11','layerDefs':'{"11":"YEARMONTH='+str(yearnow)+str(prevmonth)+'"}'}},
        legend_title='SPI (1-month)',
        layer_options={'visible':False,'opacity':0.6},
        legend_extent=[-112, 36.3, -98.5, 41.66])
        
    # NCDC/NIDIS standardized precip index
    ncdc_spi_3 = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://gis.ncdc.noaa.gov/arcgis/rest/services/cdo/indices/MapServer',
                'params': {'LAYERS': 'show:13','layerDefs':'{"13":"YEARMONTH='+str(yearnow)+str(prevmonth)+'"}'}},
        legend_title='SPI (3-month)',
        layer_options={'visible':False,'opacity':0.6},
        legend_extent=[-112, 36.3, -98.5, 41.66])
        
    # NCDC/NIDIS standardized precip index
    ncdc_spi_6 = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://gis.ncdc.noaa.gov/arcgis/rest/services/cdo/indices/MapServer',
                'params': {'LAYERS': 'show:14','layerDefs':'{"14":"YEARMONTH='+str(yearnow)+str(prevmonth)+'"}'}},
        legend_title='SPI (6-month)',
        layer_options={'visible':False,'opacity':0.6},
        legend_extent=[-112, 36.3, -98.5, 41.66])
    
        
    # Define map view options
    drought_index_map_view_options = MapView(
            height='100%',
            width='100%',
            controls=['ZoomSlider', 'Rotate', 'ScaleLine', 'FullScreen',
                      {'MousePosition': {'projection': 'EPSG:4326'}},
                      {'ZoomToExtent': {'projection': 'EPSG:4326', 'extent': [-112, 36.3, -98.5, 41.66]}}],
            layers=[tiger_boundaries,climo_divs,usdm_current,ncdc_pdsi,ncdc_palmz,ncdc_spi_1,ncdc_spi_3,ncdc_spi_6,SWSI_kml,watersheds],
            view=view_options,
            basemap='OpenStreetMap',
            legend=True
        )

    context = {
        'drought_index_map_view_options':drought_index_map_view_options,
    }

    return render(request, 'co_drought/drought_index.html', context)
########################### End drought_index map #######################################
########################## Start drought_veg_index Map#########################################
@login_required()
def drought_veg_index_map(request):
    """
    Controller for the app drought map page.
    """
           
    view_center = [-105.2, 39.0]
    view_options = MVView(
        projection='EPSG:4326',
        center=view_center,
        zoom=7.0,
        maxZoom=12,
        minZoom=5
    )

    # TIGER state/county mapserver
    tiger_boundaries = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer'},
        legend_title='States & Counties',
        layer_options={'visible':True,'opacity':0.8},
        legend_extent=[-112, 36.3, -98.5, 41.66]) 

    # NCDC Climate Divisions
    climo_divs = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://gis.ncdc.noaa.gov/arcgis/rest/services/backgrounds/MapServer',
                 'params': {'LAYERS': 'show:1'}},
        legend_title='Climate Divisions',
        layer_options={'visible':False,'opacity':0.8},
        legend_extent=[-112, 36.3, -98.5, 41.66]) 
        
    # USGS Rest server for HUC watersheds        
    watersheds = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer'},
        legend_title='HUC Watersheds',
        layer_options={'visible':False,'opacity':0.4},
        legend_extent=[-112, 36.3, -98.5, 41.66])
    
    ##### WMS Layers - Ryan
    vdri_legend = MVLegendImageClass(value='VegDRI Cat',
                     image_url='https://vegdri.cr.usgs.gov/wms.php?service=WMS&request=GetLegendGraphic&format=image%2Fpng&width=20&height=20&LAYER=DROUGHT_VDRI_EMODIS_1')   
    vegdri = MVLayer(
            source='ImageWMS',
            options={'url': 'https://vegdri.cr.usgs.gov/wms.php?',
                     'params': {'LAYERS': 'DROUGHT_VDRI_EMODIS_1'},
                   'serverType': 'geoserver'},
            layer_options={'visible':True,'opacity':0.5},
            legend_title='VegDRI',
            legend_classes=[vdri_legend],
            legend_extent=[-126, 24.5, -66.2, 49])
            # historical layers https://edcintl.cr.usgs.gov/geoserver/qdrivegdriemodis/wms?', 'params': {'LAYERS': 'qdrivegdriemodis_pd_1-sevenday-53-2017_mm_data'

    qdri_legend = MVLegendImageClass(value='QuickDRI Cat',
                     image_url='https://vegdri.cr.usgs.gov/wms.php?service=WMS&request=GetLegendGraphic&format=image%2Fpng&width=20&height=20&LAYER=DROUGHT_QDRI_EMODIS_1')   
    quickdri = MVLayer(
            source='ImageWMS',
            options={'url': 'https://vegdri.cr.usgs.gov/wms.php?',
                     'params': {'LAYERS': 'DROUGHT_QDRI_EMODIS_1'},
                   'serverType': 'geoserver'},
            layer_options={'visible':False,'opacity':0.5},
            legend_title='QuickDRI',
            legend_classes=[qdri_legend],
            legend_extent=[-126, 24.5, -66.2, 49])
            # historical layers: https://edcintl.cr.usgs.gov/geoserver/qdriquickdriraster/wms?', 'params': {'LAYERS': 'qdriquickdriraster_pd_1-sevenday-53-2017_mm_data'   
    
    # Land Cover REST layer
    #https://www.mrlc.gov/arcgis/rest/services/LandCover/USGS_EROS_LandCover_NLCD/MapServer
    NLCD = MVLayer(
            source='TileArcGISRest',
            options={'url': 'https://www.mrlc.gov/arcgis/rest/services/LandCover/USGS_EROS_LandCover_NLCD/MapServer',
                     'params': {'LAYERS': 'show6'}},
            layer_options={'visible':False,'opacity':0.5},
            legend_title='NLCD',
            legend_extent=[-126, 24.5, -66.2, 49])
            
    # Define map view options
    drought_veg_index_map_view_options = MapView(
            height='630px',
            width='100%',
            controls=['ZoomSlider', 'Rotate', 'ScaleLine', 'FullScreen',
                      {'MousePosition': {'projection': 'EPSG:4326'}},
                      {'ZoomToExtent': {'projection': 'EPSG:4326', 'extent': [-112, 36.3, -98.5, 41.66]}}],
            layers=[tiger_boundaries,climo_divs,vegdri,quickdri,NLCD,watersheds],
            view=view_options,
            basemap='OpenStreetMap',
            legend=True
        )

    context = {
        'drought_veg_index_map_view_options':drought_veg_index_map_view_options,
    }

    return render(request, 'co_drought/drought_veg_index.html', context)
########################### End drought_veg_index map #######################################
######################## Start Drought Precip Map Main ###################################
@login_required()
def drought_prec_map(request):
    """
    Controller for the app drought map page.
    """
           
    view_center = [-105.2, 39.0]
    view_options = MVView(
        projection='EPSG:4326',
        center=view_center,
        zoom=7.0,
        maxZoom=12,
        minZoom=5
    )

    # TIGER state/county mapserver
    tiger_boundaries = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer'},
        legend_title='States & Counties',
        layer_options={'visible':True,'opacity':0.8},
        legend_extent=[-112, 36.3, -98.5, 41.66])    
        
    # USGS Rest server for HUC watersheds        
    watersheds = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer'},
        legend_title='HUC Watersheds',
        layer_options={'visible':False,'opacity':0.4},
        legend_extent=[-112, 36.3, -98.5, 41.66])
    
    # Previous 7-day precip from USGS (not working) 
    prec7_legend = MVLegendImageClass(value='7-day Precip Total',
                         image_url='https://vegdri.cr.usgs.gov/wms.php?service=WMS&request=GetLegendGraphic&format=image%2Fpng&width=20&height=20&LAYER=PRECIP_TP7')   
    precip7day = MVLayer(
            source='ImageWMS',
            options={'url': 'https://vegdri.cr.usgs.gov/wms.php?',
                     'params': {'LAYERS': 'PRECIP_RD7'},
                   'serverType': 'geoserver'},
            layer_options={'visible':True,'opacity':0.5},
            legend_title='Prev 7-day Precip',
            legend_classes=[prec7_legend],
            legend_extent=[-126, 24.5, -66.2, 49])
            
    # NWS Precip analysis data       
    nws_prec7 = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Forecasts_Guidance_Warnings/rfc_dly_qpe/MapServer',
                'params': {'LAYERS': 'show:15'}},
        legend_title='7-day % of Norm',
        layer_options={'visible':False,'opacity':0.6},
        legend_extent=[-112, 36.3, -98.5, 41.66])
               
    # NOAA NOHRSC snow products
    snodas_swe = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Observations/NOHRSC_Snow_Analysis/MapServer',
                'params': {'LAYERS': 'show:7'}},
        legend_title='SNODAS Model SWE',
        layer_options={'visible':True,'opacity':0.7},
        legend_classes=[
            MVLegendClass('polygon', '0.04', fill='rgba(144,175,180,0.7)'),
            MVLegendClass('polygon', '0.20', fill='rgba(128,165,192,0.7)'),
            MVLegendClass('polygon', '0.39', fill='rgba(95,126,181,0.7)'),
            MVLegendClass('polygon', '0.78', fill='rgba(69,73,171,0.7)'),
            MVLegendClass('polygon', '2.00', fill='rgba(71,46,167,0.7)'),
            MVLegendClass('polygon', '3.90', fill='rgba(79,20,144,0.7)'),
            MVLegendClass('polygon', '5.90', fill='rgba(135,33,164,0.7)'),
            MVLegendClass('polygon', '9.80', fill='rgba(155,53,148,0.7)'),
            MVLegendClass('polygon', '20', fill='rgba(189,88,154,0.7)'),
            MVLegendClass('polygon', '30', fill='rgba(189,115,144,0.7)'),
            MVLegendClass('polygon', '39', fill='rgba(195,142,150,0.7)'),
            MVLegendClass('polygon', '79', fill='rgba(179,158,153,0.7)')],
        legend_extent=[-112, 36.3, -98.5, 41.66])
        
    # Coloado CDSS snowpack data (requires token --- expires)
    snodas_cdss = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://gis.colorado.gov/oit/rest/services/DNR_CWCB/SNODAS/MapServer',
                'params': {'LAYERS': 'show:0','TOKEN':'4HhtbZGoUS6eXs7G93BmoyFjDnjQNfNC_pWr3N-FbLI.'}},
        legend_title='SNODAS Mean',
        layer_options={'visible':False,'opacity':0.5},
        legend_extent=[-112, 36.3, -98.5, 41.66])
    
    # testing homemand kml image dispaly for SNODAS % daily median SWE (kml not working - kmz contains png with data??)    
    snodas_kml_med = MVLayer(
        source='KML',
        options={'url': '/static/tethys_gizmos/data/20180322_multyear_perc_med.kmz'},
        layer_options={'visible':False,'opacity':0.5},
        legend_title='SNODAS SWE % of Median',
        legend_extent=[-126, 24.5, -66.2, 49])
        
    # Define map view options
    drought_prec_map_view_options = MapView(
            height='630px',
            width='100%',
            controls=['ZoomSlider', 'Rotate', 'FullScreen', 'ScaleLine', 'WMSLegend',
                      {'MousePosition': {'projection': 'EPSG:4326'}},
                      {'ZoomToExtent': {'projection': 'EPSG:4326', 'extent': [-112, 36.3, -98.5, 41.66]}}],
            layers=[tiger_boundaries,snodas_swe,nws_prec7,watersheds],
            view=view_options,
            basemap='OpenStreetMap',
            legend=True
        )

    context = {
        'drought_prec_map_view_options':drought_prec_map_view_options,
    }

    return render(request, 'co_drought/drought_prec.html', context)
##################### End Drought Precip Map #############################################
############################## Drought Fire Main ############################################
@login_required()
def drought_fire_map(request):
    """
    Controller for the app drought map page.
    """
           
    view_center = [-105.2, 39.0]
    view_options = MVView(
        projection='EPSG:4326',
        center=view_center,
        zoom=7.0,
        maxZoom=12,
        minZoom=5
    )

    # TIGER state/county mapserver
    tiger_boundaries = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer'},
        legend_title='States & Counties',
        layer_options={'visible':True,'opacity':0.8},
        legend_extent=[-112, 36.3, -98.5, 41.66])    
        
    # USGS Rest server for HUC watersheds        
    watersheds = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer'},
        legend_title='HUC Watersheds',
        layer_options={'visible':False,'opacity':0.4},
        legend_extent=[-112, 36.3, -98.5, 41.66])

    ## Colorado Wildfire Risk Assessment Portal - Fire Intensity Scale
    # https://www.coloradowildfirerisk.com/map/Public
    fire_intensity = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://www.coloradowildfirerisk.com/arcgis/rest/services/WUI_fieldwork/FireIntensityScale/MapServer',
                'params': {'LAYERS': 'show:0'}},
        legend_title='Fire Intensity Scale',
        legend_classes=[
            MVLegendClass('polygon', 'Lowest Intensity', fill='rgba(199,215,158,0.5)'),
            MVLegendClass('polygon', '', fill='rgba(255,255,190,0.5)'),
            MVLegendClass('polygon', 'Moderate Intensity', fill='rgba(255,214,79,0.5)'),
            MVLegendClass('polygon', '', fill='rgba(255,153,0,0.5)'),
            MVLegendClass('polygon', 'Highest Intensity', fill='rgba(230,0,0,0.5)')],
        layer_options={'visible':False,'opacity':0.6},
        legend_extent=[-112, 36.3, -98.5, 41.66])
        
    fire_occur = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://www.coloradowildfirerisk.com/arcgis/rest/services/WUI_fieldwork/FireOccurrenceAreas/MapServer',
                'params': {'LAYERS': 'show:0'}},
        legend_title='Fire Occurance Areas',
        legend_classes=[
            MVLegendClass('polygon', '1 Lowest Occurrence', fill='rgba(204,204,204,0.5)'),
            MVLegendClass('polygon', '2', fill='rgba(199,215,158,0.5)'),
            MVLegendClass('polygon', '3', fill='rgba(242,242,183,0.5)'),
            MVLegendClass('polygon', '4', fill='rgba(255,211,127,0.5)'),
            MVLegendClass('polygon', '5', fill='rgba(255,170,0,0.5)'),
            MVLegendClass('polygon', '6', fill='rgba(168,0,0,0.5)'),
            MVLegendClass('polygon', '7 Highest Intensity', fill='rgba(230,0,0,0.5)')],
        layer_options={'visible':False,'opacity':0.6},
        legend_extent=[-112, 36.3, -98.5, 41.66])
        
    ## WFAS - Severe Fire Weather Potential Forecast 
    ## https://m.wfas.net/wfas_sfwp_map.html
    wfas_legend = MVLegendImageClass(value='SFWF',
                             image_url='https://www.wfas.net/cgi-bin/mapserv?map=/var/www/html/nfdr/mapfiles/ndfd_geog5.map&SERVICE=WMS&VERSION=1.3.0&SLD_VERSION=1.1.0&REQUEST=GetLegendGraphic&FORMAT=image/jpeg&LAYER=fbxday0&STYLE=')
    wfas_sfw = MVLayer(
        source='ImageWMS',
        options={'url': 'https://www.wfas.net/cgi-bin/mapserv?map=/var/www/html/nfdr/mapfiles/wfas_wms_new.map',
                 'params': {'LAYERS': 'fbxday0'}},
        layer_options={'visible':True,'opacity':0.7},
        legend_title='Fire Weather Forecast',
        legend_classes=[wfas_legend],
        legend_extent=[-126, 24.5, -66.2, 49])
        
    ## NOAA - nowcoast fire weather
    nws_fire_hazards = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://nowcoast.noaa.gov/arcgis/rest/services/nowcoast/wwa_meteoceanhydro_longduration_hazards_time/MapServer',
                'params': {'LAYERS': 'show:38'}},
        legend_title='NWS Fire Hazards',
        legend_classes=[
            MVLegendClass('polygon', 'Red Flag Warning', fill='rgba(255,20,147,0.6)'),
            MVLegendClass('polygon', 'Fire Weather Watch', fill='rgba(255,222,173,0.6)')],
        layer_options={'visible':False,'opacity':0.6},
        legend_extent=[-112, 36.3, -98.5, 41.66])
        
    # Define map view options
    drought_fire_map_view_options = MapView(
            height='630px',
            width='100%',
            controls=['ZoomSlider', 'Rotate', 'ScaleLine', 'FullScreen',
                      {'MousePosition': {'projection': 'EPSG:4326'}},
                      {'ZoomToExtent': {'projection': 'EPSG:4326', 'extent': [-130, 22, -65, 54]}}],
            layers=[tiger_boundaries,wfas_sfw,fire_intensity,fire_occur,nws_fire_hazards,watersheds],
            view=view_options,
            basemap='OpenStreetMap',
            legend=True
        )

    context = {
        'drought_fire_map_view_options':drought_fire_map_view_options,
    }

    return render(request, 'co_drought/drought_fire.html', context)
############################## End Drought Fire Map #############################################
############################## Drought Vulnerability Main ############################################
@login_required()
def drought_vuln_map(request):
    """
    Controller for the app drought map page.
    """
           
    view_center = [-105.2, 39.0]
    view_options = MVView(
        projection='EPSG:4326',
        center=view_center,
        zoom=7.0,
        maxZoom=12,
        minZoom=5
    )

    # TIGER state/county mapserver
    tiger_boundaries = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer'},
        legend_title='States & Counties',
        layer_options={'visible':True,'opacity':0.8},
        legend_extent=[-112, 36.3, -98.5, 41.66])    
    
    ##### WMS Layers - Ryan
    usdm_legend = MVLegendImageClass(value='Drought Category',
                             image_url='http://ndmc-001.unl.edu:8080/cgi-bin/mapserv.exe?map=/ms4w/apps/usdm/service/usdm_current_wms.map&version=1.3.0&service=WMS&request=GetLegendGraphic&sld_version=1.1.0&layer=usdm_current&format=image/png&STYLE=default')
    usdm_current = MVLayer(
            source='ImageWMS',
            options={'url': 'http://ndmc-001.unl.edu:8080/cgi-bin/mapserv.exe?',
                     'params': {'LAYERS':'usdm_current','FORMAT':'image/png','VERSION':'1.1.1','STYLES':'default','MAP':'/ms4w/apps/usdm/service/usdm_current_wms.map'}},
            layer_options={'visible':False,'opacity':0.25},
            legend_title='USDM',
            legend_classes=[usdm_legend],
            legend_extent=[-126, 24.5, -66.2, 49])
   
    # USGS Rest server for HUC watersheds        
    watersheds = MVLayer(
        source='TileArcGISRest',
        options={'url': 'https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer'},
        legend_title='HUC Watersheds',
        layer_options={'visible':False,'opacity':0.4},
        legend_extent=[-112, 36.3, -98.5, 41.66])
    
    # Ag vulnerability county risk score map -> from 2018 CO Drought Plan update
    ag_vuln_legend = MVLegendImageClass(value='Risk Score',
                             image_url='/static/tethys_gizmos/data/ag_vuln_legend.jpg')
    ag_vuln_kml = MVLayer(
        source='KML',
        options={'url': '/static/tethys_gizmos/data/CO_Ag_vuln_score_2018.kml'},
        layer_options={'visible':True,'opacity':0.5},
        legend_title='Ag Vulnerability Score',
        feature_selection=True,
        legend_classes=[ag_vuln_legend],
        legend_extent=[-126, 24.5, -66.2, 49])
        
    # Define GeoJSON layer
    # Data from CoCoRaHS Condition Monitoring: https://www.cocorahs.org/maps/conditionmonitoring/
    with open(r'C:\Users\Lynker1\tethys\src\tethys_gizmos\static\tethys_gizmos\data\cartodb-query.geojson') as f:
        data = json.load(f)
        
    # the section below is grouping data by 'scalebar' drought condition
    # this is a work around for displaying each drought report classification with a unique colored icon
    data_sd = {}; data_md ={}; data_ml={}
    data_sd[u'type'] = data['type']; data_md[u'type'] = data['type']; data_ml[u'type'] = data['type']
    data_sd[u'features'] = [];data_md[u'features'] = [];data_ml[u'features'] = []
    for element in data['features']:
        if 'Severely Dry' in element['properties']['scalebar']:
            data_sd[u'features'].append(element)
        if 'Moderately Dry' in element['properties']['scalebar']:
            data_md[u'features'].append(element)
        if 'Mildly Dry' in element['properties']['scalebar']:
            data_ml[u'features'].append(element)
        
    cocojson_sevdry = MVLayer(
        source='GeoJSON',
        options=data_sd,
        legend_title='Condition Monitor',
        legend_extent=[-112, 36.3, -98.5, 41.66],
        feature_selection=True,
        legend_classes=[MVLegendClass('point', 'Severely Dry', fill='#67000d')],
        layer_options={'style': {'image': {'circle': {'radius': 6,'fill': {'color':  '#67000d'},'stroke': {'color': '#ffffff', 'width': 1},}}}})

    cocojson_moddry = MVLayer(
        source='GeoJSON',
        options=data_md,
        legend_title='',
        legend_extent=[-112, 36.3, -98.5, 41.66],
        feature_selection=True,
        legend_classes=[MVLegendClass('point', 'Moderately Dry', fill='#a8190d')],
        layer_options={'style': {'image': {'circle': {'radius': 6,'fill': {'color':  '#a8190d'},'stroke': {'color': '#ffffff', 'width': 1},}}}})

    cocojson_mildry = MVLayer(
        source='GeoJSON',
        options=data_ml,
        legend_title='',
        legend_extent=[-112, 36.3, -98.5, 41.66],
        feature_selection=True,
        legend_classes=[MVLegendClass('point', 'Mildly Dry', fill='#f17d44')],
        layer_options={'style': {'image': {'circle': {'radius': 6,'fill': {'color':  '#f17d44'},'stroke': {'color': '#ffffff', 'width': 1},}}}})

        
    # Define map view options
    drought_vuln_map_view_options = MapView(
            height='630px',
            width='100%',
            controls=['ZoomSlider', 'Rotate', 'ScaleLine', 'FullScreen',
                      {'MousePosition': {'projection': 'EPSG:4326'}},
                      {'ZoomToExtent': {'projection': 'EPSG:4326', 'extent': [-130, 22, -65, 54]}}],
            layers=[tiger_boundaries,cocojson_sevdry,cocojson_moddry,cocojson_mildry,ag_vuln_kml,usdm_current,watersheds],
            view=view_options,
            basemap='OpenStreetMap',
            legend=True
        )

    context = {
        'drought_vuln_map_view_options':drought_vuln_map_view_options,
    }

    return render(request, 'co_drought/drought_vuln.html', context)
##################### End Drought Vulnerability Map #############################################
#########################################################################################
@login_required()
def drought_4pane(request):
    context = {}
    return render(request, 'co_drought/drought_4pane.html', context)
#########################################################################################
@login_required()
def add_dam(request):
    """
    Controller for the Add Dam page.
    """
    # Default Values
    location = ''
    name = ''
    owner = 'Reclamation'
    river = ''
    date_built = ''

    # Errors
    location_error = ''
    name_error = ''
    owner_error = ''
    river_error = ''
    date_error = ''

    # Handle form submission
    if request.POST and 'add-button' in request.POST:
        # Get values
        has_errors = False
        location = request.POST.get('geometry', None)
        name = request.POST.get('name', None)
        owner = request.POST.get('owner', None)
        river = request.POST.get('river', None)
        date_built = request.POST.get('date-built', None)

        # Validate
        if not location:
            has_errors = True
            location_error = 'Location is required.'

        if not name:
            has_errors = True
            name_error = 'Name is required.'

        if not owner:
            has_errors = True
            owner_error = 'Owner is required.'

        if not river:
            has_errors = True
            river_error = 'River is required.'

        if not date_built:
            has_errors = True
            date_error = 'Date Built is required.'

        if not has_errors:
            add_new_dam(location=location, name=name, owner=owner, river=river, date_built=date_built)
            return redirect(reverse('dam_inventory:home'))

        messages.error(request, "Please fix errors.")

    # Define form gizmos
    initial_view = MVView(
        projection='EPSG:4326',
        center=[-98.6, 39.8],
        zoom=3.5
    )

    drawing_options = MVDraw(
        controls=['Modify', 'Delete', 'Move', 'Point'],
        initial='Point',
        output_format='GeoJSON',
        point_color='#FF0000'
    )

    location_input = MapView(
        height='300px',
        width='100%',
        basemap='OpenStreetMap',
        draw=drawing_options,
        view=initial_view
    )

    name_input = TextInput(
        display_text='Name',
        name='name',
        initial=name,
        error=name_error
    )

    owner_input = SelectInput(
        display_text='Owner',
        name='owner',
        multiple=False,
        options=[('Reclamation', 'Reclamation'), ('Army Corp', 'Army Corp'), ('Other', 'Other')],
        initial=owner,
        error=owner_error
    )

    river_input = TextInput(
        display_text='River',
        name='river',
        placeholder='e.g.: Mississippi River',
        initial=river,
        error=river_error
    )

    date_built = DatePicker(
        name='date-built',
        display_text='Date Built',
        autoclose=True,
        format='MM d, yyyy',
        start_view='decade',
        today_button=True,
        initial=date_built,
        error=date_error
    )

    add_button = Button(
        display_text='Add',
        name='add-button',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'form': 'add-dam-form'},
        submit=True
    )

    cancel_button = Button(
        display_text='Cancel',
        name='cancel-button',
        href=reverse('dam_inventory:home')
    )

    context = {
        'location_input': location_input,
        'location_error': location_error,
        'name_input': name_input,
        'owner_input': owner_input,
        'river_input': river_input,
        'date_built_input': date_built,
        'add_button': add_button,
        'cancel_button': cancel_button,
    }

    return render(request, 'co_drought/add_dam.html', context)


@login_required()
def list_dams(request):
    """
    Show all dams in a table view.
    """
    dams = get_all_dams()
    table_rows = []

    for dam in dams:
        table_rows.append(
            (
                dam['name'], dam['owner'],
                dam['river'], dam['date_built']
            )
        )

    dams_table = DataTableView(
        column_names=('Name', 'Owner', 'River', 'Date Built'),
        rows=table_rows,
        searching=False,
        orderClasses=False,
        lengthMenu=[ [10, 25, 50, -1], [10, 25, 50, "All"] ],
    )

    context = {
        'dams_table': dams_table
    }

    return render(request, 'co_drought/list_dams.html', context)
