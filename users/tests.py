from django.test import TestCase
from .models import User


class UserTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a user
        testuser1 = User.objects.create_user(
            username='testuser1', email='testuser1@etest.com',
            password='abc123', first_name='Alex',
            last_name='Brown', stage_of_study='M', years_of_study=5,
            contact_phone='+78888888888', contact_email='testusercontact1@etest.com')

        testuser1.save()

    def test_blog_content(self):
        # username = 'testuser1'
        # email = 'testuser1@etest.com'
        # first_name = 'Alex'
        # last_name = 'Brown'
        # stage_of_study = 'M'
        # course_of_study= 5
        # contact_phone = '+78888888888'
        # contact_email = 'testusercontact1@etest.com'

        user = User.objects.get(id=1)

        username = f'{user.username}'
        email = f'{user.email}'
        first_name = f'{user.first_name}'
        last_name = f'{user.last_name}'
        stage_of_study = f'{user.stage_of_study}'
        years_of_study = f'{user.course_of_study}'
        contact_phone = f'{user.contact_phone}'
        contact_email = f'{user.contact_email}'

        self.assertEqual(username, 'testuser1')
        self.assertEqual(email, 'testuser1@etest.com')
        self.assertEqual(first_name, 'Alex')
        self.assertEqual(last_name, 'Brown')

        self.assertEqual(stage_of_study, 'M')
        self.assertEqual(years_of_study, '5')
        self.assertEqual(contact_phone, '+78888888888')
        self.assertEqual(contact_email, 'testusercontact1@etest.com')
