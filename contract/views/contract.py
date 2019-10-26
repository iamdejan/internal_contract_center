from django.shortcuts import render
from django.http import JsonResponse

from rest_framework.decorators import api_view

from contract.models import build_fail_response, build_success_response

import requests, json

URL = "http://localhost:"
PORT = 8000

NO_DATA_HASH = ''.join(["0" for i in range(128)])

def build_URL_PORT(sub_url, id):
    global URL
    global PORT
    url = "%s%d" % (URL, PORT)
    url += "/system/"
    url += sub_url
    url += "/"
    url += id
    return url

@api_view(["GET"])
def validate(request, project_id):

    url = build_URL_PORT("projects", str(project_id))
    response = requests.get(url = url)
    if response.status_code != 200:
        response = build_fail_response({
            "message": "Response is not success"
        })
        return JsonResponse(response.serialize())

    response = json.loads(response.content)
    if response["success"] != True:
        response = build_fail_response({
            "message": "System is busy"
        })
        return JsonResponse(response.serialize())

    data = response["data"]
    checklist_mask = int(data["checklist_mask"])
    current_hash = data["tail_hash"]
    while current_hash != NO_DATA_HASH:
        url = build_URL_PORT("approval", current_hash)
        url +="/validate"
        response = requests.get(url = url)
        response = json.loads(response.content)
        if response["success"] != True:
            response = build_fail_response({
                "message": "Block is broken"
            })
            return JsonResponse(response.serialize())

        # query the hash
        url = build_URL_PORT("approval", current_hash)
        response = requests.get(url = url)
        response = json.loads(response.content)
        data = response["data"]
        current_hash = data["previous_hash"]
        pass

    response = build_success_response({
        "message": "The chain is valid"
    })
    return JsonResponse(response.serialize(), safe = False)