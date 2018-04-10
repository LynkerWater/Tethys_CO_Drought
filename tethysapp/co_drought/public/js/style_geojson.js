function my_styler(feature, resolution) {
var image, properties;
    properties = feature.getProperties();

    // Default icon
    image = new ol.style.Circle({
        radius: 5,
        fill: new ol.style.Fill({
            color: 'red'
        })
    });

    if ('type' in properties) {
        if (properties.type === 'TANK') {
            image = new ol.style.RegularShape({
                fill: new ol.style.Fill({
                    color: SELECTED_NODE_COLOR
                }),
                stroke: new ol.style.Stroke({
                    color: 'white',
                    width: 1
                }),
                points: 4,
                radius: 14,
                rotation: 0,
                angle: Math.PI / 4
            });

        }
        else if (properties.type === 'RESERVOIR') {
            image = new ol.style.RegularShape({
                fill: new ol.style.Fill({
                    color: SELECTED_NODE_COLOR
                }),
                stroke: new ol.style.Stroke({
                    color: 'white',
                    width: 1
                }),
                points: 3,
                radius: 14,
                rotation: 0,
                angle: 0
            });
        }
    }

    return [new ol.style.Style({image: image})];

}

TETHYS_MAP_VIEW.overrideSelectionStyler('points', my_styler);