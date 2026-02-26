from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

def index(request):
    print('Index view called')
    return HttpResponse('Fish and Chips')

def test_response(request):
    return HttpResponse('IAD')

@csrf_exempt  # <--- Add this decorator
def test_post(request):
    print('Received POST request with data:', request.body)
    return HttpResponse("Received!", status=200)


