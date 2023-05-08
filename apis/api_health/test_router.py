# API Root Path
api_root_path = "/api/ssot/latest/health"

def test_health_no_auth(client_noauth):
    response = client_noauth.get(f"{api_root_path}")
    assert response.status_code == 200