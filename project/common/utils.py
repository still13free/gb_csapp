import json
from .variables import MAX_PACKAGE_LENGTH, ENCODING
from .errors import NonDictInputError, IncorrectDataReceivedError


def get_message(client):

    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise NonDictInputError
    raise IncorrectDataReceivedError


def send_message(sock, message):
    if not isinstance(message, dict):
        raise NonDictInputError
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)
