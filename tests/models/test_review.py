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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.test import TestCase

from assistant.models.enums import assistant_mandate_state, reviewer_role
from assistant.models.enums import review_status
from assistant.models.review import find_before_mandate_state
from assistant.models.review import get_in_progress_for_mandate
from assistant.tests.factories import review
from assistant.tests.factories import reviewer
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.mandate_entity import MandateEntityFactory
from base.models.enums import entity_type
from base.tests.factories.entity_version import EntityVersionFactory


class TestGetInProgressForMandate(TestCase):
    def test_should_return_none_when_mandate_has_no_review_in_progress_state(self):
        review_with_done_status = review.ReviewFactory(status=review_status.DONE)
        self.assertIsNone(
            get_in_progress_for_mandate(review_with_done_status.mandate)
        )

    def test_should_return_review_when_mandate_has_a_review_in_progress_state(self):
        review_with_done_status = review.ReviewFactory(status=review_status.IN_PROGRESS)
        self.assertEqual(
            get_in_progress_for_mandate(review_with_done_status.mandate),
            review_with_done_status
        )


class TestFindBeforeMandateState(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.mandate = AssistantMandateFactory(state=assistant_mandate_state.DONE)
        cls.entity_version1 = EntityVersionFactory(
            entity_type=entity_type.INSTITUTE,
            end_date=None
        )
        cls.mandate_entity1 = MandateEntityFactory(
            assistant_mandate=cls.mandate,
            entity=cls.entity_version1.entity
        )
        cls.entity_version2 = EntityVersionFactory(
            entity_type=entity_type.FACULTY,
            end_date=None
        )
        cls.mandate_entity2 = MandateEntityFactory(
            assistant_mandate=cls.mandate,
            entity=cls.entity_version2.entity
        )
        cls.entity_version3 = EntityVersionFactory(
            entity_type=entity_type.SECTOR,
            end_date=None
        )
        cls.mandate_entity3 = MandateEntityFactory(
            assistant_mandate=cls.mandate,
            entity=cls.entity_version3.entity
        )

    def setUp(self):
        self.research_reviewer = reviewer.ReviewerFactory(
            role=reviewer_role.RESEARCH,
            entity=self.entity_version1.entity
        )
        self.research_review = review.ReviewFactory(
            reviewer=self.research_reviewer,
            status=review_status.DONE,
            mandate=self.mandate
        )

        self.vice_rector_assistant_reviewer = reviewer.ReviewerFactory(
            role=reviewer_role.VICE_RECTOR_ASSISTANT,
            entity=self.entity_version3.entity
        )
        self.vice_rectore_assistant_review = review.ReviewFactory(
            reviewer=self.vice_rector_assistant_reviewer,
            status=review_status.DONE,
            mandate=self.mandate
        )

        self.supervision_reviewer = reviewer.ReviewerFactory(
            role=reviewer_role.SUPERVISION,
            entity=self.entity_version2.entity
        )
        self.supervision_review = review.ReviewFactory(
            reviewer=self.supervision_reviewer,
            status=review_status.DONE,
            mandate=self.mandate
        )

        self.client.force_login(self.research_reviewer.person.user)

    def test_should_return_reviews_of_roles_with_less_or_equal_privilege(self):
        result = find_before_mandate_state(self.mandate, reviewer_role.SUPERVISION)
        self.assertQuerysetEqual(
            result,
            [self.research_review, self.supervision_review],
            lambda obj: obj
        )

    def test_should_consider_role_as_main_one_when_find_before_mandate_state_is_called_with_assistant_role(self):
        result = find_before_mandate_state(self.mandate, reviewer_role.SUPERVISION_ASSISTANT)
        self.assertQuerysetEqual(
            result,
            [self.research_review, self.supervision_review],
            lambda obj: obj
        )

    def test_should_order_queryset_by_role(self):
        result = find_before_mandate_state(self.mandate, reviewer_role.VICE_RECTOR_ASSISTANT)
        self.assertQuerysetEqual(
            result,
            [self.research_review, self.supervision_review, self.vice_rectore_assistant_review],
            transform=lambda obj: obj
        )
