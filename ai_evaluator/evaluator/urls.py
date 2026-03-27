from django.urls import path
from .views import home, evaluate 
urlpatterns = [ path('', home),
    path('evaluate/', evaluate),
]