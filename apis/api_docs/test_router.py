# API Root Path
api_root_path = "/api/ssot/latest"

def test_no_auth_fails(client_noauth):
    response = client_noauth.get(f"{api_root_path}/docs")
    assert response.status_code == 401

def test_docs(client_read):
    response = client_read.get(f"{api_root_path}/docs")
    assert response.status_code == 200

def test_openapi_spec(client_read):
    response = client_read.get(f"{api_root_path}/openapi.json")
    data = response.json()
    assert response.status_code == 200