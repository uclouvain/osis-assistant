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


class TestReviewFactory(TestCase):
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
        cls.reviewer1 = reviewer.ReviewerFactory(
            role=reviewer_role.RESEARCH,
            entity=cls.entity_version1.entity
        )
        cls.review1 = review.ReviewFactory(reviewer=cls.reviewer1, status=review_status.DONE, mandate=cls.mandate)
        cls.reviewer2 = reviewer.ReviewerFactory(
            role=reviewer_role.SUPERVISION,
            entity=cls.entity_version2.entity
        )
        cls.review2 = review.ReviewFactory(reviewer=cls.reviewer2, status=review_status.DONE, mandate=cls.mandate)
        cls.reviewer3 = reviewer.ReviewerFactory(
            role=reviewer_role.VICE_RECTOR_ASSISTANT,
            entity=cls.entity_version3.entity
        )
        cls.review2 = review.ReviewFactory(reviewer=cls.reviewer3, status=review_status.DONE, mandate=cls.mandate)

    def setUp(self):
        self.client.force_login(self.reviewer1.person.user)

    def test_find_in_progress_for_mandate(self):
        self.assertFalse(get_in_progress_for_mandate(self.review1.mandate))
        self.review1.status = review_status.IN_PROGRESS
        self.review1.save()
        self.assertEqual(get_in_progress_for_mandate(self.review1.mandate), self.review1)
        self.review1.delete()
        self.mandate.state = assistant_mandate_state.TRTS
        self.assertFalse(get_in_progress_for_mandate(self.review1.mandate))

    def test_find_before_mandate_state(self):
        self.assertEqual(len(find_before_mandate_state(self.mandate, reviewer_role.SUPERVISION)), 2)
        self.assertTrue(
            self.review1 in find_before_mandate_state(self.mandate, reviewer_role.SUPERVISION)
        )

    def test_find_before_mandate_state_for_assistant(self):
        self.assertEqual(len(find_before_mandate_state(self.mandate, reviewer_role.SUPERVISION_ASSISTANT)), 2)
        self.assertTrue(
            self.review1 in find_before_mandate_state(self.mandate, reviewer_role.SUPERVISION)
        )
