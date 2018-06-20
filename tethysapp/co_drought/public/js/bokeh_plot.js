$(function() { //wait for page to load

    $.ajax({
        url: 'drought_bokeh_plot',
        method: 'GET',
        data: {
            'plot_height': 500, //example data to pass to the controller
        },
        success: function(data) {
            // add plot to page
            $("#bokeh_plot_div").html(data);
        }
    });

});