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
import datetime

from django.test import TestCase
from django.urls import reverse

from assistant.models.enums import assistant_mandate_state
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.manager import ManagerFactory
from assistant.tests.factories.settings import SettingsFactory
from base.tests.factories.academic_year import AcademicYearFactory

HTTP_OK = 200
HTTP_FOUND = 302


class ManagerAssistantForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.settings = SettingsFactory()
        today = datetime.date.today()
        cls.manager = ManagerFactory()
        cls.assistant = AcademicAssistantFactory()
        cls.current_academic_year = AcademicYearFactory(start_date=today,
                                                        end_date=today.replace(year=today.year + 1),
                                                        year=today.year)
        cls.assistant_mandate = AssistantMandateFactory(academic_year=cls.current_academic_year,
                                                        state=assistant_mandate_state.RESEARCH)

    def test_assistant_form_view(self):
        self.client.force_login(self.manager.person.user)
        response = self.client.get(reverse("manager_assistant_form_view", args=[self.assistant_mandate.id]))
        self.assertEqual(response.status_code, HTTP_OK)

    def test_user_is_not_manager(self):
        self.client.force_login(self.assistant.person.user)
        response = self.client.get(reverse("manager_assistant_form_view", args=[self.assistant_mandate.id]))
        self.assertEqual(response.status_code, HTTP_FOUND)
