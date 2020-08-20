from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from django.urls import path

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

import emailusername.views as emailusername_views

import questions.views as question_views

admin.autodiscover()

urlpatterns = [
    path(
        route='login/',
        view=auth_views.LoginView.as_view(template_name='questions/login.html'),
        name='login'),
    url(regex=r'^logout$', view=emailusername_views.logout, name='logout'),
    url(regex=r'^$', view=question_views.flashcard),
    url(regex=r'^flashcard/$', view=question_views.flashcard, name='flashcard'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', admin.site.urls),
]

if settings.ENABLE_DJANGO_DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
