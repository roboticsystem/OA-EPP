from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
print('routes:', sorted({r.path for r in app.routes}))
resp = client.post('/api/auth/login', json={'identifier':'2025001','password':'2025001'})
print('status', resp.status_code)
print(resp.text)
