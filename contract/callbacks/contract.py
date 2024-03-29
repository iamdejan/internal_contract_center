from django.shortcuts import render

from contract.models import build_fail_response, build_success_response
from contract.models import SmartContract
from contract import constants

import pika
import requests
import json

NO_DATA_HASH = ''.join(["0" for i in range(128)])

contracts = {}

def init_all_contracts():
    global contracts
    db_contracts = SmartContract.objects.all()
    for contract in db_contracts:
        contracts[contract.contract_code] = contract
        pass
    pass

def init_queues(channel):
    global contracts
    for key in contracts:
        channel.queue_declare(key)
    pass

def popcount(number):
    popcounts = [0 for i in range(number + 1)]
    for i in range(number + 1):
        popcounts[i] = popcounts[i >> 1] + (i & 1 == 1)
    return popcounts[number]

def fire_API_call(sub_url, id, *args):
    URL = "http://localhost:"
    PORT = 8000
    url = "%s%d" % (URL, PORT)
    url += "/system/"
    url += sub_url
    url += "/"
    url += id
    for suffix in args:
        url += suffix
        pass

    response = requests.get(url = url)
    return response

def callback(channel, method, properties, body):
    init_all_contracts()
    init_queues(channel)

    response = fire_API_call("projects", body.decode())
    if response.status_code != 200:
        response = build_fail_response({
            "message": "Response is not success"
        })
        channel.basic_publish(
            "",
            routing_key = constants.FAILED,
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
            routing_key = constants.FAILED,
            body = json.dumps(response.serialize())
        )
        return

    data = response["data"]
    checklist_mask = int(data["checklist_mask"])

    success_contract = contracts[constants.SUCCESS]
    threshold = success_contract.threshold
    if popcount(checklist_mask) < threshold:
        response = build_fail_response({
            "message": "Approval below threshold"
        })
        channel.basic_publish(
            "",
            routing_key = constants.FAILED,
            body = json.dumps(response.serialize())
        )
        return

    actual_checklist_mask = 0
    current_hash = data["tail_hash"]
    while current_hash != NO_DATA_HASH:
        response = fire_API_call("approval", current_hash, "/validate")
        response = json.loads(response.content)
        if response["success"] != True:
            response = build_fail_response({
                "message": "Block is broken"
            })
            channel.basic_publish(
                "",
                routing_key = constants.FAILED,
                body = json.dumps(response.serialize())
            )
            return

        # query the hash
        response = fire_API_call("approval", current_hash)
        response = json.loads(response.content)
        data = response["data"]
        current_hash = data["previous_hash"]

        # query the employee to get the level
        response = fire_API_call("employees", str(data["employee_id"]))
        response = json.loads(response.content)
        data = response["data"]
        actual_checklist_mask |= (1 << (int(data["level_id"]) - 1))
        pass

    response = None
    expected_checklist_mask = checklist_mask
    if expected_checklist_mask == actual_checklist_mask:
        response = build_success_response({
            "message": "The chain is valid"
        })
        channel.basic_publish(
            "",
            routing_key = constants.SUCCESS,
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
            routing_key = constants.FAILED,
            body = json.dumps(response.serialize())
        )
    pass