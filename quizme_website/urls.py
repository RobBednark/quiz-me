from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^login$', 'emailusername.views.login', name='login'),
    url(r'^logout$', 'emailusername.views.logout', name='logout'),

    url(r'^$', 'questions.views.question_next'),
    url(r'^/$', 'questions.views.question_next'),
    url(r'^question/$', 'questions.views.question_next', name='question_next'),
    url(r'^question/(?P<id_question>[0-9]*)/$', 'questions.views.question', name='question_new'),
    url(r'^answer/(?P<id_attempt>[0-9]*)/$', 'questions.views.answer', name='answer'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
