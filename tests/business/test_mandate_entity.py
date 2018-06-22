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

from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.models.enums import entity_type

from assistant.business.mandate_entity import get_entities_for_mandate
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.mandate_entity import MandateEntityFactory


class TestMandateEntity(TestCase):


    def setUp(self):

        self.maxDiff = None
        self.assistant_mandate = AssistantMandateFactory()
        self.entity1 = EntityFactory()
        self.entity_version1 = EntityVersionFactory(entity=self.entity1, entity_type=entity_type.SECTOR)
        self.entity2 = EntityFactory()
        self.entity_version2 = EntityVersionFactory(entity=self.entity2, entity_type=entity_type.FACULTY)
        self.entity3 = EntityFactory()
        self.entity_version3 = EntityVersionFactory(entity=self.entity3, entity_type=entity_type.INSTITUTE)
        self.entity4 = EntityFactory()
        self.entity_version4 = EntityVersionFactory(
            entity=self.entity4, parent=self.entity3, entity_type=entity_type.SCHOOL)

        self.mandate_entity1 = MandateEntityFactory(assistant_mandate=self.assistant_mandate, entity=self.entity1)
        self.mandate_entity2 = MandateEntityFactory(assistant_mandate=self.assistant_mandate, entity=self.entity2)
        self.mandate_entity3 = MandateEntityFactory(assistant_mandate=self.assistant_mandate, entity=self.entity3)

    def test_get_entities_for_mandate(self):
        self.assertCountEqual(
            get_entities_for_mandate(self.assistant_mandate),
            [self.entity_version1, self.entity_version2, self.entity_version3]
        )
