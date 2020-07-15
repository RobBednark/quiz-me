from django.contrib.auth.views import (LoginView,
                                       logout_then_login)


def login(request):
    response = LoginView.as_view(
                            template_name="login.html",
                            extra_context=dict(next='/'),
                            )
    return response


def logout(request):
    # By default, will go to settings.LOGIN_URL
    return logout_then_login(request=request)
