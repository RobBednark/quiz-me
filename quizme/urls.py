from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from django.urls import path

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

from emailusername.views import logout

from questions.views import answer, question, question_next

admin.autodiscover()

urlpatterns = [
    path(
        route='login/',
        view=auth_views.LoginView.as_view(template_name='questions/login.html'),
        name='login'),
    url(regex=r'^logout$', view=logout, name='logout'),

    url(regex=r'^$', view=question_next),
    url(regex=r'^question/$', view=question_next, name='question_next'),
    url(regex=r'^question/(?P<id_question>[0-9]*)/$', view=question, name='question'),
    url(regex=r'^answer/(?P<id_attempt>[0-9]*)/$', view=answer, name='answer'),

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
