from django.core.paginator import Paginator

PAGE_NUM = 10


def block_paginator(object, request):
    """Унифирсальная часть кода для пагинатора"""
    paginator = Paginator(object, PAGE_NUM)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
