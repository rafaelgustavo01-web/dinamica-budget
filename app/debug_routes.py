import sys, os
sys.path.insert(0, '.')
from backend.main import create_app
app = create_app()
from starlette.routing import Match

test_uuid = '1a551def-b5e0-410e-b1a3-d1093175faca'
target = '/api/v1/propostas/' + test_uuid + '/items'

print("Testing path:", target)
print("---")
for i, route in enumerate(app.routes):
    scope = {'type': 'http', 'method': 'GET', 'path': target, 'root_path': '', 'query_string': b''}
    match, child = route.matches(scope)
    if match == Match.FULL:
        p = getattr(route, 'path', '?')
        m = getattr(route, 'methods', set())
        print('FIRST FULL match at [' + str(i) + ']: methods=' + str(m) + ' path=' + p)
        break

print("---")
# Also test /api/v1/propostas/UUID (detail - known to work)
target2 = '/api/v1/propostas/' + test_uuid
for i, route in enumerate(app.routes):
    scope = {'type': 'http', 'method': 'GET', 'path': target2, 'root_path': '', 'query_string': b''}
    match, child = route.matches(scope)
    if match == Match.FULL:
        p = getattr(route, 'path', '?')
        m = getattr(route, 'methods', set())
        print('FIRST FULL match (detail) at [' + str(i) + ']: methods=' + str(m) + ' path=' + p)
        break

print("---")
# Also show where BCU epi route falls
target3 = '/api/v1/propostas/' + test_uuid + '/items/bcu/epi'
for i, route in enumerate(app.routes):
    scope = {'type': 'http', 'method': 'GET', 'path': target3, 'root_path': '', 'query_string': b''}
    match, child = route.matches(scope)
    if match == Match.FULL:
        p = getattr(route, 'path', '?')
        m = getattr(route, 'methods', set())
        print('FIRST FULL match (bcu/epi) at [' + str(i) + ']: methods=' + str(m) + ' path=' + p)
        break
