from django.contrib.auth.views import login as django_login

def login(request):
    return django_login(request=request, 
                        template_name="login.html",
                        extra_context=dict(next='/'),
                        )
