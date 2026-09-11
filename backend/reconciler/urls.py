from django.urls import path

from .views import discrepancies, organizations


urlpatterns = [
    path(
        "organizations/",
        organizations,
        name="organizations",
    ),
    path(
        "discrepancies/",
        discrepancies,
        name="discrepancies",
    ),
]
