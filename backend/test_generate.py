import urllib.request, json
req = urllib.request.Request(
    'https://smart-campus-backend-fx5m.onrender.com/api/scheduler/generate/',
    data=json.dumps({}).encode('utf-8'),
    headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_TOKEN_HERE'
    },
    method='POST'
)
# We can't easily test the live server without a token, so let's test the local server instead.
