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

from django import http
from django.test import TestCase
from django.urls import reverse

from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.manager import ManagerFactory
from assistant.tests.factories.reviewer import ReviewerFactory
from assistant.tests.factories.settings import SettingsFactory
from base.models.enums import entity_type
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory


class ReviewerReviewViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = AcademicYearFactory(current=True)
        cls.settings = SettingsFactory()
        cls.manager = ManagerFactory()
        cls.entity_version = EntityVersionFactory(entity_type=entity_type.INSTITUTE)
        cls.reviewer = ReviewerFactory(entity=cls.entity_version.entity)
        cls.assistant = AcademicAssistantFactory()
        cls.unauthorized_person = PersonFactory()

    def test_manager_home(self):
        self.client.force_login(self.manager.person.user)
        response = self.client.get(reverse('manager_home'))
        self.assertTemplateUsed(response, 'manager_home.html')
        self.assertEqual(response.status_code, http.HttpResponse.status_code)

    def test_access_denied(self):
        response = self.client.get(reverse('access_denied'))
        self.assertEqual(response.status_code, http.HttpResponseForbidden.status_code)

    def test_assistant_home(self):
        response = self.client.get(reverse('assistants_home'))
        self.assertRedirects(response, '/login/?next=/assistants/')

        self.client.force_login(self.manager.person.user)
        response = self.client.get(reverse('assistants_home'))
        self.assertRedirects(response, reverse('manager_home'))

        self.client.force_login(self.reviewer.person.user)
        response = self.client.get(reverse('assistants_home'))
        self.assertRedirects(response, reverse('reviewer_mandates_list_todo'))

        self.client.force_login(self.assistant.person.user)
        response = self.client.get(reverse('assistants_home'))
        self.assertRedirects(response, reverse('assistant_mandates'))

        self.client.force_login(self.unauthorized_person.user)
        response = self.client.get(reverse('assistants_home'))
        self.assertRedirects(
            response, reverse('access_denied'),
            target_status_code=http.HttpResponseForbidden.status_code
        )

