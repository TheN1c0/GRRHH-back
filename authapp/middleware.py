from django.http import HttpResponse

class BlockScannerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.suspicious_paths = [
            "/.env", "/.git/", "/.ssh/", "/wp-admin/",
            "/config.yml", "/config.yaml", "/config.php",
            "/settings.py", "/database.sql", "/docker-compose.yml"
        ]

    def __call__(self, request):
        for path in self.suspicious_paths:
            if request.path.startswith(path):
                return HttpResponse(status=404)
        return self.get_response(request)
