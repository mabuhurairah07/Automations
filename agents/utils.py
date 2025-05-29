import requests


def fire_and_forget(url, data):
    try:
        requests.post(url=url, json=data)
    except Exception as e:
        pass
