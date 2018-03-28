from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import CustomSetting
from tethys_sdk.app_settings import SpatialDatasetServiceSetting


class DamInventory(TethysAppBase):
    """
    Tethys app class for Dam Inventory.
    """

    name = 'Colorado Drought Monitoring Tool - Beta'
    index = 'co_drought:drought'
    icon = 'co_drought/images/drought_logo.png'
    package = 'co_drought'
    root_url = 'co-drought'
    color = '#0063bf'
    description = 'Lynker prototype drought monitoring tool for Colorado Drought Plan'
    tags = ''
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (
            UrlMap(
                name='drought',
                url='co-drought/drought',
                controller='co_drought.controllers.drought_map'
            ),   
            UrlMap(
                name='drought_nwmfx',
                url='co-drought/drought_nwmfx',
                controller='co_drought.controllers.drought_map_nwmforecast'
            ), 
            UrlMap(
                name='drought_outlook',
                url='co-drought/drought_outlook',
                controller='co_drought.controllers.drought_map_outlook'
            ), 
            UrlMap(
                name='drought_index',
                url='co-drought/drought_index',
                controller='co_drought.controllers.drought_index_map'
            ), 
            UrlMap(
                name='drought_veg_index',
                url='co-drought/drought_veg_index',
                controller='co_drought.controllers.drought_veg_index_map'
            ),
            UrlMap(
                name='drought_prec',
                url='co-drought/drought_prec',
                controller='co_drought.controllers.drought_prec_map'
            ),
            UrlMap(
                name='drought_4pane',
                url='co-drought/drought_4pane',
                controller='co_drought.controllers.drought_4pane'
            ),
            UrlMap(
                name='add_dam',
                url='co-drought/dams/add',
                controller='co_drought.controllers.add_dam'
            ),
            UrlMap(
                name='dams',
                url='co-drought/dams',
                controller='co_drought.controllers.list_dams'
            ),
        )

        return url_maps

    def custom_settings(self):
        """
        Example custom_settings method.
        """
        custom_settings = (
            CustomSetting(
                name='max_dams',
                type=CustomSetting.TYPE_INTEGER,
                description='Maximum number of dams that can be created in the app.',
                required=False
            ),
        )
        return custom_settings
