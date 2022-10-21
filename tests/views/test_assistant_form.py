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
import json
from typing import Dict

from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from assistant.models import academic_assistant
from assistant.models.enums import assistant_mandate_state, assistant_phd_inscription
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.settings import SettingsFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.tutor import TutorFactory


class AssistantFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.settings = SettingsFactory()

        cls.current_academic_year = AcademicYearFactory(current=True)

        cls.assistant_mandate = AssistantMandateFactory(
            academic_year=cls.current_academic_year,
            state=assistant_mandate_state.TRTS
        )
        LearningUnitYearFactory(academic_year=cls.current_academic_year, acronym="LBIR1210")
        LearningUnitYearFactory(academic_year=cls.current_academic_year, acronym="LBIR1211")

    def setUp(self):
        self.client.force_login(self.assistant_mandate.assistant.person.user)

    def test_assistant_form_part4_edit_view_basic(self):
        response = self.client.get('/assistants/assistant/form/part4/edit/')
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_get_learning_units_year(self):
        response = self.client.generic(method='get',
                                       path='/assistants/assistant/form/part2/get_learning_units_year/?q=LBIR1211',
                                       HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['results'][0]['text'][:8], 'LBIR1211')
        self.assertEqual(len(data['results']), 1)
        response = self.client.generic(method='get',
                                       path='/assistants/assistant/form/part2/get_learning_units_year/?q=LBIR12',
                                       HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data['results']), 2)


class PhDTabFormView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.settings = SettingsFactory()

        cls.current_academic_year = AcademicYearFactory(current=True)
        cls.tutor = TutorFactory()

        cls.get_url = reverse("form_part3_edit")
        cls.post_url = reverse("form_part3_save")

    def setUp(self) -> None:
        self.assistant_mandate = AssistantMandateFactory(
            academic_year=self.current_academic_year,
            state=assistant_mandate_state.TRTS
        )
        self.client.force_login(self.assistant_mandate.assistant.person.user)

    def test_template_used_for_get(self):
        response = self.client.get(self.get_url)

        self.assertTemplateUsed(response, "assistant_form_part3.html")

    def test_invalid_post_if_inscription_set_and_no_promoter_given(self):
        data = {
            "mand-thesis_title": "My thesis",
            "mand-remark": "This is my remark",
            "mand-inscription": assistant_phd_inscription.IN_PROGRESS,
        }

        response = self.client.post(self.post_url, data=data)
        self.assertFalse(response.context["form"].is_valid())

    def test_invalid_post_data_if_no_inscription_information_given(self):
        data = {
            "mand-thesis_title": "My thesis",
            "mand-remark": "This is my remark",
            "mand-supervisor": str(self.tutor.person.id)
        }

        response = self.client.post(self.post_url, data=data)
        self.assertFalse(response.context["form"].is_valid())

    def test_valid_post_data_if_no_inscription_to_phd_and_no_promoter_given(self):
        data = {
            "mand-thesis_title": "My thesis",
            "mand-remark": "This is my remark",
            "mand-inscription": assistant_phd_inscription.NO,
        }

        self.client.post(self.post_url, data=data)

        self.assert_assistant_mandate_equal_to_post_data(data)

    def test_valid_post_with_promoter_given(self):
        data = {
            "mand-thesis_title": "My thesis",
            "mand-remark": "This is my remark",
            "mand-inscription": assistant_phd_inscription.YES,
            "mand-supervisor": str(self.tutor.person.id)
        }

        self.client.post(self.post_url, data=data)

        self.assert_assistant_mandate_equal_to_post_data(data)

    def assert_assistant_mandate_equal_to_post_data(self, post_data: Dict):
        self.assistant_mandate.refresh_from_db()

        academic_assistant_obj = self.assistant_mandate.assistant  # type: academic_assistant.AcademicAssistant
        for field_name, field_value in post_data.items():
            cleaned_field_name = field_name.lstrip("mand-")
            if cleaned_field_name == "supervisor":
                self.assertEqual(str(academic_assistant_obj.supervisor.id), field_value, field_name)
            else:
                self.assertEqual(
                    getattr(academic_assistant_obj, cleaned_field_name),
                    field_value,
                    cleaned_field_name
                )
