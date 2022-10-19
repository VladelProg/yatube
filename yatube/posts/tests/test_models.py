from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Временные файлы необходимые для тестов."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост длинной больше 15 символов',
        )

    def test_object_group_is_title_fild(self):
        """
        В поле __str__  объекта Group записано значение поля group.title .
        """
        self.assertEqual(self.group.title, str(self.group))

    def test_object_post_is_text_fild(self):
        """
        В поле __str__  объекта Post записано
        значение поля post.text нужной длины.
        """
        len_str_post = len(str(self.post))
        self.assertEqual(self.post.text[:len_str_post], str(self.post))
