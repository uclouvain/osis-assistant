############################################################################
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
############################################################################
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.manager import ManagerFactory
from assistant.views import mandates_list
from base.tests.factories.academic_year import AcademicYearFactory


class TestMandatesListView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.past_acy, cls.current_acy, cls.next_acy = AcademicYearFactory.produce()

        cls.mandates = AssistantMandateFactory.create_batch(5, academic_year=cls.current_acy)
        cls.past_mandates = AssistantMandateFactory.create_batch(3, academic_year=cls.past_acy)

        cls.manager = ManagerFactory()
        cls.url = reverse("mandates_list")

    def setUp(self) -> None:
        self.client.force_login(self.manager.person.user)

    def test_should_return_mandates_of_current_academic_year_by_default(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "mandates_list.html")

        context = response.context
        self.assertCountEqual(list(context["object_list"]), self.mandates)
        self.assertEqual(context["year"], self.current_acy.year)

    def test_should_return_mandates_of_selected_academic_year(self):
        response = self.client.get(self.url, data={"academic_year": self.past_acy.id})

        context = response.context
        self.assertCountEqual(list(context["object_list"]), self.past_mandates)
        self.assertEqual(context["year"], self.past_acy.year)

    def test_should_return_mandates_of_academic_year_in_session(self):
        self.client.session[mandates_list.SELECTED_ACADEMIC_YEAR_KEY_SESSION] = self.past_acy.id
        response = self.client.get(self.url, data={"academic_year": self.past_acy.id})

        context = response.context
        self.assertCountEqual(list(context["object_list"]), self.past_mandates)
        self.assertEqual(context["year"], self.past_acy.year)
