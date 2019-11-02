from django.shortcuts import render

from contract.models import build_fail_response, build_success_response
from contract import constants

import pika
import requests
import json

NO_DATA_HASH = ''.join(["0" for i in range(128)])

contracts = {}

def build_URL_PORT(sub_url, id):
    URL = "http://localhost:"
    PORT = 8000
    url = "%s%d" % (URL, PORT)
    url += "/system/"
    url += sub_url
    url += "/"
    url += id
    return url

def init_all_contracts():
    global contracts
    # TODO: get all contracts from DB
    # for this time, we will mock
    contracts[constants.SUCCESS] = "APPROVAL_SUCCESS"
    contracts[constants.FAILED] = "APPROVAL_FAILED"
    pass

def init_queues(channel):
    global contracts
    for key in contracts:
        channel.queue_declare(contracts[key])
    pass

def callback(channel, method, properties, body):
    init_all_contracts()
    init_queues(channel)

    url = build_URL_PORT("projects", body.decode())
    response = requests.get(url = url)
    if response.status_code != 200:
        response = build_fail_response({
            "message": "Response is not success"
        })
        channel.basic_publish(
            "",
            routing_key = contracts[constants.FAILED],
            body = json.dumps(response.serialize())
        )
        return
    response = json.loads(response.content)
    if response["success"] != True:
        response = build_fail_response({
            "message": "System is busy"
        })
        channel.basic_publish(
            "",
            routing_key = contracts[constants.FAILED],
            body = json.dumps(response.serialize())
        )
        return

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
            channel.basic_publish(
                "",
                routing_key = contracts[constants.FAILED],
                body = json.dumps(response.serialize())
            )
            return

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
        channel.basic_publish(
            "",
            routing_key = contracts[constants.SUCCESS],
            body = json.dumps(response.serialize())
        )
    else:
        response = build_fail_response({
            "message": "The chain is broken",
            "expected_checklist_mask": expected_checklist_mask,
            "actual_checklist_mask": actual_checklist_mask,
        })
        channel.basic_publish(
            "",
            routing_key = contracts[constants.FAILED],
            body = json.dumps(response.serialize())
        )
    pass