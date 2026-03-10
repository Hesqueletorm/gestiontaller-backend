import sys
import os
import requests
import time

# URL base del backend
BASE_URL = "http://localhost:8000/api/v1"

def test_config_persistence():
    try:
        import time
        import random
        # 0. Register new user
        username = f"testuser_{random.randint(10000,99999)}"
        email = f"{username}@example.com"
        password = "password123"
        
        print(f"0. Registering user {username}...")
        reg_resp = requests.post(f"{BASE_URL}/login/register", json={
            "usuario": username,
            "email": email,
            "password": password,
            "nombre": "Test User"
        })
        
        if reg_resp.status_code not in [200, 201]:
             print(f"Registration failed: {reg_resp.text}. Trying login directly...")
        
        # 1. Login
        print(f"1. Logging in as {username}...")
        resp = requests.post(f"{BASE_URL}/login/access-token", data={"username": username, "password": password})
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            return

        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get current config
        print("2. Getting current config...")
        resp = requests.get(f"{BASE_URL}/config/me", headers=headers)
        if resp.status_code != 200:
             print(f"Get config failed: {resp.text}")
             return
        config = resp.json()
        print(f"Current nombre_lubricentro: {config.get('nombre_lubricentro')}")
        
        # 3. Update config
        import random
        new_name = f"Lubricentro Test {random.randint(1000, 9999)}"
        print(f"3. Updating name to: {new_name}")
        resp = requests.put(f"{BASE_URL}/config/me", json={"nombre_lubricentro": new_name}, headers=headers)
        if resp.status_code != 200:
            print(f"Update failed: {resp.text}")
            return
            
        # 4. Get config again to verify update
        print("4. Verifying immediate update...")
        resp = requests.get(f"{BASE_URL}/config/me", headers=headers)
        config = resp.json()
        saved_name = config.get('nombre_lubricentro')
        print(f"Read name: {saved_name}")
        
        if saved_name == new_name:
            print("SUCCESS: Config updated correctly in Backend.")
        else:
            print("FAILURE: Config did NOT update in Backend.")

    except Exception as e:
        print(f"Connection error: {e}")
        print("Ensure backend is running on http://localhost:8000")

if __name__ == "__main__":
    test_config_persistence()
