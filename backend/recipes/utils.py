import uuid


def generate_short_link():
    return uuid.uuid4().hex
