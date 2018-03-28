$(function()
{
      var layer = new ol.layer.Tile({
        source: new ol.source.OSM()
      });
      var tiger_county_state = new ol.layer.Tile({
          extent: [-13884991, 2870341, -7455066, 6338219],
          source: new ol.source.TileArcGISRest({
            url: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer'
          }),
          opacity: 0.7
        })
      var usdm_layer = new ol.layer.Image({
          extent: [-13884991, 2870341, -7455066, 6338219],
          source: new ol.source.ImageWMS({
            url: 'http://ndmc-001.unl.edu:8080/cgi-bin/mapserv.exe?map=/ms4w/apps/usdm/service/usdm_current_wms.map&',
            params: {'LAYERS': 'usdm_current'},
            ratio: 1,
            serverType: 'geoserver',
            attributions: 'NDMC USDM'
          }),
		  visible: true,
		  setAttributions: 'USDM NDMC',
          opacity: 0.5
      })
        var spi_6 = new ol.layer.Tile({
          extent: [-13884991, 2870341, -7455066, 6338219],
          source: new ol.source.TileArcGISRest({
            url: 'https://gis.ncdc.noaa.gov/arcgis/rest/services/cdo/indices/MapServer',
            params: {'LAYERS': 'show:14','layerDefs':'{"14":"YEARMONTH=201712"}'},
            ratio: 1,
            attributions: 'NCEI SPI'
          }),
		  visible: true,
          opacity: 0.6
      })
        var ncdc_pdsi = new ol.layer.Tile({
          extent: [-13884991, 2870341, -7455066, 6338219],
          source: new ol.source.TileArcGISRest({
            url: 'https://gis.ncdc.noaa.gov/arcgis/rest/services/cdo/indices/MapServer',
            params: {'LAYERS': 'show:2','layerDefs':'{"2":"YEARMONTH=201712"}'},
            ratio: 1,
            attributions: 'NDMC USDM'
          }),
		  visible: true,
          opacity: 0.6
      })
      var ncep_month_outlook_layer = new ol.layer.Tile({
          extent: [-13884991, 2870341, -7455066, 6338219],
          source: new ol.source.TileArcGISRest({
            url: 'https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Climate_Outlooks/cpc_drought_outlk/MapServer',
            params: {'LAYERS': 'show:0'}
          }),
          opacity: 0.5
        })
      var nwm_streamanom_layer = new ol.layer.Tile({
          extent: [-13884991, 2870341, -7455066, 6338219],
          source: new ol.source.TileArcGISRest({
            url: 'https://mapservice.nohrsc.noaa.gov/arcgis/rest/services/national_water_model/NWM_Stream_Analysis/MapServer',
            params: {'LAYERS': 'show:7,8,9,10,11,12'}
          }),
          opacity: 0.5
        })
      var nwm_soil_layer = new ol.layer.Tile({
          extent: [-13884991, 2870341, -7455066, 6338219],
          source: new ol.source.TileArcGISRest({
            url: 'https://mapservice.nohrsc.noaa.gov/arcgis/rest/services/national_water_model/NWM_Land_Analysis/MapServer',
          }),
          opacity: 0.5
        })
      var snodas_layer = new ol.layer.Tile({
          extent: [-13884991, 2870341, -7455066, 6338219],
          source: new ol.source.TileArcGISRest({
            url: 'https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Observations/NOHRSC_Snow_Analysis/MapServer',
            params: {'LAYERS': 'show:7'}
          }),
		  visible: true,
          opacity: 0.5
        })

      var co_center = new ol.proj.transform([-105.36,39.11], 'EPSG:4326', 'EPSG:3857');
      var view = new ol.View({
        center: co_center,
        zoom: 6
      });
      var view2 = new ol.View({
        center: co_center,
        zoom: 6
      });
      // create two maps
      var map1 = new ol.Map({
        target: 'map1',
        layers: [layer, usdm_layer,tiger_county_state],
		controls: new ol.Collection(),
        view: view,
      });
      var map2 = new ol.Map({
        target: 'map2',
        layers: [layer, spi_6,tiger_county_state],
        controls: new ol.Collection(),
        view: view
      });
	  var map3 = new ol.Map({
        target: 'map3',
        layers: [layer,ncdc_pdsi,tiger_county_state],
        controls: new ol.Collection(),
        view: view
      });
	  var map4 = new ol.Map({
        target: 'map4',
        layers: [layer,snodas_layer,tiger_county_state],
        controls: new ol.Collection(),
        view: view
      });
	  /*map1.addControl(new ol.control.ZoomSlider());*/

      // and bind the view properties so they effectively share a view (using the listenfor functions in OL4)
/*      view.on('change:center', function(evt){
        view2.setCenter(view.getCenter());
		view2.setZoom(view.getZoom());
});
*/
});