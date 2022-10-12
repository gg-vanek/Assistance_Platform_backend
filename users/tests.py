from django.test import TestCase
from .models import CustomUser


class UserTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a user
        testuser1 = CustomUser.objects.create_user(
            username='testuser1', email='testuser1@etest.com',
            password='abc123', first_name='Alex',
            last_name='Brown', age=18, stage_of_study='M', years_of_study=5)

        testuser1.save()

    def test_blog_content(self):
        # username = 'testuser1'
        # email = 'testuser1@etest.com'
        # first_name = 'Alex'
        # last_name = 'Brown'
        # age = 18
        # stage_of_study = 'M'
        # course_of_study= 5

        user = CustomUser.objects.get(id=1)

        username = f'{user.username}'
        email = f'{user.email}'
        first_name = f'{user.first_name}'
        last_name = f'{user.last_name}'
        age = f'{user.age}'
        stage_of_study = f'{user.stage_of_study}'
        years_of_study = f'{user.course_of_study}'

        self.assertEqual(username, 'testuser1')
        self.assertEqual(email, 'testuser1@etest.com')
        self.assertEqual(first_name, 'Alex')
        self.assertEqual(last_name, 'Brown')
        self.assertEqual(age, '18')
        self.assertEqual(stage_of_study, 'M')
        self.assertEqual(years_of_study, '5')
