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

from assistant.business.mandate_entity import get_entities_for_mandate
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.mandate_entity import MandateEntityFactory
from base.models.enums import entity_type
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory


class TestMandateEntity(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.maxDiff = None
        cls.assistant_mandate = AssistantMandateFactory()
        cls.entity1 = EntityFactory()
        cls.entity_version1 = EntityVersionFactory(entity=cls.entity1, entity_type=entity_type.SECTOR)
        cls.entity2 = EntityFactory()
        cls.entity_version2 = EntityVersionFactory(entity=cls.entity2, entity_type=entity_type.FACULTY)
        cls.entity3 = EntityFactory()
        cls.entity_version3 = EntityVersionFactory(entity=cls.entity3, entity_type=entity_type.INSTITUTE)
        cls.entity4 = EntityFactory()
        cls.entity_version4 = EntityVersionFactory(
            entity=cls.entity4, parent=cls.entity3, entity_type=entity_type.SCHOOL)

        cls.mandate_entity1 = MandateEntityFactory(assistant_mandate=cls.assistant_mandate, entity=cls.entity1)
        cls.mandate_entity2 = MandateEntityFactory(assistant_mandate=cls.assistant_mandate, entity=cls.entity2)
        cls.mandate_entity3 = MandateEntityFactory(assistant_mandate=cls.assistant_mandate, entity=cls.entity3)

    def test_get_entities_for_mandate(self):
        self.assertCountEqual(
            get_entities_for_mandate(self.assistant_mandate),
            [self.entity_version1, self.entity_version2, self.entity_version3]
        )
