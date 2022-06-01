from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import Follow, Group, Post, User
from .forms import PostForm, CommentForm
from .utils import block_paginator


def index(request):
    """Общая страница"""
    posts = Post.objects.select_related('group', 'author').all()
    page_obj = block_paginator(posts, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Список постов группы"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    page_obj = block_paginator(posts, request)
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Посты принадлежащие автору"""
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('group', 'author').all()
    page_obj = block_paginator(posts, request)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            author=author,
            user=request.user).exists()
    else:
        following = False
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


@login_required
def follow_index(request):
    """Информация о подписках пользователя"""
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = block_paginator(posts, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора"""
    follow_author = get_object_or_404(User, username=username)
    if request.user != follow_author:
        Follow.objects.get_or_create(
            author=follow_author,
            user=request.user,
        )
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    """отписаться от автора"""
    follow_author = get_object_or_404(User, username=username)
    follow = Follow.objects.get(
        author=follow_author,
        user=request.user,
    )
    if request.user != follow_author:
        if Follow.objects.filter(
            author=follow_author,
            user=request.user,
        ).exists():
            follow.delete()
    return redirect('posts:follow_index')


def post_detail(request, post_id):
    """Деталировка поста"""
    post = get_object_or_404(
        Post.objects.select_related('author'), pk=post_id
    )
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создать новый пост"""
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Редактирование поста"""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    is_edit = True
    form = PostForm(
        request.POST or None,
        instance=post,
        files=request.FILES or None
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {'form': form, 'post': post, 'is_edit': is_edit}
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)
