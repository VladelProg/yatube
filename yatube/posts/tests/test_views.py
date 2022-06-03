import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms

from ..models import Group, Post, Comment, Follow, User
from ..utils import PAGE_NUM as PAGE_NUM

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.user_2 = User.objects.create_user(username='auth_2')
        cls.user_3 = User.objects.create_user(username='auth_3')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            author=cls.user_2,
            post=cls.post,
            text='Тестовый комментарий',
        )
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)
        self.authorized_client_3 = Client()
        self.authorized_client_3.force_login(self.user_3)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': 'auth'}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_page_show_correct_context(self):
        """Шаблоны index, group_list, profile
        сформирован с правильным контекстом.
        """
        reverse_names = {
            reverse('posts:index'): 'page_obj',
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug
            }): 'page_obj',
            reverse('posts:profile', kwargs={
                'username': self.user.username
            }): 'page_obj',
        }
        for reverse_name, value in reverse_names.items():
            response = self.authorized_client.get(reverse_name)
            self.assertEqual(
                response.context[value][0].text,
                self.post.text,
            )
            self.assertEqual(
                response.context[value][0].group,
                self.post.group,
            )
            self.assertEqual(
                response.context[value][0].author,
                self.post.author,
            )
            self.assertEqual(
                response.context[value][0].image,
                self.post.image,
            )

    def test_post_detail_page_show_correct_context(self):
        """
        Словарь шаблона post_detail сформирован
        с правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context['post'].author, self.post.author)
        self.assertEqual(response.context['post'].group, self.post.group)
        self.assertEqual(response.context['post'].text, self.post.text)
        self.assertEqual(response.context['post'].image, self.post.image)
        self.assertEqual(len(response.context['comments']), 1)

    def test_post_create_page_show_correct_context(self):
        """Шаблона post_create сформирован с правильным контекстом.
        """
        response = self.authorized_client.get(reverse('posts:post_create'))
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблона post_edit сформирован с правильным контекстом.
        """
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_new_post_is_not_in_wrong_list(self):
        """Проверяем, что новый пост не попал в другую группу
        """
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_2.slug}))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_pages_uses_correct_template(self):
        """Тестируем наличие нового поста с выбранной группой
        на 3 страницах (index, group_list, profile)
        """
        reverse_names = {
            reverse('posts:index'): 'page_obj',
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}): 'page_obj',
            reverse('posts:profile', kwargs={
                'username': self.user.username}): 'page_obj',
        }
        for reverse_name, page_obj in reverse_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    response.context[page_obj][0].group,
                    self.post.group,
                )

    def test_index_cache(self):
        """Проверяем что механизм кеширования главной страницы
        """
        response_1 = self.authorized_client.get(reverse('posts:index'))
        Post.objects.create(
            author=self.user,
            text='Тестовый пост для кэша',
            group=self.group,
        )
        response_2 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response_1.content, response_3.content)

    def test_follow_create(self):
        """
        Авторизованный пользователь может подписываться
        на других пользователей
        """
        count = Follow.objects.count()
        self.authorized_client_2.get(
            reverse('posts:profile_follow', kwargs={
                'username': self.user.username})
        )
        count_follow = Follow.objects.count()
        self.assertEqual(count, count_follow - 1)

    def test_follow_delete(self):
        """
        Авторизованный пользователь может отписываться
        на других пользователей
        """
        count = Follow.objects.count()
        Follow.objects.create(
            author=self.user,
            user=self.user_2,
        )
        self.authorized_client_2.get(
            reverse('posts:profile_unfollow', kwargs={
                'username': self.user.username})
        )
        count_unfollow = Follow.objects.count()
        self.assertEqual(count, count_unfollow)

    def test_in_follow_index_new_posts_in_follower_index(self):
        """
        Новая запись пользователя появляется в ленте тех,
        кто на него подписан
        """
        Follow.objects.create(
            author=self.user,
            user=self.user_2,
        )
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        count_index = len(response.context['page_obj'])
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост для follow',
        )
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        count_index_2 = len(response.context['page_obj'])
        self.assertEqual(count_index, count_index_2 - 1)

    def test_in_follow_index_new_posts_in_not_follower_index(self):
        """
        Новая запись автора не появляется в ленте тех,
        кто на него не подписан
        """
        Follow.objects.create(
            author=self.user,
            user=self.user_2,
        )
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        count_index = len(response.context['page_obj'])
        self.post = Post.objects.create(
            author=self.user_3,
            text='Тестовый пост 2 для follow',
        )
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        count_index_2 = len(response.context['page_obj'])
        self.assertEqual(count_index, count_index_2)

    def test_authorized_client_add_comment(self):
        """
        Авторизованный пользователь может оставлять комметарии
        """
        count = Comment.objects.count()
        form_data = {'text': 'Тестовый комент'}
        self.authorized_client_2.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), count + 1)

    def test_guest_client_not_add_comment(self):
        """
        Не авторизованный пользователь не может оставлять комметарии
        """
        count = Comment.objects.count()
        form_data = {'text': 'Тестовый комент'}
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), count)


class PostViewsPaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа 4',
            slug='4',
            description='Тестовое описание 4',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.paginator = Post.objects.bulk_create(
            [Post(
                text=cls.post.text,
                author=cls.post.author,
                group=cls.post.group,) for _ in range(PAGE_NUM)])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Тестируем сразу 3 страницы (index, group_list, profile)
        пагинатора на 10 постов.
        """
        paginator_pages = {
            reverse('posts:index'): 'page_obj',
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug
            }): 'page_obj',
            reverse('posts:profile', kwargs={
                'username': self.user.username
            }): 'page_obj',
        }
        for reverse_name, page_obj in paginator_pages.items():
            response = self.authorized_client.get(reverse_name)
            self.assertEqual(len(response.context[page_obj]), PAGE_NUM)

    def test_second_page_contains_tree_records(self):
        """Тестируем сразу 3 страницы
        (index, group_list, profile)
        пагинатора на 2-ой странице
        """
        paginator_pages = {
            reverse('posts:index'): 'page_obj',
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug
            }): 'page_obj',
            reverse('posts:profile', kwargs={
                'username': self.user.username
            }): 'page_obj',
        }
        for reverse_name, page_obj in paginator_pages.items():
            count = Post.objects.count()
            response = self.authorized_client.get(reverse_name, {'page': 2})
            self.assertEqual(len(response.context[page_obj]), count - PAGE_NUM)
