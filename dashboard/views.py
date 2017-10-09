from django.shortcuts import render

# Create your views here.


def index(request):
    print("Hello world!")
    return render(request, "index.html")