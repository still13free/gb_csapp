class IncorrectDataReceivedError(Exception):
    def __str__(self):
        return 'Incorrect data received from remote computer'


class NonDictInputError(Exception):
    def __str__(self):
        return 'Function argument must be a dict'


class RequiredFieldMissingError(Exception):
    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'Received dict is missing a required field: {self.missing_field}'


class ServerError(Exception):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text
