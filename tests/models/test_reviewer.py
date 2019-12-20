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

from assistant.models import reviewer
from assistant.models.enums import reviewer_role
from assistant.tests.factories.reviewer import ReviewerFactory
from base.models.enums import entity_type
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory


class TestReviewerFactory(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.entity1 = EntityFactory()
        cls.entity_version1 = EntityVersionFactory(entity=cls.entity1, entity_type=entity_type.SECTOR)
        cls.entity2 = EntityFactory()
        cls.entity_version2 = EntityVersionFactory(entity=cls.entity2, entity_type=entity_type.FACULTY)
        cls.entity3 = EntityFactory()
        cls.entity_version3 = EntityVersionFactory(entity=cls.entity3, entity_type=entity_type.FACULTY)
        cls.entity4 = EntityFactory()
        cls.entity_version4 = EntityVersionFactory(
            entity=cls.entity4, parent=cls.entity3, entity_type=entity_type.SCHOOL)
        cls.reviewer1 = ReviewerFactory(role=reviewer_role.VICE_RECTOR, entity=cls.entity1)
        cls.reviewer2 = ReviewerFactory(role=reviewer_role.SUPERVISION, entity=cls.entity2)
        cls.reviewer3 = ReviewerFactory(role=reviewer_role.SUPERVISION, entity=cls.entity3)
        cls.reviewer4 = ReviewerFactory(role=reviewer_role.SUPERVISION_DAF, entity=cls.entity3)
        cls.reviewer5 = ReviewerFactory(role=reviewer_role.SUPERVISION_DAF_ASSISTANT, entity=cls.entity4)
        cls.reviewer6 = ReviewerFactory(role=reviewer_role.VICE_RECTOR_ASSISTANT, entity=cls.entity1)

    def test_find_by_person(self):
        self.assertQuerysetEqual(
            reviewer.find_by_person(self.reviewer1.person),
            [self.reviewer1],
            transform=lambda x: x
        )

    def test_find_reviewers(self):
        self.assertCountEqual(
            list(reviewer.find_reviewers()),
            [self.reviewer2, self.reviewer1, self.reviewer3, self.reviewer4, self.reviewer5, self.reviewer6]
        )

    def test_find_by_id(self):
        self.assertEqual(self.reviewer1, reviewer.find_by_id(self.reviewer1.id))

    def test_find_by_role(self):
        self.assertCountEqual(
            [self.reviewer2, self.reviewer3],
            list(reviewer.find_by_role(reviewer_role.SUPERVISION))
        )

    def test_find_by_entity_and_role(self):
        self.assertCountEqual(
            [self.reviewer2],
            list(reviewer.find_by_entity_and_role(self.entity2, reviewer_role.SUPERVISION))
        )

    def test_can_delegate(self):
        self.assertFalse(reviewer.can_delegate(self.reviewer1))
        self.assertTrue(reviewer.can_delegate(self.reviewer2))

    def test_daf_assistant_cannot_delegate(self):
        self.assertFalse(reviewer.can_delegate(self.reviewer5))

    def test_daf_can_delegate(self):
        self.assertTrue(reviewer.can_delegate(self.reviewer4))

    def test_vice_rector_assistant_can_delegate(self):
        self.assertTrue(reviewer.can_delegate(self.reviewer6))

    def test_can_delegate_to_entity(self):
        self.assertFalse(reviewer.can_delegate_to_entity(self.reviewer1, self.entity1))
        self.assertFalse(reviewer.can_delegate_to_entity(self.reviewer2, self.entity1))
        self.assertTrue(reviewer.can_delegate_to_entity(self.reviewer2, self.entity2))
        self.assertTrue(reviewer.can_delegate_to_entity(self.reviewer3, self.entity4))
        self.assertFalse(reviewer.can_delegate_to_entity(self.reviewer4, self.entity1))

