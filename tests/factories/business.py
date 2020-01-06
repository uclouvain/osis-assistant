############################################################################
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
############################################################################
import random

import factory

from assistant.models.enums import reviewer_role
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.manager import ManagerFactory
from assistant.tests.factories.mandate_entity import MandateEntityFactory
from assistant.tests.factories.reviewer import ReviewerFactory
from base.models.entity_version import EntityVersion
from base.models.enums import entity_type
from base.tests.factories.entity_version import EntityVersionFactory


class BusinessFactory:
    def __init__(self):
        self.entities_tree = EntityVersionTreeFactory()
        self.manager = ManagerFactory()
        self.assistant_mandates = AssistantMandateFactoryBusiness.create_batch(
            10,
            academic_year__current=True,
            post=self.entities_tree
        )
        self.reviewers = assign_reviewer_to_entities(self.entities_tree.elements)


def assign_reviewer_to_entities(entities_version: [EntityVersion]):
    entity_type_to_reviewer_role = {
        entity_type.SECTOR: (reviewer_role.VICE_RECTOR,),
        entity_type.FACULTY: (reviewer_role.SUPERVISION, reviewer_role.SUPERVISION_DAF),
        entity_type.INSTITUTE: (reviewer_role.RESEARCH,)
    }
    reviewers = []
    for entity_version in entities_version:
        for role in entity_type_to_reviewer_role.get(entity_version.entity_type, []):
            reviewers.append(
                ReviewerFactory(role=role, entity=entity_version.entity)
            )
    return reviewers


class AssistantMandateFactoryBusiness(AssistantMandateFactory):

    @factory.post_generation
    def post(obj, create, entity_tree, **kwargs):
        try:
            node = random.choice(entity_tree.root.children)
            while True:
                MandateEntityFactory(
                    assistant_mandate=obj,
                    entity=node.element.entity
                )
                node = random.choice(node.children)
        except IndexError:
            pass


class EntityVersionTreeFactory:

    class Node:
        def __init__(self, element: EntityVersion):
            self.element = element
            self.children = []

    def __init__(self):
        self.root = self.Node(EntityVersionFactory(parent=None, entity_type=""))
        self.nodes = [self.root]
        self._genererate_tree(self.root)

    @property
    def elements(self):
        return [node.element for node in self.nodes]

    def _genererate_tree(self, parent: Node):
        for _ in range(3):
            child_entity_type = self.entity_type_to_generate(parent.element.entity_type)
            if child_entity_type is None:
                continue
            child = self.Node(EntityVersionFactory(parent=parent.element.entity, entity_type=child_entity_type))
            parent.children.append(child)
            self.nodes.append(child)

            self._genererate_tree(child)

    def entity_type_to_generate(self, parent_entity_type):
        type_based_on_parent_type = {
            entity_type.SECTOR: (entity_type.FACULTY, entity_type.LOGISTICS_ENTITY),
            entity_type.FACULTY: (entity_type.PLATFORM, entity_type.SCHOOL, entity_type.INSTITUTE),
            entity_type.LOGISTICS_ENTITY: (entity_type.INSTITUTE, ),
            entity_type.SCHOOL: (None, ),
            entity_type.INSTITUTE: (None, entity_type.POLE, entity_type.PLATFORM),
            entity_type.POLE: (None, ),
            entity_type.DOCTORAL_COMMISSION: (None, ),
            entity_type.PLATFORM: (None, ),
        }
        return random.choice(
            type_based_on_parent_type.get(parent_entity_type, (entity_type.SECTOR, ))
        )
