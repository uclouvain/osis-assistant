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

from django.http import HttpResponse
from django.test import TestCase, RequestFactory, Client
from django.urls import reverse

from assistant.forms import assistant as assistant_forms
from assistant.models.enums import assistant_mandate_state
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.settings import SettingsFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory


class TestAssistantAdministrativeForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        SettingsFactory()
        cls.url = reverse("form_part1_edit")

    def setUp(self) -> None:
        self.assistant_mandate = AssistantMandateFactory(
            academic_year__current=True,
            state=assistant_mandate_state.TRTS
        )
        self.client.force_login(self.assistant_mandate.assistant.person.user)

    def test_get_request(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "assistant_form_part1.html")

        context = response.context
        self.assertEqual(context["assistant"], self.assistant_mandate.assistant)
        self.assertEqual(context["mandate"], self.assistant_mandate)
        self.assertIsInstance(context["form"], assistant_forms.AdministrativeInformationsForm)

    def test_post_request(self):
        response = self.client.post(self.url, data={
            "mandate_id": str(self.assistant_mandate.id),
            "external_functions": "This is a explanation"
        })

        self.assertTemplateUsed(response, "assistant_form_part1.html")

        self.assistant_mandate.refresh_from_db()
        self.assertEqual(self.assistant_mandate.external_functions, "This is a explanation")


class AssistantFormViewTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.settings = SettingsFactory()

        self.current_academic_year = AcademicYearFactory(current=True)

        self.assistant_mandate = AssistantMandateFactory(
            academic_year=self.current_academic_year,
            state=assistant_mandate_state.TRTS
        )
        LearningUnitYearFactory(academic_year=self.current_academic_year, acronym="LBIR1210")
        LearningUnitYearFactory(academic_year=self.current_academic_year, acronym="LBIR1211")

    def test_assistant_form_part4_edit_view_basic(self):
        self.client.force_login(self.assistant_mandate.assistant.person.user)
        response = self.client.get('/assistants/assistant/form/part4/edit/')
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_get_learning_units_year(self):
        self.client.force_login(self.assistant_mandate.assistant.person.user)
        response = self.client.generic(method='get',
                                       path='/assistants/assistant/form/part2/get_learning_units_year/?term=LBIR1211',
                                       HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data[0]['value'], 'LBIR1211')
        self.assertEqual(len(data), 1)
        response = self.client.generic(method='get',
                                       path='/assistants/assistant/form/part2/get_learning_units_year/?term=LBIR12',
                                       HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data), 2)
