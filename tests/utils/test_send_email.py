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
from django.test import TestCase

from assistant.models.enums import assistant_mandate_renewal
from assistant.models.enums import reviewer_role
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.manager import ManagerFactory
from assistant.tests.factories.reviewer import ReviewerFactory
from assistant.tests.factories.settings import SettingsFactory
from assistant.utils import send_email
from base.models.person import Person
from base.tests.factories.academic_year import AcademicYearFactory


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
        send_email.send_message(self.academic_assistant.person, html_template_ref, txt_template_ref)
        args = mock_send_messages.call_args[0][0]
        self.assertEqual(len(args.get('receivers')), 1)

    @patch("base.models.academic_year.current_academic_year")
    @patch("osis_common.messaging.send_message.send_messages")
    def test_with_one_phd_supervisor(self, mock_send_messages, mock_current_ac_year):
        mock_current_ac_year.return_value = self.current_academic_year
        html_template_ref = 'assistant_phd_supervisor_html'
        txt_template_ref = 'assistant_phd_supervisor_txt'
        send_email.send_message(self.phd_supervisor, html_template_ref, txt_template_ref)
        args = mock_send_messages.call_args[0][0]
        self.assertEqual(len(args.get('receivers')), 1)
