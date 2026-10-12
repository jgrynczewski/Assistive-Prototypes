# -*- coding: utf-8 -*-

import urllib2
import json
import time
import logging
import os

BASE_URL = 'http://localhost:8765/api/v1'
TIMEOUT = 10

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'iot.log')

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
_log = logging.getLogger('iot')


def _get(path):
    url = BASE_URL + path
    _log.info('REQUEST GET %s', url)
    try:
        response = urllib2.urlopen(url, timeout=TIMEOUT)
        data = json.loads(response.read())
        _log.info('RESPONSE GET %s -> %s', url, json.dumps(data))
        return data
    except Exception as e:
        _log.error('ERROR GET %s -> %s', url, e)
        return None


def _post(path, data=None):
    url = BASE_URL + path
    body = json.dumps(data) if data is not None else '{}'
    _log.info('REQUEST POST %s body=%s', url, body)
    try:
        req = urllib2.Request(url, body, {'Content-Type': 'application/json'})
        response = urllib2.urlopen(req, timeout=TIMEOUT)
        result = json.loads(response.read())
        _log.info('RESPONSE POST %s -> %s', url, json.dumps(result))
        return result
    except Exception as e:
        _log.error('ERROR POST %s -> %s', url, e)
        return None


def _put(path, data):
    url = BASE_URL + path
    body = json.dumps(data)
    for attempt in range(1, 4):
        _log.info('REQUEST PUT %s body=%s attempt=%d', url, body, attempt)
        try:
            req = urllib2.Request(url, body, {'Content-Type': 'application/json'})
            req.get_method = lambda: 'PUT'
            response = urllib2.urlopen(req, timeout=TIMEOUT)
            result = json.loads(response.read())
            _log.info('RESPONSE PUT %s -> %s', url, json.dumps(result))
            return result
        except urllib2.HTTPError as e:
            _log.error('ERROR PUT %s attempt=%d -> %s', url, attempt, e)
            if e.code != 500:
                return None
            if attempt < 3:
                _log.info('RETRY PUT %s in 1s (attempt %d/3)', url, attempt)
                time.sleep(1)
        except Exception as e:
            _log.error('ERROR PUT %s attempt=%d -> %s', url, attempt, e)
            return None
    return None


def discover_devices():
    url = BASE_URL + '/devices/discover'
    body = '{}'
    _log.info('REQUEST POST %s (discovery, timeout=30s)', url)
    try:
        req = urllib2.Request(url, body, {'Content-Type': 'application/json'})
        response = urllib2.urlopen(req, timeout=30)
        result = json.loads(response.read())
        _log.info('RESPONSE POST %s -> %s', url, json.dumps(result))
        return result
    except Exception as e:
        _log.error('ERROR POST %s -> %s', url, e)
        return None


def get_devices():
    return _get('/devices')


def get_capabilities(device_id):
    return _get('/devices/' + str(device_id) + '/capabilities')


def control_device(device_id, prop, value):
    return _put('/devices/' + str(device_id) + '/control', {'properties': {prop: value}})


def device_effect(device_id, effect):
    return _post('/devices/' + str(device_id) + '/effect', {'effect_name': effect})


def stop_effect(device_id):
    return _post('/devices/' + str(device_id) + '/effect/stop')


def reset_device(device_id):
    _post('/devices/' + str(device_id) + '/effect/stop')
    return _put('/devices/' + str(device_id) + '/control', {'properties': {'power': 'on', 'brightness': 100, 'temperature': 'warm'}})
