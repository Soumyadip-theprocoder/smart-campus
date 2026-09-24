import urllib.request, json, urllib.error
req = urllib.request.Request(
    'https://smart-campus-backend-fx5m.onrender.com/api/auth/login/',
    data=json.dumps({'email':'alice.brown@smartcampus.edu', 'password':'student123'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
try:
    res = urllib.request.urlopen(req)
    print(f'Status: {res.status}')
    print(res.headers)
    print(res.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f'HTTPError: {e.code}')
    print(e.headers)
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f'Error: {e}')
