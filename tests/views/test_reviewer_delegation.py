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

from django.test import TestCase, RequestFactory, Client
from django.http.response import HttpResponseRedirect, HttpResponse
from django.urls import reverse

from assistant.models.academic_assistant import is_supervisor
from assistant.models.enums import assistant_mandate_state, review_status
from assistant.models.enums import reviewer_role
from assistant.models.reviewer import find_by_person
from assistant.models.reviewer import get_delegate_for_entity
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.mandate_entity import MandateEntityFactory
from assistant.tests.factories.review import ReviewFactory
from assistant.tests.factories.reviewer import ReviewerFactory
from assistant.tests.factories.settings import SettingsFactory
from base.models import entity_version
from base.models.entity import find_versions_from_entites
from base.models.enums import entity_type
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory


class ReviewerDelegationDataMixin:
    def setUp(self):
        self.settings = SettingsFactory()

        self.current_academic_year = AcademicYearFactory(current=True)
        self.assistant_mandate = AssistantMandateFactory(
            academic_year=self.current_academic_year,
            state=assistant_mandate_state.PHD_SUPERVISOR
        )
        self.review = ReviewFactory(reviewer=None, mandate=self.assistant_mandate, status=review_status.IN_PROGRESS)

        self.institute = EntityVersionFactory(entity_type=entity_type.INSTITUTE, end_date=None)
        self.institute_child = EntityVersionFactory(parent=self.institute.entity, end_date=None)
        self.school = EntityVersionFactory(entity_type=entity_type.SCHOOL, end_date=None)
        self.sector = EntityVersionFactory(entity_type=entity_type.SECTOR)
        self.faculty = EntityVersionFactory(entity_type=entity_type.FACULTY)

        self.mandate_entity = MandateEntityFactory(
            assistant_mandate=self.assistant_mandate,
            entity=self.institute.entity
        )
        self.research_reviewer = ReviewerFactory(role=reviewer_role.RESEARCH, entity=self.institute.entity)
        self.research_assistant_reviewer = ReviewerFactory(
            role=reviewer_role.RESEARCH_ASSISTANT,
            entity=self.institute_child.entity
        )
        self.vice_sector_reviewer = ReviewerFactory(role=reviewer_role.VICE_RECTOR, entity=self.school.entity)
        self.supervision_reviewer = ReviewerFactory(role=reviewer_role.SUPERVISION, entity=self.faculty.entity)

        self.delegate = PersonFactory()
        self.delegate2 = PersonFactory()

        self.client.force_login(self.research_reviewer.person.user)


class StructuresListView(ReviewerDelegationDataMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("reviewer_delegation")

    def test_context_data(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponse.status_code)

        context = response.context

        # Check if already delegated
        entities_vers_qs = entity_version.EntityVersion.objects.filter(
            pk__in=[self.institute.pk, self.institute_child.pk]
        )
        self.assertQuerysetEqual(context['object_list'], entities_vers_qs, transform=lambda x: x, ordered=False)
        self.assertQuerysetEqual(
            context["object_list"],
            [tuple(), (self.research_assistant_reviewer,)],
            transform=lambda x: tuple(x.entity.delegated_reviewer),
            ordered=False
        )

        self.assertEqual(context['entity'], entity_version.get_last_version(self.research_reviewer.entity))
        self.assertEqual(context['year'], self.current_academic_year.year)
        self.assertEqual(context['current_reviewer'], find_by_person(self.research_reviewer.person)[0])
        self.assertFalse(context['is_supervisor'])


class TestAddReviewerForDelegation(ReviewerDelegationDataMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("reviewer_delegation_add")

    def test_add_reviewer_for_structure_with_invalid_data(self):
        data = {
            'entity': self.institute.entity.id,
            'role': self.research_reviewer.role
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_can_add_reviewer_for_structure_with_person_already_reviewer(self):
        data = {
            'person_id': self.vice_sector_reviewer.person.id,
            'entity': self.institute.entity.id,
            'role': self.research_reviewer.role
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)
        self.assertEqual(
            len(find_by_person(self.vice_sector_reviewer.person)),
            2
        )

    def test_add_reviewer_for_structure_with_valid_data(self):
        data = {
            'person_id': self.delegate.id,
            'entity': self.institute.entity.id,
            'role': self.research_reviewer.role
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)
        self.assertTrue(find_by_person(self.delegate))

    def test_add_reviewer_for_structure_if_logged_reviewer_cannot_delegate(self):
        self.client.force_login(self.vice_sector_reviewer.person.user)
        data = {
            'entity': self.research_reviewer.entity.id
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)
