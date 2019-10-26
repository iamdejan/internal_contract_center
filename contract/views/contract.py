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
    expected_checklist_mask = int(data["checklist_mask"])

    # TODO: check threshold from checklist_mask

    actual_checklist_mask = 0
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

        # query the employee to get the level
        url = build_URL_PORT("employees", str(data["employee_id"]))
        response = requests.get(url = url)
        response = json.loads(response.content)
        data = response["data"]
        actual_checklist_mask |= (1 << (int(data["level_id"]) - 1))
        pass

    response = None
    if expected_checklist_mask == actual_checklist_mask:
        response = build_success_response({
            "message": "The chain is valid"
        })
    else:
        response = build_fail_response({
            "message": "The chain is broken",
            "expected_checklist_mask": expected_checklist_mask,
            "actual_checklist_mask": actual_checklist_mask,
        })
    return JsonResponse(response.serialize(), safe = False)