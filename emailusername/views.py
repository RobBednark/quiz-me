from django.contrib.auth.views import (login as django_login,
                                       logout_then_login)


def login(request):
    response = django_login(request=request,
                            template_name="login.html",
                            extra_context=dict(next='/'),
                            )
    return response


def logout(request):
    # By default, will go to settings.LOGIN_URL
    return logout_then_login(request=request)
