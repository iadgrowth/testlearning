from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse('Fish and Chips')

def test_response(request):
    return HttpResponse('IAD')