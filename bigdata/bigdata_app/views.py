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


from .download_dataset import *


def randomURL(random_line):
    with open("unsplash_dataset/photos.tsv000", "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        # Itération sur chaque ligne du fichier
        for i, row in enumerate(reader):
            if i == random_line:
                url = row[2]
                print(url)

    return url


def accueil_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if not os.path.exists(download_dir):
        os.mkdir(download_dir)

    if len(os.listdir(download_dir)) == 0:
        status = 0
        url_image = None
    else:
        status = 1
        randomNumber = random.randint(0, 20000)
        url_image = randomURL(randomNumber)

    if request.method == 'POST':
        if request.POST.get('like') == '1':
            print("Bonjour")
        elif request.POST.get('like') == '0':
            print("au revoir")
    context = {'status': status, 'url_image': url_image}
    return render(request, 'accueil.html', context)


def dataset_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    download_unsplash_dataset(download_dir)
    return render(request, 'acceuil.html')


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


def profile_view(request):
    if not request.user.is_authenticated:
        # return redirect('login')
        pass
    return render(request, 'profile.html')
