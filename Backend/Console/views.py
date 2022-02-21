from django.shortcuts import render

# Create your views here.
def Application(request):
    return render(request,"Console/index.html")