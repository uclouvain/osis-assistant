##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.test import TestCase, RequestFactory, Client
from django.urls import reverse

from base.models.enums import entity_type
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory

from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.manager import ManagerFactory
from assistant.tests.factories.reviewer import ReviewerFactory
from assistant.tests.factories.settings import SettingsFactory

HTTP_OK = 200
HTTP_FORBIDDEN = 403

class ReviewerReviewViewTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        today = datetime.date.today()
        self.current_academic_year = AcademicYearFactory(start_date=today,
                                                         end_date=today.replace(year=today.year + 1),
                                                         year=today.year)
        self.settings = SettingsFactory()
        self.manager = ManagerFactory()
        self.entity_version = EntityVersionFactory(entity_type=entity_type.INSTITUTE)
        self.reviewer = ReviewerFactory(entity=self.entity_version.entity)
        self.assistant = AcademicAssistantFactory()
        self.unauthorized_person = PersonFactory()

    def test_manager_home(self):
        self.client.force_login(self.manager.person.user)
        response = self.client.get(reverse('manager_home'))
        self.assertTemplateUsed(response, 'manager_home.html')
        self.assertEqual(response.status_code, HTTP_OK)

    def test_access_denied(self):
        self.client.logout()
        response = self.client.get(reverse('access_denied'))
        self.assertEqual(response.status_code, HTTP_FORBIDDEN)

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
        self.assertRedirects(response, reverse('access_denied'), target_status_code=HTTP_FORBIDDEN)

