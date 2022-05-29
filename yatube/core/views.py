from django.shortcuts import render


def page_not_found(request, exception):
    return render(
        request,
        '/Dev/hw05_final/yatube/core/templates/404.html',
        {'path': request.path},
        status=404,
    )


def server_error(request):
    return render(
        request,
        '/Dev/hw05_final/yatube/core/templates/500.html',
        status=500,
    )


def permission_denied(request, exception):
    return render(
        request,
        '/Dev/hw05_final/yatube/core/templates/403.html',
        status=403,
    )


def csrf_failure(request, reason=''):
    return render(
        request,
        '/Dev/hw05_final/yatube/core/templates/403csrf.html',
    )
