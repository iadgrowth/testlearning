from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    print('Index view called')
    return HttpResponse('Fish and Chips')

def test_response(request):
    return HttpResponse('IAD')