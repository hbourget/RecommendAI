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

def accueil_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    imgList = ['static/img/poulpe.png', 'static/img/croix.png', 'static/img/img.png'
        ]
    if  len(imgList) == 0:
        status = 0
        random_img = None
    else:
        status = 1
        random_img = random.choice(imgList)

    if request.method == 'POST':
        if request.POST.get('like') == '1':
            print("Bonjour")
        elif request.POST.get('like') == '0':
            print("au revoir")
    context = {'random_img': random_img, 'status': status}
    return render(request, 'accueil.html', context)

def dataset_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    print("Telechargement")
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
    
def profile_view(request):
    if not request.user.is_authenticated:
        #return redirect('login')
        pass
    return render(request, 'profile.html')