import ipywidgets as widgets
from ipywidgets import Box
from ipyleaflet import Map, Marker, basemaps, GeomanDrawControl
from ipyleaflet import Polygon as iPoly
from shapely.geometry.polygon import Polygon
import asf_search as asf
import numpy as np
import datetime as dt

class SearchState:
    def __init__(self):
        self.drawn_polygon = None
        self.scenes = None
        self.search_coordinates = None
        self.path = None
        self.scenes2download = None
    
    def updateScenes2download(self):
        self.scenes2download = [scene for scene in self.scenes if scene.properties['pathNumber'] == self.path]

    def pathSelector(self):
        scenes = self.scenes
        paths = np.array([int(scene.properties['pathNumber']) for scene in scenes])
        paths = np.unique(paths)
        paths_dropdown = widgets.Dropdown(
            options=paths,
            value=paths[0],
            description='Relative Orbit:',
            disabled=False,
        )
        self.path = paths_dropdown.value
        self.updateScenes2download()

        def pathChange(change):
            self.path = change.new
            self.updateScenes2download()
            print('Updated Path')
    
        paths_dropdown.observe(pathChange, names='value')

        return paths_dropdown
    
    def summaryMap(self):
        m = Map(center=(37.5531, -109.6914), zoom=3)

        coords_latlon = [(lat, lon) for lon, lat in self.search_coordinates]
        search_layer = iPoly(locations=coords_latlon, color='orange', fill_color='orange')

        for scene in self.scenes2download:
            coords = scene.geometry['coordinates'][0]
            coords_latlon = [(lat, lon) for lon, lat in coords]
            rpoly = iPoly(locations=coords_latlon, color="green", fill_color="green", fill_opacity=0.1)
            layer = m.add(rpoly)
        m.add(search_layer)

        return m

### Search Parameter Widgets
orbit_direction = widgets.Dropdown(
    options=['ascending', 'descending'],
    value='ascending',
    description='Orbit:',
    disabled=False,
)

start_date_default = dt.datetime(2025, 7, 1)
end_date_default = dt.datetime.today()

start_date = widgets.DatePicker(
    description='Start Date:',
    value=start_date_default,
    disabled=False
)
end_date = widgets.DatePicker(
    description='End Date:',
    value=end_date_default,
    disabled=False
)
items = [orbit_direction, start_date, end_date]
inputs = Box(children=items)

download_location = widgets.Text(
    value='/',
    placeholder='//Enter/Valid/Folder/Paths',
    description='Folder:',
    disabled=False   
)


### Search map
def getSearchMap(inputs, basemap=basemaps.OpenStreetMap.Mapnik):
    m = Map(center=(37.5531, -109.6914), zoom=3, basemap=basemap)
    draw_control = GeomanDrawControl()
    draw_control.polyline =  {
        "pathOptions": {
            "color": "#6bc2e5",
            "weight": 8,
            "opacity": 0.3
        }
    }
    draw_control.polygon = {
        "pathOptions": {
            "fillColor": "#6be5c3",
            "color": "#6be5c3",
            "fillOpacity": 0.3
        }
    }
    draw_control.circlemarker = {
        "pathOptions": {
            "fillColor": "#efed69",
            "color": "#efed69",
            "fillOpacity": 0.62
        }
    }
    draw_control.rectangle = {
        "pathOptions": {
            "fillColor": "#fca45d",
            "color": "#fca45d",
            "fillOpacity": 0.3
        }
    }
    searchState = SearchState()

    def handle_draw(target, action, geo_json):
        searchState.search_coordinates = geo_json[0]['geometry']['coordinates'][0]
        searchState.drawn_polygon = Polygon(geo_json[0]['geometry']['coordinates'][0])

    
        date1 = inputs.children[1].value.strftime('%Y-%m-%d')
        date2 = inputs.children[2].value.strftime('%Y-%m-%d')

        results = asf.geo_search(dataset=asf.constants.NISAR, 
            intersectsWith=str(searchState.drawn_polygon), 
            flightDirection=inputs.children[0].value.upper(), 
            processingLevel='GSLC',start=date1, end=date2)

        searchState.scenes = results
        for result in results:
            coords = result.geometry['coordinates'][0]
            coords_latlon = [(lat, lon) for lon, lat in coords]
            rpoly = iPoly(locations=coords_latlon, color="green", fill_color="green", fill_opacity=0.1)
            layer = m.add(rpoly)

    draw_control.on_draw(handle_draw)
    m.add(draw_control)
    return m, searchState
