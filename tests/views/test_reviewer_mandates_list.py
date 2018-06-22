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

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.models.enums import entity_type
from base.models.entity import find_versions_from_entites

from assistant.models.assistant_mandate import find_by_academic_year
from assistant.models.enums import reviewer_role
from assistant.models.mandate_entity import find_by_entity
from assistant.models.reviewer import find_by_person
from assistant.tests.factories.review import ReviewFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.mandate_entity import MandateEntityFactory
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.reviewer import ReviewerFactory
from assistant.tests.factories.settings import SettingsFactory
from assistant.models.enums import assistant_mandate_state, review_status

HTTP_OK = 200
HTTP_FOUND = 302

class ReviewerMandatesListViewTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.settings = SettingsFactory()
        today = datetime.date.today()
        self.current_academic_year = AcademicYearFactory(
            start_date=today,
            end_date=today.replace(year=today.year + 1),
            year=today.year
        )
        self.previous_academic_year = AcademicYearFactory(
            start_date=today.replace(year=today.year - 2),
            end_date=today.replace(year=today.year - 1),
            year=today.year-2
        )
        self.phd_supervisor = PersonFactory()
        self.assistant = AcademicAssistantFactory(supervisor=self.phd_supervisor)
        self.assistant_mandate = AssistantMandateFactory(
            academic_year=self.current_academic_year,
            assistant=self.assistant,
            state=assistant_mandate_state.PHD_SUPERVISOR
        )
        self.assistant2 = AcademicAssistantFactory(supervisor=None)
        self.assistant_mandate2 = AssistantMandateFactory(
            academic_year=self.current_academic_year,
            assistant=self.assistant2,
            state=assistant_mandate_state.RESEARCH,
        )
        self.review = ReviewFactory(reviewer=None, mandate=self.assistant_mandate,
                                    status=review_status.IN_PROGRESS)
        self.entity_version = EntityVersionFactory(entity_type=entity_type.INSTITUTE, end_date=None)
        self.mandate_entity = MandateEntityFactory(assistant_mandate=self.assistant_mandate,
                                                   entity=self.entity_version.entity)
        self.mandate_entity2 = MandateEntityFactory(assistant_mandate=self.assistant_mandate2,
                                                   entity=self.entity_version.entity)

    def test_with_unlogged_user(self):
        response = self.client.get('/assistants/reviewer/')
        self.assertEqual(response.status_code, HTTP_FOUND)


    def test_context_data(self):
        self.reviewer = ReviewerFactory(role=reviewer_role.RESEARCH,
                                        entity=self.entity_version.entity,
                                        person=self.phd_supervisor)
        self.client.force_login(self.phd_supervisor.user)
        response = self.client.get('/assistants/reviewer/')
        self.assertEqual(response.context['reviewer'], find_by_person(self.phd_supervisor))
        self.assertTrue(response.context['can_delegate'])
        mandates_id = find_by_entity(self.reviewer.entity).values_list(
            'assistant_mandate_id', flat=True)
        self.assertQuerysetEqual(response.context['object_list'],
                                 find_by_academic_year(self.current_academic_year).filter(id__in=mandates_id),
                                 transform=lambda x: x
                                 )

    def test_context_data_for_specific_academic_year(self):
        self.reviewer = ReviewerFactory(role=reviewer_role.RESEARCH,
                                        entity=self.entity_version.entity,
                                        person=self.phd_supervisor)
        self.client.force_login(self.phd_supervisor.user)
        response = self.client.get('/assistants/reviewer/?academic_year=' + str(self.previous_academic_year.id))
        self.assertEqual(response.context['reviewer'], find_by_person(self.phd_supervisor))
        self.assertTrue(response.context['can_delegate'])
        mandates_id = find_by_entity(self.reviewer.entity).values_list(
            'assistant_mandate_id', flat=True)
        self.assertQuerysetEqual(response.context['object_list'],
                                 find_by_academic_year(self.previous_academic_year).filter(id__in=mandates_id),
                                 transform=lambda x: x
                                 )

