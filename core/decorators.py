from django.shortcuts import redirect


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            return redirect("login")

        if getattr(user, "rol", None) != "admin":
            return redirect("home")

        return view_func(request, *args, **kwargs)

    return wrapper


def login_required_custom(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)

        return redirect("login")

    return wrapper