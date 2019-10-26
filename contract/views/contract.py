from django.shortcuts import render
from django.http import JsonResponse

from rest_framework.decorators import api_view

import requests, json

URL = "http://localhost:"
PORT = 8000

def build_URL_PORT():
    global URL
    global PORT
    return "%s%d" % (URL, PORT)

NO_DATA_HASH = ''.join(["0" for i in range(128)])

@api_view(["GET"])
def validate(request, project_id):
    id = int(project_id)

    url = build_URL_PORT() + "/system/projects/"
    url += str(id)
    print(url)
    response = requests.get(url = url)
    return JsonResponse(json.loads(response.content)["data"], safe = False)