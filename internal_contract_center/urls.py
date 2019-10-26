from django.urls import path

from contract.views import contract

urlpatterns = [
    path("projects/<int:project_id>/validate", contract.validate, name = "validate"),
]
