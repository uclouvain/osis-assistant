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
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.mandate_entity import MandateEntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.models.enums import entity_type
from assistant.models import mandate_entity


class TestMandateEntityFactory(TestCase):

    def setUp(self):
        self.assistant_mandate = AssistantMandateFactory()
        self.entity3 = EntityVersionFactory(entity_type=entity_type.SECTOR).entity
        self.entity = EntityVersionFactory(entity_type=entity_type.FACULTY, parent=self.entity3).entity
        self.entity2 = EntityVersionFactory(entity_type=entity_type.SCHOOL, parent=self.entity).entity
        self.mandate_entity = MandateEntityFactory(assistant_mandate=self.assistant_mandate, entity=self.entity)
        self.mandate_entity2 = MandateEntityFactory(assistant_mandate=self.assistant_mandate, entity=self.entity2)
        self.mandate_entity3 = MandateEntityFactory(assistant_mandate=self.assistant_mandate, entity=self.entity3)

    def test_find_by_mandate_and_type(self):
        self.assertEqual(self.mandate_entity,
                         mandate_entity.find_by_mandate_and_type(self.assistant_mandate,
                                                                 entity_type.FACULTY).first())

    def test_find_by_mandate_and_part_of_entity(self):
        self.assertEqual(self.mandate_entity2,
                         mandate_entity.find_by_mandate_and_part_of_entity(self.assistant_mandate, self.entity).first())

    def test_find_by_entity(self):
        self.assertEqual(self.mandate_entity,
                         mandate_entity.find_by_entity(self.entity).first())

    def test_find_by_mandate_and_entity(self):
        self.assertEqual(self.mandate_entity,
                         mandate_entity.find_by_mandate_and_entity(self.assistant_mandate, self.entity).first())

    def test_find_by_mandate(self):
        self.assertCountEqual(
            [self.mandate_entity, self.mandate_entity2, self.mandate_entity3],
            mandate_entity.find_by_mandate(self.assistant_mandate)
        )
