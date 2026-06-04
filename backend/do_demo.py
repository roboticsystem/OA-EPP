import json, urllib.request, urllib.parse
BASE='http://127.0.0.1:8009'

def post(path, data, headers=None):
    url=BASE+path
    b=json.dumps(data).encode('utf-8')
    req=urllib.request.Request(url, data=b, headers={'Content-Type':'application/json'} if not headers else headers)
    with urllib.request.urlopen(req) as r:
        return r.read().decode()

# teacher login
print('Teacher login...')
res=post('/api/teacher/login', {'password':'admin123'})
print('login res', res)
obj=json.loads(res)
token=obj['token']
print('Teacher token:', token)

# add student
print('Adding student 2025001 张三...')
headers={'Content-Type':'application/json','Authorization':'Bearer '+token}
url=BASE+'/api/teacher/students/add'
data={'name':'张三','student_id':'2025001','class_name':'研一'}
req=urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
with urllib.request.urlopen(req) as r:
    print('add student res', r.read().decode())

# student login
print('Student login...')
res=post('/api/auth/login', {'account':'2025001','password':'2025001'})
print('student login res', res)
obj=json.loads(res)
print('student token:', obj.get('token'))
