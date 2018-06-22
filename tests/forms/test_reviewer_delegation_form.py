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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.test import TestCase

from base.models.entity import find_versions_from_entites
from base.models.enums import entity_type
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory

from assistant.forms import ReviewerDelegationForm
from assistant.models.enums import reviewer_role
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.reviewer import ReviewerFactory

class TestReviewerDelegationForm(TestCase):

    def setUp(self):
        self.mandate = AssistantMandateFactory()
        self.entity_factory = EntityFactory()
        self.entity_version = EntityVersionFactory(entity_type=entity_type.INSTITUTE,
                                                   end_date=None,
                                                   entity=self.entity_factory)
        self.entity_factory2 = EntityFactory()
        self.entity_version2 = EntityVersionFactory(entity_type=entity_type.SECTOR,
                                                   end_date=None,
                                                   entity=self.entity_factory2)
        self.reviewer = ReviewerFactory(role=reviewer_role.RESEARCH,
                                        entity=self.entity_version.entity)
        self.delegate = PersonFactory()

    def test_with_valid_data(self):
        form = ReviewerDelegationForm(data={
            'entity': find_versions_from_entites([self.entity_factory.id], date=None),
            'role': self.reviewer.role
        })
        self.assertTrue(form.is_valid())

    def test_with_invalid_data(self):
        form = ReviewerDelegationForm(data={
            'entity': find_versions_from_entites([self.entity_factory2.id], date=None),
            'role': self.reviewer.role
        })
        self.assertFalse(form.is_valid())
