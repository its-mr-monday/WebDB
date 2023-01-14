import requests

class WebDBException(Exception):
    pass

class WebDB:
    def __init__(self, server: str, username: str, password: str, port=5555):
        self.api_route = f"http://{server}:{port}/webdb/api/v1.0"
        self.token = None
        self.user = None
        self.isLoggedIn = False
        self.login(username, password)
        
    def login(self, username: str, password: str):
        data = {"username": username, "password": password}
        r = requests.post(self.api_route + "/login", json=data)
        if r.status_code == 200:
            self.user = username
            self.token = r.json()["token"]
            self.isLoggedIn = True
            return
        raise WebDBException(r.json()["error"])
    
    def logout(self):
        self.token = None
        self.user = None
        self.isLoggedIn = False
    
    def databases(self):
        if not self.isLoggedIn:
            raise WebDBException("Not logged in")
        
        r = requests.get(self.api_route + "/databases", headers={"Authorization": "Bearer " + self.token})
        if r.status_code == 200:
            return r.json()["databases"]
        
        self.logout()
        raise WebDBException(r.json()["error"])
    
    