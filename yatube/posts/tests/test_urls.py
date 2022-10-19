from http import HTTPStatus

from django.test import Client, TestCase

from ..models import Group, Post, User


class PostUrlsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Временные файлы необходимые для тестов."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_2 = User.objects.create_user(username='not_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            pub_date='Тестовая дата',
            group=cls.group,
        )

    def setUp(self):
        """Пользователи для тестирования."""
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)

    def test_urls_uses_correct_template(self):
        """Доступ любого пользователя к страницам приложения."""
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{self.group.slug}/',
            'posts/profile.html': f'/profile/{self.user.username}/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
        }
        for address in templates_url_names.values():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, HTTPStatus.OK)

    def test_post_create_url_exists_at_desired_location(self):
        """Страница '/create/' доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_desired_location(self):
        """Страница /posts/<post_id>/edit/
        доступна автору поста.
        """
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_add_comment_url_exists_at_desired_location(self):
        """Страница /posts/<int:post_id>/comment/
        доступна автору поста.
        """
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/comment/'
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_edit_url_redirect_guest_client(self):
        """Страница /posts/{self.post.id}/edit/
        перенаправляет анонимного пользователя.
        """
        response = self.guest_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_edit_url_redirect_authorized_client_not_author(self):
        """Страница /posts/{self.post.id}/edit/
        перенаправляет не автора поста
        """
        response = self.authorized_client_2.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_create_url_redirect_anonymous(self):
        """Страница /create/ перенаправляет анонимного
        пользователя.
        """
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/post_create.html',
            f'/posts/{self.post.id}/edit/': 'posts/post_create.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_guest_client_not_add_comment(self):
        """
        Анонимный пользователь не может оставлять комментарии
        под постом.
        """
        response = self.guest_client.get(f'/posts/{self.post.id}/comment/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
