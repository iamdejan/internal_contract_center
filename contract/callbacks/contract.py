from django.shortcuts import render

from contract.models import build_fail_response, build_success_response

import pika
import requests
import json

NO_DATA_HASH = ''.join(["0" for i in range(128)])

APPROVAL_SUCCESS = "APPROVAL_SUCCESS"
APPROVAL_FAILED = "APPROVAL_FAILED"

def _get_connection():
    parameters = pika.URLParameters("amqp://localhost")
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # TODO :change this into for-loop
    channel.queue_declare(APPROVAL_SUCCESS)
    channel.queue_declare(APPROVAL_FAILED)
    return (connection, channel)

def build_URL_PORT(sub_url, id):
    URL = "http://localhost:"
    PORT = 8000
    url = "%s%d" % (URL, PORT)
    url += "/system/"
    url += sub_url
    url += "/"
    url += id
    return url

def callback(ch, method, properties, body):
    connection, channel = _get_connection()

    url = build_URL_PORT("projects", body.decode())
    response = requests.get(url = url)
    if response.status_code != 200:
        response = build_fail_response({
            "message": "Response is not success"
        })
        # TODO: publish
        channel.basic_publish(
            "",
            routing_key = APPROVAL_FAILED,
            body = json.dumps(response.serialize())
        )
        connection.close()
        return
    response = json.loads(response.content)
    if response["success"] != True:
        response = build_fail_response({
            "message": "System is busy"
        })
        channel.basic_publish(
            "",
            routing_key = APPROVAL_FAILED,
            body = json.dumps(response.serialize())
        )
        connection.close()
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
                routing_key = APPROVAL_FAILED,
                body = json.dumps(response.serialize())
            )
            connection.close()
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
            routing_key = APPROVAL_SUCCESS,
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
            routing_key = APPROVAL_FAILED,
            body = json.dumps(response.serialize())
        )
    connection.close()