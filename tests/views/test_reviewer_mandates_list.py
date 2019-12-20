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

from django.http.response import HttpResponseRedirect
from django.test import TestCase

from assistant.models.assistant_mandate import find_by_academic_year
from assistant.models.enums import assistant_mandate_state, review_status
from assistant.models.enums import reviewer_role
from assistant.models.mandate_entity import find_by_entity
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.mandate_entity import MandateEntityFactory
from assistant.tests.factories.review import ReviewFactory
from assistant.tests.factories.reviewer import ReviewerFactory
from assistant.tests.factories.settings import SettingsFactory
from base.models.enums import entity_type
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory


class ReviewerMandatesListViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.settings = SettingsFactory()

        cls.previous_academic_year, cls.current_academic_year, _ = AcademicYearFactory.produce()
        cls.phd_supervisor = PersonFactory()
        cls.assistant = AcademicAssistantFactory(supervisor=cls.phd_supervisor)
        cls.assistant_mandate = AssistantMandateFactory(
            academic_year=cls.current_academic_year,
            assistant=cls.assistant,
            state=assistant_mandate_state.PHD_SUPERVISOR
        )
        cls.assistant2 = AcademicAssistantFactory(supervisor=None)
        cls.assistant_mandate2 = AssistantMandateFactory(
            academic_year=cls.current_academic_year,
            assistant=cls.assistant2,
            state=assistant_mandate_state.RESEARCH,
        )
        cls.review = ReviewFactory(reviewer=None, mandate=cls.assistant_mandate,
                                   status=review_status.IN_PROGRESS)
        cls.entity_version = EntityVersionFactory(entity_type=entity_type.INSTITUTE, end_date=None)
        cls.mandate_entity = MandateEntityFactory(
            assistant_mandate=cls.assistant_mandate,
            entity=cls.entity_version.entity
        )
        cls.mandate_entity2 = MandateEntityFactory(
            assistant_mandate=cls.assistant_mandate2,
            entity=cls.entity_version.entity
        )

        cls.reviewer = ReviewerFactory(
            role=reviewer_role.RESEARCH,
            entity=cls.entity_version.entity,
            person=cls.phd_supervisor
        )

    def test_with_unlogged_user(self):
        response = self.client.get('/assistants/reviewer/')
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

    def test_context_data(self):
        self.client.force_login(self.phd_supervisor.user)
        response = self.client.get('/assistants/reviewer/')
        self.assertEqual(response.context['reviewer'], self.reviewer)
        self.assertTrue(response.context['can_delegate'])
        mandates_id = find_by_entity(self.reviewer.entity).values_list('assistant_mandate_id', flat=True)
        self.assertQuerysetEqual(
            response.context['object_list'],
            find_by_academic_year(self.current_academic_year).filter(id__in=mandates_id),
            transform=lambda x: x
        )

    def test_context_data_for_specific_academic_year(self):
        self.client.force_login(self.phd_supervisor.user)
        response = self.client.get('/assistants/reviewer/?academic_year=' + str(self.previous_academic_year.id))
        self.assertEqual(response.context['reviewer'], self.reviewer)
        self.assertTrue(response.context['can_delegate'])
        mandates_id = find_by_entity(self.reviewer.entity).values_list('assistant_mandate_id', flat=True)
        self.assertQuerysetEqual(
            response.context['object_list'],
            find_by_academic_year(self.previous_academic_year).filter(id__in=mandates_id),
            transform=lambda x: x
        )
