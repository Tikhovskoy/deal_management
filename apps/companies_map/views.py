from django.shortcuts import render

def index(request):
    return render(request, 'companies_map/index.html')
