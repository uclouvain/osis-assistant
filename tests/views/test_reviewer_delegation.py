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

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.models.enums import entity_type
from base.models.entity import find_versions_from_entites
from base.models import entity_version

from assistant.models.academic_assistant import is_supervisor
from assistant.models.enums import reviewer_role
from assistant.models.reviewer import find_by_person
from assistant.models.reviewer import get_delegate_for_entity
from assistant.tests.factories.review import ReviewFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.mandate_entity import MandateEntityFactory
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.reviewer import ReviewerFactory
from assistant.tests.factories.settings import SettingsFactory
from assistant.models.enums import assistant_mandate_state, review_status

HTTP_OK = 200
HTTP_FOUND = 302

class StructuresListView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        self.settings = SettingsFactory()
        today = datetime.date.today()
        self.current_academic_year = AcademicYearFactory(start_date=today,
                                                         end_date=today.replace(year=today.year + 1),
                                                         year=today.year)
        self.phd_supervisor = PersonFactory()

        self.assistant = AcademicAssistantFactory(supervisor=self.phd_supervisor)
        self.assistant_mandate = AssistantMandateFactory(academic_year=self.current_academic_year,
                                                         assistant=self.assistant)
        self.assistant_mandate.state = assistant_mandate_state.PHD_SUPERVISOR
        self.assistant_mandate.save()
        self.review = ReviewFactory(reviewer=None, mandate=self.assistant_mandate,
                                    status=review_status.IN_PROGRESS)
        self.entity_factory = EntityFactory()
        self.entity_version = EntityVersionFactory(
            entity_type=entity_type.INSTITUTE,
            end_date=None,
            entity=self.entity_factory
        )
        self.entity_factory2 = EntityFactory()
        self.entity_version2 = EntityVersionFactory(
            entity_type=entity_type.SCHOOL,
            end_date=None,
            entity=self.entity_factory2
        )
        self.entity_version2 = EntityVersionFactory(entity_type=entity_type.SECTOR)
        self.mandate_entity = MandateEntityFactory(assistant_mandate=self.assistant_mandate,
                                                   entity=self.entity_version.entity)
        self.reviewer = ReviewerFactory(role=reviewer_role.RESEARCH,
                                        entity=self.entity_version.entity)
        self.reviewer2 = ReviewerFactory(role=reviewer_role.VICE_RECTOR,
                                        entity=self.entity_version2.entity)
        self.entity_version3 = EntityVersionFactory(entity_type=entity_type.FACULTY)
        self.reviewer3 = ReviewerFactory(role=reviewer_role.SUPERVISION,
                                         entity=self.entity_version3.entity)

        self.delegate = PersonFactory()
        self.delegate2 = PersonFactory()

    def test_with_unlogged_user(self):
        response = self.client.get('/assistants/reviewer/delegation/')
        self.assertEqual(response.status_code, HTTP_FOUND)

    def test_context_data(self):
        self.client.force_login(self.reviewer.person.user)
        response = self.client.get('/assistants/reviewer/delegation/')
        entities_version = entity_version.get_last_version(self.reviewer.entity).children
        entities = [this_entity_version.entity for this_entity_version in entities_version]
        entities.insert(0, entity_version.get_last_version(self.reviewer.entity).entity)
        queryset = [{
            'id': entity.id,
            'title': entity_version.get_last_version(entity, None).title,
            'acronym': entity.most_recent_acronym,
            'has_already_delegate': get_delegate_for_entity(self.reviewer, entity)
        } for entity in entities]
        self.assertQuerysetEqual(response.context['object_list'],
                                 queryset,
                                 transform=lambda x: x
                                 )
        self.assertEqual(response.context['entity'], entity_version.get_last_version(self.reviewer.entity))
        self.assertEqual(response.context['year'], self.current_academic_year.year)
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertEqual(response.context['current_reviewer'], find_by_person(self.reviewer.person))
        self.assertEqual(response.context['is_supervisor'], is_supervisor(self.reviewer.person))

    def test_add_reviewer_for_structure_with_invalid_data(self):
        self.client.force_login(self.reviewer.person.user)
        this_entity = find_versions_from_entites([self.entity_factory.id], date=None)[0]
        response = self.client.post('/assistants/reviewer/delegate/add/',
                                    {
                                        #'person_id': self.delegate.id,
                                        'entity': this_entity.id,
                                        'role': self.reviewer.role
                                    }
                                    )
        self.assertEqual(response.status_code, HTTP_OK)

    def test_add_reviewer_for_structure_with_person_already_reviewer(self):
        self.client.force_login(self.reviewer.person.user)
        this_entity = find_versions_from_entites([self.entity_factory.id], date=None)[0]
        response = self.client.post('/assistants/reviewer/delegate/add/',
                                    {
                                        'person_id': self.reviewer2.person.id,
                                        'entity': this_entity.id,
                                        'role': self.reviewer.role
                                    }
                                    )
        self.assertEqual(response.status_code, HTTP_OK)

    def test_add_reviewer_for_structure_with_valid_data(self):
        self.client.force_login(self.reviewer.person.user)
        this_entity = find_versions_from_entites([self.entity_factory.id], date=None)[0]
        response = self.client.post('/assistants/reviewer/delegate/add/',
                                    {
                                        'person_id': self.delegate.id,
                                        'entity': this_entity.id,
                                        'role': self.reviewer.role
                                    }
                                    )
        self.assertEqual(response.status_code, HTTP_FOUND)
        self.assertTrue(find_by_person(self.delegate))

    def test_add_reviewer_for_structure_if_logged_reviewer_cannot_delegate(self):
        self.client.force_login(self.reviewer2.person.user)
        response = self.client.post('/assistants/reviewer/delegate/add/', {'entity': self.reviewer.entity.id})
        self.assertEqual(response.status_code, HTTP_FOUND)