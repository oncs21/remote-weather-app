from html.parser import HTMLParser
from io import StringIO
from metar import Metar
import base64
from io import BytesIO
import folium, json
from .models import Visitor, User
from branca.element import MacroElement, Template
from django.conf import settings
from pathlib import Path
import json
from jinja2 import Template


DEFAULT_WEATHER_ICON_PATH = Path(settings.BASE_DIR) / "app" / "static" / "app" / "img" / "weather_unknown.png"


def storeVisitorInfo(request):
    ip = get_client_ip(request)
    isRegistered = False
    try:
        visitor = Visitor.objects.get(ip = ip)
        pass
    except Visitor.DoesNotExist:

        visitor = Visitor.objects.create(
            ip = ip,
            isRegistered = isRegistered
        )
        visitor.save()

def checkRegisteredVisitor(userId):
    user = User.objects.get(id = userId)
    try:
        visitor = Visitor.objects.get(ip = user.ip)
        visitor.isRegistered = False
    except:
        pass
            
    

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def plotPoint(coords, pointMap, city):
    jobs = []

    for i, (c, ci) in enumerate(zip(coords, city)):
        lat = float(c[0])
        lon = float(c[1])

        marker = folium.Marker(
            location=[lat, lon],
            icon=folium.CustomIcon(str(DEFAULT_WEATHER_ICON_PATH), icon_size=(30, 30))
        ).add_to(pointMap)

        folium.Popup(
            f"<b>{ci}</b><br>Loading…",
            max_width=250
        ).add_to(marker)

        jobs.append({
            "marker": marker.get_name(),
            "lat": lat,
            "lon": lon,
            "city": str(ci),
        })

    map_var = pointMap.get_name()
    jobs_json = json.dumps(jobs)

    js = f"""
    {{% macro script(this, kwargs) %}}
    (function () {{
      const map = {map_var};
      const jobs = {jobs_json};

      function getWeatherIcon(code) {{
        code = Number(code);
        if (code === 0) return "/static/app/img/sunny.png";
        if (code >= 1 && code <= 3) return "/static/app/img/cloudy.png";
        if (code >= 61 && code <= 65) {{
            if (code === 61) return "/static/app/img/rain_intensity/slight.png";
            if (code === 63) return "/static/app/img/rain_intensity/moderate.png";
            return "/static/app/img/rain_intensity/heavy.png"; 
        }}
        if (code >= 71 && code <= 75) return "/static/app/img/snowy.png";
        if (code >= 80 && code <= 82) {{
            if (code == 80) return "/static/app/img/rain_shower_intensity/slight.png";
            if (code == 81) return "/static/app/img/rain_shower_intensity/moderate.png";
            return "/static/app/img/rain_shower_intensity/violent.png";
        }}
        return "/static/app/img/weather_unknown.png";
      }}

      async function update(job) {{
        const marker = window[job.marker];
        if (!marker) return;

        try {{
          const r = await fetch(`/weather/?lat=${{job.lat}}&lon=${{job.lon}}&WMO_codes=true`);
          const data = await r.json();

          if (data.error) {{
            marker.getPopup().setContent(`<b>${{job.city}}</b><br>Error: ${{data.error}}`);
            return;
          }}

          marker.getPopup().setContent(
            `<b>${{job.city}}</b><br>` +
            `Temp: ${{data.temp_c}} °C<br>` +
            `Wind: ${{data.wind_kph}} km/h<br>` +
            `Code: ${{data.weather_code}}`
          );

          marker.setIcon(L.icon({{
            iconUrl: getWeatherIcon(data.weather_code),
            iconSize: [30, 30],
            iconAnchor: [15, 30],
            popupAnchor: [0, -30]
          }}));
        }} catch (e) {{
          marker.getPopup().setContent(`<b>${{job.city}}</b><br>Failed to load weather`);
        }}
      }}

      map.whenReady(function () {{
        jobs.forEach(update);
      }});
    }})();
    {{% endmacro %}}
    """

    macro = MacroElement()
    macro._template = Template(js)
    pointMap.get_root().add_child(macro)



        

# def highlightCountry(country, countryMap):
#     with open('A:/Django Projects/weather project/weather/app/countries.geojson') as handle:
#      country_geo = json.loads(handle.read())

#     for i in country_geo['features']:
#         if i['properties']['ADMIN'] == 'India':
#             country = i
#             break


    # folium.GeoJson(country,
    #             name='india').add_to(countryMap)

    # folium.LayerControl().add_to(countryMap)

# def get_graph():
#     buffer = BytesIO()
#     plt.savefig(buffer, format="png")
#     buffer.seek(0)
#     image_png = buffer.getvalue()
#     graph = base64.b64encode(image_png)
#     graph = graph.decode('utf-8')
#     buffer.close()
#     return graph

# def get_plot():
#     fig = plt.figure(figsize=(10, 10))
#     m = Basemap(projection='lcc', resolution=None,
#             width=8E6, height=8E6, 
#             lat_0=23.117686823036014, lon_0=80.00322021440945,)
#     #m.etopo(scale=0.5, alpha=0.5)
#     m.bluemarble()

#     # Map (long, lat) to (x, y) for plotting
#     x, y = m(77.20861811045259, 28.617638361345335)
#     plt.plot(x, y, 'ok', markersize=5, color="red")
#     plt.text(x, y, ' New Delhi', fontsize=12, color="yellow");
#     graph = get_graph
#     return graph

def getData(usefulData):
    metarData = {}
    ct = 1
    incr = 0
    for i in range(0, len(usefulData)):
        if i < incr:
            continue
        if i == len(usefulData)-1:
            break
        #print("i = ", i)
        city = ''; metarCode = ''
        j = i
        if usefulData[i] == str(ct) or ((usefulData[i]+usefulData[i+1] == str(ct))  and i+1 < len(usefulData)):
            
            if usefulData[i] == str(ct):
                j += 2
            elif usefulData[i]+usefulData[i+1] == str(ct):
                j += 3
            ct += 1
            #print("before city j = ", j)
            while (usefulData[j] != ' '):
                city += usefulData[j]
                j += 1
            #print("after city j = ", j)
            j += 1
            #print("before code j = ", j)
            while usefulData[j] != chr(61):
                metarCode += usefulData[j]
                j += 1
            metarCode += '='
            #print("after code j = ", j)
            j += 2
            incr = j
            #print("incr = ", incr)
            city = city.replace('\n', "")
            city = city.replace('\r', "")
            metarCode = metarCode.replace('\n', " ")
            metarCode = metarCode.replace('\r', " ")
            # mIndex = metarCode.find('/M')
            # bIndex = metarCode.find('BRFEE')
            # if metarCode[mIndex+2] == ' ':
            #     metarCode = metarCode[0:mIndex+2]+metarCode[mIndex+3:]
            # if metarCode[bIndex+2] != ' ':
            #     metarCode = metarCode[0:bIndex+2]+' '+metarCode[bIndex+2:bIndex+4]+metarCode[bIndex+5:]
            # qIndex = metarCode.find('Q1')
            # bIndex = metarCode.find('BECMG')
            # bIndex1 = metarCode.find('BECM')
            # if metarCode[qIndex-1] != ' ':
            #     metarCode = metarCode[0:qIndex]+' '+metarCode[qIndex:]
            # if metarCode[bIndex+4] != ' ':
            #     metarCode = metarCode[0:bIndex+5]+' '+metarCode[bIndex+5:]
            # if metarCode[bIndex+4] == ' ':
            #     metarCode = metarCode[0:bIndex1+4]+metarCode[bIndex1+5:]
            metarCodeList = metarCode.split(' ')
            metarData[city] = metarCode
            if usefulData[j+2] == "-":
                break

    return metarData

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def organizeDecodedData(metarData):
    orgData = {}
    for key in metarData:
        try:
            orgVal = Metar.Metar(metarData[key]).string()
            lst = []
            lst = orgVal
            # lst += orgVal.time().strptime(string_date, "%Y-%m-%d")
            # lst += orgVal.temp()
            # lst += orgVal.dewpt()
            # lst += orgVal.wind()
            # lst += orgVal.visibility()
            # lst += orgVal.press()
            # lst += orgVal.weather()
            # lst += orgVal.sky()
            #lst = orgVal.split(' ')
            orgData[key] = lst
        except Metar.ParserError:
            continue
        
    return orgData
