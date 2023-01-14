namespace WebDB;

public class WebDB {

    private string api_route;
    private string? token = null;
    private string? user = null;

    public WebDB(string server, string username, string password, int port = 5555) {
        this.api_route = $"http://{server}:{port}/webdb/api/v1.0";
    }

    public void Login(string username, string password) {
        string data = $"{{\"username\": \"{username}\", \"password\": \"{password}\"}}";

    }
    
}