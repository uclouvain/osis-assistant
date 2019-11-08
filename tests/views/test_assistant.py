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
from django import urls
from django.test import TestCase

from assistant.models.enums import assistant_mandate_state
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.settings import SettingsFactory
from base.tests.factories.academic_year import AcademicYearFactory


class TestAssistantListView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.open_settings = SettingsFactory()
        cls.previous_acy, cls.current_acy, cls.next_acy = AcademicYearFactory.produce()
        cls.academic_assistant = AcademicAssistantFactory()

        cls.assistant_mandate = AssistantMandateFactory(assistant=cls.academic_assistant, academic_year=cls.current_acy)

        cls.url = urls.reverse('assistant_mandates')

    def setUp(self) -> None:
        self.client.force_login(self.academic_assistant.person.user)

    def test_should_show_mandate_for_current_year(self):
        response = self.client.get(self.url)

        self.assertQuerysetEqual(
            response.context["assistant_mandates_list"],
            [self.assistant_mandate],
            transform=lambda obj: obj
        )

        self.assertEqual(response.context["assistant"], self.academic_assistant)
        self.assertEqual(response.context["current_academic_year"], self.current_acy)
        self.assertTrue(response.context["can_see_file"])

    def test_should_show_past_completed_mandates(self):
        past_completed_mandate = AssistantMandateFactory(
            assistant=self.academic_assistant,
            academic_year=self.previous_acy,
            state=assistant_mandate_state.DONE
        )

        response = self.client.get(self.url)

        self.assertQuerysetEqual(
            response.context["assistant_mandates_list"],
            [past_completed_mandate, self.assistant_mandate],
            transform=lambda obj: obj
        )

    def test_should_show_past_started_mandates(self):
        past_to_do_mandate = AssistantMandateFactory(
            assistant=self.academic_assistant,
            academic_year=self.previous_acy,
            state=assistant_mandate_state.TO_DO
        )

        response = self.client.get(self.url)

        self.assertQuerysetEqual(
            response.context["assistant_mandates_list"],
            [past_to_do_mandate, self.assistant_mandate],
            transform=lambda obj: obj
        )
