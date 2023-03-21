from django.shortcuts import render

# Create your views here.

from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.forms import AuthenticationForm

def accueil_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'accueil.html')

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
