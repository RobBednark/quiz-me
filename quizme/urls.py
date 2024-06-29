from django.conf import settings
from django.conf.urls import include
from django.contrib.auth import views as auth_views
from django.urls import path, re_path

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
    re_path(route=r'^logout$', view=emailusername_views.logout, name='logout'),
    re_path(route=r'^$', view=question_views.view_select_tags),
    re_path(route=r'^question/$', view=question_views.view_question, name='question'),
    re_path(route=r'^select-tags/$', view=question_views.view_select_tags, name='select_tags'),

    # Uncomment the admin/doc line below to enable admin documentation:
    re_path(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    re_path(r'^admin/', admin.site.urls),
]

if settings.ENABLE_DJANGO_DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
