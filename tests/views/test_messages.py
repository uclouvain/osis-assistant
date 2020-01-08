##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from assistant.models.enums import message_type
from assistant.models.manager import Manager
from assistant.models.message import Message
from assistant.views.messages import show_history
from base.models.person import Person
from base.tests.factories.academic_year import AcademicYearFactory

HTTP_OK = 200


class MessagesViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='tests', email='tests@uclouvain.be', password='secret'
        )
        cls.person = Person.objects.create(user=cls.user, first_name='first_name', last_name='last_name')
        cls.manager = Manager.objects.create(person=cls.person)
        cls.current_academic_year = AcademicYearFactory()
        Message.objects.create(
            sender=cls.manager,
            type=message_type.TO_ALL_ASSISTANTS,
            date=timezone.now(),
            academic_year=cls.current_academic_year
        )
        Message.objects.create(
            sender=cls.manager,
            type=message_type.TO_ALL_DEANS,
            date=timezone.now(),
            academic_year=cls.current_academic_year
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_messages_history_view_basic(self):
        response = self.client.get(reverse(show_history))
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertTemplateUsed(response, 'messages.html')

    def test_messages_history_view_returns_messages(self):
        response = self.client.get(reverse('messages_history'))
        messages = response.context['sent_messages']
        self.assertIs(type(messages), QuerySet)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].sender, self.manager)
        self.assertEqual(messages[1].type, message_type.TO_ALL_DEANS)
