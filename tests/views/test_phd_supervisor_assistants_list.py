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

from django.http import HttpResponse, HttpResponseRedirect
from django.test import TestCase

from assistant.models.assistant_mandate import find_for_supervisor_for_academic_year
from assistant.models.enums import assistant_mandate_state, review_status
from assistant.models.enums import reviewer_role
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.mandate_entity import MandateEntityFactory
from assistant.tests.factories.review import ReviewFactory
from assistant.tests.factories.reviewer import ReviewerFactory
from assistant.tests.factories.settings import SettingsFactory
from base.models.entity import find_versions_from_entites
from base.models.enums import entity_type
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory

HTTP_OK = HttpResponse.status_code
HTTP_FOUND = HttpResponseRedirect.status_code


class AssistantsListViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.settings = SettingsFactory()
        today = datetime.date.today()
        cls.current_academic_year = AcademicYearFactory(start_date=today,
                                                        end_date=today.replace(year=today.year + 1),
                                                        year=today.year)
        cls.phd_supervisor = PersonFactory()

        cls.assistant = AcademicAssistantFactory(supervisor=cls.phd_supervisor)
        cls.assistant_mandate = AssistantMandateFactory(academic_year=cls.current_academic_year,
                                                        assistant=cls.assistant)
        cls.assistant_mandate.state = assistant_mandate_state.PHD_SUPERVISOR
        cls.assistant_mandate.save()
        cls.review = ReviewFactory(reviewer=None, mandate=cls.assistant_mandate,
                                   status=review_status.IN_PROGRESS)
        cls.entity_version = EntityVersionFactory(entity_type=entity_type.INSTITUTE)
        cls.mandate_entity = MandateEntityFactory(assistant_mandate=cls.assistant_mandate,
                                                  entity=cls.entity_version.entity)

    def test_with_unlogged_user(self):
        response = self.client.get('/assistants/phd_supervisor/assistants/')
        self.assertEqual(response.status_code, HTTP_FOUND)

    def test_context_data_phd_supervisor_is_not_reviewer(self):
        self.client.force_login(self.phd_supervisor.user)
        response = self.client.get('/assistants/phd_supervisor/assistants/')
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertFalse(response.context['current_reviewer'])
        self.assertFalse(response.context['can_delegate'])
        entities_id = self.assistant_mandate.mandateentity_set.all().order_by('id').values_list('entity', flat=True)
        self.assistant_mandate.entities = find_versions_from_entites(entities_id, None)
        self.assistant_mandate.save()
        self.assertQuerySetEqual(response.context['object_list'],
                                 find_for_supervisor_for_academic_year(self.phd_supervisor, self.current_academic_year),
                                 transform=lambda x: x
                                 )

    def test_context_data_phd_supervisor_is_reviewer(self):
        self.reviewer = ReviewerFactory(role=reviewer_role.RESEARCH,
                                        entity=self.entity_version.entity,
                                        person=self.phd_supervisor)
        self.client.force_login(self.phd_supervisor.user)
        response = self.client.get('/assistants/phd_supervisor/assistants/')
        self.assertEqual(response.context['current_reviewer'], self.reviewer)
        self.assertTrue(response.context['can_delegate'])
