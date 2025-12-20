from sqlite3 import IntegrityError
from django.shortcuts import render
from django.contrib.auth import login, logout, authenticate
from markdown2 import markdown
import markdown2
import urllib.request
from .utils import get_client_ip, getData, organizeDecodedData, storeVisitorInfo, strip_tags, plotPoint
from metar import Metar
import os
import folium
import urllib
from geopy.geocoders import Nominatim
import itertools
from .models import cityWeatherRequest, weatherData, User
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
import json
from metar import Metar

import uuid
import shutil
import torch

from pipeline.src.model import ResNet18_CustomHead
from pipeline.src.utils import load_images_from_path, get_default_test_transforms
from pipeline.src.inference import infer_on_unknown_data
from pathlib import Path
from django.conf import settings

TEMP_DIR = Path(settings.BASE_DIR) / "pipeline" / "temp_data"
MODEL_WEIGHTS_PATH = Path(settings.BASE_DIR) / "pipeline" / "models"

# Home page view
def weatherView(request):
    storeVisitorInfo(request)
    return render(request, 'app/home.html')

def loginView(request):
    storeVisitorInfo(request)

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username = username, password = password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('home'))
        else:
            return render(request, 'app/home.html', {
                'message': 'Invalid username/password. Please try again!'
            })
    
    else:
        return render(request, 'app/login.html')

def logoutView(request):
    storeVisitorInfo(request)
    logout(request)
    return HttpResponseRedirect(reverse('home'))

def profilePageView(request, userId):
    storeVisitorInfo(request)
    user = User.objects.get(id = userId)
    
    if user.is_authenticated:
        user.isOnline = True
        user.save()

    return render(request, 'app/profile.html', {
        'user': user
    })

def editPageView(request, userId):
    storeVisitorInfo(request)
    user = User.objects.get(id = userId)

    if request.method == "POST":
        jsonData = json.loads(request.body)
        firstName = jsonData.get('firstName')
        lastName = jsonData.get('lastName')
        username = jsonData.get('username')

        user.first_name = firstName
        user.last_name = lastName
        user.username = username
        user.save()
        return JsonResponse("Success", safe=False)
    else:
        return HttpResponseRedirect('profile', kwargs={
            userId: userId,
        })

# Docs page view
def docsPageView(request, contentFile):
    storeVisitorInfo(request)
    #md = open(os.getcwd(), 'r')
    md = open(f"{os.getcwd()}/hava-on/app/content/docs/{contentFile}", 'r')
    content = markdown2.markdown(md.read())

    #ohb = organizeDecodedData(metarData)
    #obs = Metar.Metar(metarData['Ahmedabad'])
    return render(request, 'app/docs.html', {
        'content': content,
    })


def analysisPageView(request):
    if request.method == "POST":
        # jsonData = json.loads(request.body)

        os.makedirs(TEMP_DIR, exist_ok=True)

        for p in TEMP_DIR.iterdir():
            if not p.is_dir():
                continue

            shutil.rmtree(p)

        req_dir = TEMP_DIR / uuid.uuid4().hex
        req_dir.mkdir(parents=True, exist_ok=True)
        

        modelType = request.POST.get('model-type')
        
        uploaded_files = request.FILES.getlist('images')

        for f in uploaded_files:
            file_name = Path(f.name).name
            ext = Path(file_name).suffix.lower()

            final_file_name = f'image-{uuid.uuid4().hex[:8]}{ext}'

            with open(req_dir / final_file_name, "wb") as dest:
                for chunk in f.chunks():
                    dest.write(chunk)

        
        images = load_images_from_path(req_dir)
        test_tfms = get_default_test_transforms()
        model = None
        device = 'cuda'

        model = ResNet18_CustomHead(
                num_classes=5,
            ).to(device)
        
        ckpt = torch.load(MODEL_WEIGHTS_PATH / "resnet18_model.pth", map_location=device)
        state_dict = ckpt["model_state_dict"]
        model.load_state_dict(state_dict)

        pred_labels = infer_on_unknown_data(images, model, device, test_tfms)
        print(pred_labels)

        return JsonResponse({
            'labels': pred_labels
        })

    return render(request, 'app/analysis.html')


def loginPageView(request):
    return render(request, 'app/login.html')


def liveDataPageView(request):
    storeVisitorInfo(request)
    #url = 'https://amssdelhi.gov.in/Palam4.php'
    url = 'https://onapte.github.io/metar-data-file/'
    file = urllib.request.urlopen(url)
    raw_data = file.read().decode('utf-8')
    usefulData = strip_tags(raw_data)

    metarData = getData(usefulData[114:])
    finalData = organizeDecodedData(metarData)

    if request.method == "POST":
        c = request.POST['city-inp']
        ip = get_client_ip(request)
        newObj = cityWeatherRequest.objects.create(
            city = c,
            userIP = ip
        )
        newObj.save()
        return HttpResponseRedirect(reverse('livedata'))

    # Individual field lists
    city = finalData.keys()
    stationCode = []
    timeOfReport = []
    temperature = []
    dewPoint = []
    windSpeed = []
    visibility = []
    pressure = []
    weather = []
    sky = []

    for key in finalData:
        tempString = ''
        data = finalData[key]

        # Station code
        for i in range(0, len(data) - 7):
            tempString = data[i] + data[i + 1] + data[i + 2] + data[
                i + 3] + data[i + 4] + data[i + 5] + data[i + 6]
            if tempString == 'station':
                tempString = ''
                for j in range(i + 9, len(data)):
                    if data[j] != '\n':
                        tempString += data[j]
                    else:
                        stationCode.append(tempString)
                        break
                break

        tempString = ''

        # Time of report
        for i in range(0, len(data) - 4):
            tempString = data[i] + data[i + 1] + data[i + 2] + data[i + 3]
            if tempString == "time":
                tempString = ''
                for j in range(i + 6, len(data)):
                    if data[j] != '\n':
                        tempString += data[j]
                    else:
                        timeOfReport.append(tempString)
                        break
                break
        
        tempString = ''

        # Temperature
        for i in range(0, len(data) - 11):
            tempString = data[i] + data[i + 1] + data[i + 2] + data[i + 3] + data[i + 4] + data[i + 5] + data[i + 6] + data[i + 7] + data[i + 8] + data[i + 9] + data[i + 10]
            if tempString == "temperature":
                tempString = ''
                for j in range(i + 13, len(data)):
                    if data[j] != '\n':
                        tempString += data[j]
                    else:
                        temperature.append(tempString)
                        break
                break
        
        tempString = ''

        # Dew point
        for i in range(0, len(data) - 9):
            tempString = data[i] + data[i + 1] + data[i + 2] + data[i + 3] + data[i + 4] + data[i + 5] + data[i + 6] + data[i + 7] + data[i + 8]
            if tempString == "dew point":
                tempString = ''
                for j in range(i + 11, len(data)):
                    if data[j] != '\n':
                        tempString += data[j]
                    else:
                        dewPoint.append(tempString)
                        break
                break
        
        tempString = ''

        # Wind speed
        for i in range(0, len(data) - 4):
            tempString = data[i] + data[i + 1] + data[i + 2] + data[i + 3]
            if tempString == "wind":
                tempString = ''
                for j in range(i + 6, len(data)):
                    if data[j] != '\n':
                        tempString += data[j]
                    else:
                        windSpeed.append(tempString)
                        break
                break
        
        tempString = ''

        # Visibility
        for i in range(0, len(data) - 10):
            tempString = data[i] + data[i + 1] + data[i + 2] + data[i + 3] + data[i + 4] + data[i + 5] + data[i + 6] + data[i + 7] + data[i + 8] + data[i + 9]
            if tempString == "visibility":
                tempString = ''
                for j in range(i + 12, len(data)):
                    if data[j] != '\n':
                        tempString += data[j]
                    else:
                        visibility.append(tempString)
                        break
                break
        
        tempString = ''

        # Pressure
        for i in range(0, len(data) - 8):
            tempString = data[i] + data[i + 1] + data[i + 2] + data[i + 3] + data[i + 4] + data[i + 5] + data[i + 6] + data[i + 7]
            if tempString == "pressure":
                tempString = ''
                for j in range(i + 10, len(data)):
                    if data[j] != '\n':
                        tempString += data[j]
                    else:
                        pressure.append(tempString)
                        break
                break
        
        tempString = ''

        # Weather
        for i in range(0, len(data) - 7):
            tempString = data[i] + data[i + 1] + data[i + 2] + data[i + 3] + data[i + 4] + data[i + 5] + data[i + 6]
            if tempString == "weather":
                tempString = ''
                for j in range(i + 9, len(data)):
                    if data[j] != '\n':
                        tempString += data[j]
                    else:
                        weather.append(tempString)
                        break
                break
        
        tempString = ''

        # Sky
        for i in range(0, len(data) - 3):
            tempString = data[i] + data[i + 1] + data[i + 2]
            if tempString == "sky":
                tempString = ''
                for j in range(i + 5, len(data)):
                    if data[j] != '\n':
                        tempString += data[j]
                    else:
                        sky.append(tempString)
                        break
                break
        
        tempString = ''

    
    
    combinedList = itertools.zip_longest(city, stationCode, timeOfReport, temperature, dewPoint, windSpeed, visibility, pressure, weather, sky)

    for cty, sc, tor, temp, dp, ws, vis, pre, wea, sk in combinedList:
        w = wea
        try:
            weatherObject = weatherData.objects.get(city = cty)

            if w == None:
                w = "No significance"
            # if cty and len(cty) > 5 and (cty[-4]+cty[-3]+cty[-2]+cty[-1]).isupper():
            #     weatherObject.city = cty[0:len(cty)-4]
            #     weatherObject.stationCode = cty[-4]+cty[-3]+cty[-2]+cty[-1]
            # else:
            weatherObject.stationCode = sc

            weatherObject.reportTime = tor
            weatherObject.temperature = temp
            weatherObject.dewPoint = dp
            weatherObject.windSpeed = ws
            weatherObject.visibility = vis
            weatherObject.pressure = pre
            weatherObject.weather = w
            weatherObject.sky = sk
            weatherObject.save()
        except weatherData.DoesNotExist:
            if w == None:
                w = "No significance"
            weatherObject = weatherData.objects.create(
                city = cty,
                stationCode = sc,
                reportTime = tor,
                temperature = temp,
                dewPoint = dp,
                windSpeed = ws,
                visibility = vis,
                pressure = pre,
                weather = w,
                sky = sk
            )
            weatherObject.save()
        except IntegrityError:
            continue

    weatherData.objects = weatherData.objects.all().order_by('city')

    return render(request, 'app/livedata.html', {
        'm': usefulData,
        'finalData': city,
        'weatherData': weatherData.objects.all()
    })

def mapPageView(request):
    url = 'https://amssdelhi.gov.in/Palam4.php'
    file = urllib.request.urlopen(url)
    raw_data = file.read().decode('utf-8')
    usefulData = strip_tags(raw_data)

    metarData = getData(usefulData[114:])
    finalData = organizeDecodedData(metarData)
    city = [key for key in finalData]
    lat = []
    long = []
    geolocator = Nominatim(user_agent="this-weather-project")
    for i in range(0, len(city)):
        gData = geolocator.geocode(city[i])
        if gData != None:
            lat += gData[0]
            long += gData[1]
    long += list(geolocator.geocode(city[0])[1])
    graph = get_plot()
    return render(request, 'app/mapview.html', {
        'dta': graph,
        'lat': geolocator.geocode(city[0]).latitude
    })

def mapView(request):
    storeVisitorInfo(request)
    # url = 'https://amssdelhi.gov.in/Palam4.php'
    # file = urllib.request.urlopen(url)
    # raw_data = file.read().decode('utf-8')
    # usefulData = strip_tags(raw_data)

    # metarData = getData(usefulData[114:])
    # finalData = organizeDecodedData(metarData)
    # city = [key for key in finalData]
    # visibility = []
    # for key in finalData:
    #     tempString = ''
    #     data = finalData[key]
    #     for i in range(0, len(data) - 10):
    #         tempString = data[i] + data[i + 1] + data[i + 2] + data[i + 3] + data[i + 4] + data[i + 5] + data[i + 6] + data[i + 7] + data[i + 8] + data[i + 9]
    #         if tempString == "visibility":
    #             tempString = ''
    #             for j in range(i + 12, len(data)):
    #                 if data[j] != '\n':
    #                     tempString += data[j]
    #                 else:
    #                     visibility.append(tempString)
    #                     break
    #             break
    visibility = []
    visibility = list(weatherData.objects.all().values_list('visibility', flat=True)) 
    city = list(weatherData.objects.all().values_list('city', flat=True)) 
    # for c in weatherData.objects.all():
    #     if c == "" or c is None or isinstance(c, type(None)):
    #         continue
    #     else:
    #         visibility += c.visibility
        
    m = folium.Map(
        location=[20.5937, 78.9629],
        width='90%', 
        height='90%',
        zoom_start=4,
        max_zoom=10,
        min_zoom=4,
        max_bounds=True,
        tiles="Stamen",
        prefer_canvas=True,
        attr="<a href=https://endless-sky.github.io/>Endless Sky</a>",
    )
    geolocator = Nominatim(user_agent="this-weather-project")
    coords = []
    for c in weatherData.objects.all():
        point = geolocator.geocode(c.city)
        if point is not None:
            coords.append([point.latitude, point.longitude])
        if point is None:
            coords.append([-1,-1])
    point = geolocator.geocode("New Delhi")
    plotPoint(coords, m, visibility, city)
    m = m._repr_html_()
    
    return render(request, 'app/mapview.html', {
        'm': m,
        'sm': coords,
        'vis': visibility,
        'cit': city
    })

def ToolsPageView(request):
    if request.method == "POST":
        jsonData = json.loads(request.body)
        formType = jsonData.get('Type')
        if formType == 'METAR':
            metarCode = jsonData.get('Metar')
            decodedVal = Metar.Metar(metarCode).string()
            #return JsonResponse({'DecodedMetarCode': decodedVal})
            return JsonResponse(decodedVal, safe=False)
        else:
            city = jsonData.get('City')
            geolocator = Nominatim(user_agent="this-weather-project")
            info = geolocator.geocode(city)
            lat = info.latitude
            long = info.longitude
            return JsonResponse({
                'latitude': lat,
                'longitude': long,
            })
        

    return render(request, 'app/tools.html')
