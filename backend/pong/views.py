"""Views for serving the Pong game frontend."""
from django.shortcuts import render


def index(request):
    """Serve the main game page."""
    return render(request, 'index.html')
