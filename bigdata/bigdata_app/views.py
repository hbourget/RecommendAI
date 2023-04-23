import threading

from django.shortcuts import render

# Create your views here.

from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.staticfiles.storage import staticfiles_storage
import random
import os
import csv
from .function.function import *


def getImageUrl(imageName):
    img = imageName.split(".")[0]

    with open("./bigdata_app/data/unsplash-research-dataset-lite-latest/photos.tsv000", "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for i, row in enumerate(reader):
            if img == row[0]:
                url = row[2]
                break

    return url


def accueil_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if not os.path.exists("./bigdata_app/data/user_preferences.json"):
        status = 0
        url_image = None
        name_image= None
    else:
        status = 1
        names_recommended = hybrid_recommendation(request.user.id)
        print(names_recommended)
        if(len(names_recommended) == 0):
            names_recommended = collaborative_filtering_recommendation(request.user.id)
        name_image = names_recommended[random.randint(0, len(names_recommended)-1)]
        url_image = getImageUrl(name_image)

    if request.method == 'POST':
        if request.POST.get('like') == '1':
            add_user_preference(request.user.id, name_image)

    context = {'status': status, 'url_image': url_image}
    return render(request, 'accueil.html', context)


def download_all_data_async():
    t = threading.Thread(target=insertDefaultData)
    t.start()

def dataset_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if not os.path.exists("./bigdata_app/data/user_preferences.json"):
        download_all_data_async()
    return redirect('accueil')


def login_view(request):
    statusLog = None
    stringMessageLog = ""
    if request.user.is_authenticated:
        return redirect('accueil')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                statusLog = 1
                return redirect('accueil')
        else:
            statusLog = 0
            stringMessageLog = "Identifiants invalides."
    else:
        form = AuthenticationForm()
    return render(request, 'login.html')


def logout_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    else:
        logout(request)
        return redirect('login')

