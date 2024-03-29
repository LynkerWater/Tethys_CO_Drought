$(function()
{
    // Create new Overlay with the #popup element
    var popup = new ol.Overlay({
        element: document.getElementById('popup')
    });

    // Get the Open Layers map object from the Tethys MapView
    var map = TETHYS_MAP_VIEW.getMap();

    // Get the Select Interaction from the Tethys MapView
    var select_interaction = TETHYS_MAP_VIEW.getSelectInteraction();

    // Add the popup overlay to the map
    map.addOverlay(popup);

    // When selected, call function to display properties
    select_interaction.getFeatures().on('change:length', function(e)
    {
        var popup_element = popup.getElement();

        if (e.target.getArray().length > 0 && e.target.item(0).get('reportdate') != null)
        {
            // this means there is at least 1 feature selected
            var selected_feature = e.target.item(0); // 1st feature in Collection

            // Get coordinates of the point to set position of the popup
            var coordinates = selected_feature.getGeometry().getExtent();

            var popup_content = '<div class="drought-popup">' +
                                    '<p><b>Date: ' + selected_feature.get('reportdate') + '</b></p>' +
                                    '<p><b>Condition: ' + selected_feature.get('scalebar') + '</b></p>' +
                                    '<p><b>Report Type: ' + selected_feature.get('categories') + '</b></p>' +
                                    '<p><b>Desc: ' + selected_feature.get('description') + '</b></p>' +
                                '</div>';

            // Clean up last popup and reinitialize
            $(popup_element).popover('destroy');

            // Delay arbitrarily to wait for previous popover to
            // be deleted before showing new popover.
            setTimeout(function() {
                popup.setPosition(coordinates);

                $(popup_element).popover({
                  'placement': 'bottom',
                  'animation': true,
                  'html': true,
                  'content': popup_content
                });

                $(popup_element).popover('show');
            }, 500);
        }
        else if (e.target.getArray().length > 0 && e.target.item(0).get('description') != null)
        {
            // this means there is at least 1 feature selected
            var selected_feature = e.target.item(0); // 1st feature in Collection

            // Get coordinates of the point to set position of the popup
            var coordinates = selected_feature.getGeometry().getExtent();

            var popup_content = '<div class="drought-popup">' +
                                    '<p><b>Description: ' + selected_feature.get('description') + '</b></p>' +
                                '</div>';

            // Clean up last popup and reinitialize
            $(popup_element).popover('destroy');

            // Delay arbitrarily to wait for previous popover to
            // be deleted before showing new popover.
            setTimeout(function() {
                popup.setPosition(coordinates);

                $(popup_element).popover({
                  'placement': 'bottom',
                  'animation': true,
                  'html': true,
                  'content': popup_content
                });

                $(popup_element).popover('show');
            }, 500);
        } else {
            // remove pop up when selecting nothing on the map
            $(popup_element).popover('destroy');
        }
    });
});