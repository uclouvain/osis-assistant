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

from django.http.response import HttpResponseRedirect, HttpResponse
from django.test import TestCase
from django.urls import reverse

from assistant.models.enums import assistant_mandate_state, review_status
from assistant.models.enums import reviewer_role
from assistant.models.reviewer import find_by_person
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.mandate_entity import MandateEntityFactory
from assistant.tests.factories.review import ReviewFactory
from assistant.tests.factories.reviewer import ReviewerFactory
from assistant.tests.factories.settings import SettingsFactory
from base.models import entity_version
from base.models.enums import entity_type
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory


class ReviewerDelegationDataMixin(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.settings = SettingsFactory()

        cls.current_academic_year = AcademicYearFactory(current=True)
        cls.assistant_mandate = AssistantMandateFactory(
            academic_year=cls.current_academic_year,
            state=assistant_mandate_state.PHD_SUPERVISOR
        )
        cls.review = ReviewFactory(reviewer=None, mandate=cls.assistant_mandate, status=review_status.IN_PROGRESS)

        cls.institute = EntityVersionFactory(entity_type=entity_type.INSTITUTE, end_date=None)
        cls.institute_child = EntityVersionFactory(parent=cls.institute.entity, end_date=None)
        cls.school = EntityVersionFactory(entity_type=entity_type.SCHOOL, end_date=None)
        cls.sector = EntityVersionFactory(entity_type=entity_type.SECTOR)
        cls.faculty = EntityVersionFactory(entity_type=entity_type.FACULTY)

        cls.mandate_entity = MandateEntityFactory(
            assistant_mandate=cls.assistant_mandate,
            entity=cls.institute.entity
        )
        cls.research_reviewer = ReviewerFactory(role=reviewer_role.RESEARCH, entity=cls.institute.entity)
        cls.research_assistant_reviewer = ReviewerFactory(
            role=reviewer_role.RESEARCH_ASSISTANT,
            entity=cls.institute_child.entity
        )
        cls.vice_sector_reviewer = ReviewerFactory(role=reviewer_role.VICE_RECTOR, entity=cls.school.entity)
        cls.supervision_reviewer = ReviewerFactory(role=reviewer_role.SUPERVISION, entity=cls.faculty.entity)

        cls.delegate = PersonFactory()
        cls.delegate2 = PersonFactory()

    def setUp(self):
        self.client.force_login(self.research_reviewer.person.user)


class StructuresListView(ReviewerDelegationDataMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = reverse("reviewer_delegation")

    def test_context_data(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponse.status_code)

        context = response.context

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
        super().setUpTestData()
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
