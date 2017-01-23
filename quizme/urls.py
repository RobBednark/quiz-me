from django.conf.urls import include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

from emailusername.views import login, logout
from questions.views import answer, question, question_next

admin.autodiscover()

urlpatterns = [
    url(regex=r'^login$', view=login, name='login'),
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
