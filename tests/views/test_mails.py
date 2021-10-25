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
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

import assistant.views.mails
from assistant.models.enums import assistant_mandate_renewal
from assistant.models.enums import message_type
from assistant.models.enums import reviewer_role
from assistant.models.manager import Manager
from assistant.models.message import Message
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.manager import ManagerFactory
from assistant.tests.factories.reviewer import ReviewerFactory
from assistant.tests.factories.settings import SettingsFactory
from assistant.views.mails import show_history
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


class SendEmailTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_assistant = AcademicAssistantFactory()
        cls.manager = ManagerFactory()
        cls.current_academic_year = AcademicYearFactory()
        cls.assistant_mandate = AssistantMandateFactory(assistant=cls.academic_assistant)
        cls.user = User.objects.create_user(
            username='phd_supervisor', email='phd_supervisor@uclouvain.be', password='phd_supervisor'
        )
        cls.user.save()
        cls.phd_supervisor = Person.objects.create(user=cls.user, first_name='phd', last_name='supervisor')
        cls.phd_supervisor.save()
        cls.academic_assistant.supervisor = cls.phd_supervisor
        cls.academic_assistant.save()
        cls.settings = SettingsFactory()
        cls.reviewer = ReviewerFactory(role=reviewer_role.SUPERVISION)

    def setUp(self):
        self.client.login(username=self.manager.person.user.username, password=self.manager.person.user.password)

    @patch("base.models.academic_year.current_academic_year")
    @patch("osis_common.messaging.send_message.send_messages")
    def test_with_one_assistant(self, mock_send_messages, mock_current_ac_year):
        mock_current_ac_year.return_value = self.current_academic_year
        if self.assistant_mandate.renewal_type == assistant_mandate_renewal.NORMAL \
                or self.assistant_mandate.renewal_type == assistant_mandate_renewal.SPECIAL:
            html_template_ref = 'assistant_assistants_startup_normal_renewal_html'
            txt_template_ref = 'assistant_assistants_startup_normal_renewal_txt'
        else:
            html_template_ref = 'assistant_assistants_startup_except_renewal_html'
            txt_template_ref = 'assistant_assistants_startup_except_renewal_txt'
        assistant.views.mails.send_message(self.academic_assistant.person, html_template_ref, txt_template_ref)
        args = mock_send_messages.call_args[0][0]
        self.assertEqual(len(args.get('receivers')), 1)

    @patch("base.models.academic_year.current_academic_year")
    @patch("osis_common.messaging.send_message.send_messages")
    def test_with_one_phd_supervisor(self, mock_send_messages, mock_current_ac_year):
        mock_current_ac_year.return_value = self.current_academic_year
        html_template_ref = 'assistant_phd_supervisor_html'
        txt_template_ref = 'assistant_phd_supervisor_txt'
        assistant.views.mails.send_message(self.phd_supervisor, html_template_ref, txt_template_ref)
        args = mock_send_messages.call_args[0][0]
        self.assertEqual(len(args.get('receivers')), 1)
