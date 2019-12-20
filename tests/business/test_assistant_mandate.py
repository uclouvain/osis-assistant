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
from django.shortcuts import reverse
from django.test import TestCase

from assistant.business.assistant_mandate import mandate_can_go_backward, add_actions_to_mandates_list
from assistant.models.enums import assistant_mandate_state
from assistant.models.enums import assistant_type
from assistant.models.enums import review_status
from assistant.models.enums import reviewer_role
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.manager import ManagerFactory
from assistant.tests.factories.mandate_entity import MandateEntityFactory
from assistant.tests.factories.review import ReviewFactory
from assistant.tests.factories.reviewer import ReviewerFactory
from assistant.tests.factories.settings import SettingsFactory
from base.models.enums import entity_type
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory


class TestMandateEntity(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = ManagerFactory()
        cls.settings = SettingsFactory()
        cls.assistant = AcademicAssistantFactory()
        cls.assistant_mandate = AssistantMandateFactory(
            state=assistant_mandate_state.TRTS,
            assistant=cls.assistant,
            assistant_type=assistant_type.ASSISTANT
        )
        cls.assistant2 = AcademicAssistantFactory()
        cls.assistant_mandate2 = AssistantMandateFactory(
            state=assistant_mandate_state.SUPERVISION,
            assistant=cls.assistant2,
            assistant_type=assistant_type.TEACHING_ASSISTANT
        )
        cls.entity1 = EntityFactory()
        cls.entity_version1 = EntityVersionFactory(entity=cls.entity1, entity_type=entity_type.SECTOR)
        cls.entity2 = EntityFactory()
        cls.entity_version2 = EntityVersionFactory(entity=cls.entity2, entity_type=entity_type.FACULTY)
        cls.entity3 = EntityFactory()
        cls.entity_version3 = EntityVersionFactory(entity=cls.entity3, entity_type=entity_type.INSTITUTE)
        cls.entity4 = EntityFactory()
        cls.entity_version4 = EntityVersionFactory(
            entity=cls.entity4, parent=cls.entity2, entity_type=entity_type.SCHOOL)

        cls.mandate_entity1 = MandateEntityFactory(assistant_mandate=cls.assistant_mandate, entity=cls.entity1)
        cls.mandate_entity2 = MandateEntityFactory(assistant_mandate=cls.assistant_mandate, entity=cls.entity2)
        cls.mandate_entity3 = MandateEntityFactory(assistant_mandate=cls.assistant_mandate, entity=cls.entity3)

        cls.mandate_entity4 = MandateEntityFactory(assistant_mandate=cls.assistant_mandate2, entity=cls.entity1)
        cls.mandate_entity5 = MandateEntityFactory(assistant_mandate=cls.assistant_mandate2, entity=cls.entity2)

        cls.reviewer1 = ReviewerFactory(entity=cls.entity3, role=reviewer_role.RESEARCH)
        cls.reviewer2 = ReviewerFactory(entity=cls.entity2, role=reviewer_role.SUPERVISION)
        cls.reviewer3 = ReviewerFactory(entity=cls.entity1, role=reviewer_role.VICE_RECTOR)
        cls.reviewer4 = ReviewerFactory(entity=None, role=reviewer_role.PHD_SUPERVISOR)

    def setUp(self):
        self.client.force_login(self.manager.person.user)

    def test_mandate_can_go_backward(self):
        self.assertTrue(mandate_can_go_backward(self.assistant_mandate))
        self.assistant_mandate.state = assistant_mandate_state.RESEARCH
        self.assistant_mandate.save()
        self.review1 = ReviewFactory(
            reviewer=self.reviewer1,
            mandate=self.assistant_mandate,
            status=review_status.IN_PROGRESS
        )
        self.assertFalse(mandate_can_go_backward(self.assistant_mandate))
        self.review1.delete()
        self.assistant_mandate.state = assistant_mandate_state.TO_DO
        self.assistant_mandate.save()
        self.assertFalse(mandate_can_go_backward(self.assistant_mandate))

    def test_assistant_mandate_step_back_from_assistant_to_beginning(self):
        self.assistant_mandate.state = assistant_mandate_state.TRTS
        self.assistant_mandate.save()
        self.client.post(reverse('assistant_mandate_step_back'), {'mandate_id': self.assistant_mandate.id})
        self.assistant_mandate.refresh_from_db()
        self.assertEqual(self.assistant_mandate.state, assistant_mandate_state.TO_DO)

    def test_assistant_mandate_step_back_from_phd_supervisor_to_assistant(self):
        self.assistant_mandate.state = assistant_mandate_state.PHD_SUPERVISOR
        self.assistant_mandate.save()
        self.client.post(reverse('assistant_mandate_step_back'), {'mandate_id': self.assistant_mandate.id})
        self.assistant_mandate.refresh_from_db()
        self.assertEqual(self.assistant_mandate.state, assistant_mandate_state.TRTS)

    def test_assistant_mandate_step_back_from_institute_president_to_php_supervisor(self):
        self.assistant.supervisor = PersonFactory()
        self.assistant.save()
        self.review1 = ReviewFactory(
            reviewer=self.reviewer1,
            mandate=self.assistant_mandate,
            status=review_status.DONE
        )
        self.review2 = ReviewFactory(
            reviewer=None,
            mandate=self.assistant_mandate,
            status=review_status.DONE
        )
        self.assistant_mandate.state = assistant_mandate_state.RESEARCH
        self.assistant_mandate.save()
        self.client.post(reverse('assistant_mandate_step_back'), {'mandate_id': self.assistant_mandate.id})
        self.assistant_mandate.refresh_from_db()
        self.assertEqual(self.assistant_mandate.state, assistant_mandate_state.PHD_SUPERVISOR)

    def test_assistant_mandate_step_back_from_institute_president_to_assistant(self):
        # Test if assistant does not have a phd supervisor
        self.assistant_mandate.state = assistant_mandate_state.RESEARCH
        self.assistant_mandate.save()
        self.assistant.supervisor = None
        self.assistant.save()
        self.client.post(reverse('assistant_mandate_step_back'), {'mandate_id': self.assistant_mandate.id})
        self.assistant_mandate.refresh_from_db()
        self.assertEqual(self.assistant_mandate.state, assistant_mandate_state.TRTS)

    def test_assistant_mandate_step_back_from_dean_of_faculty_to_institute_president(self):
        self.research_review = ReviewFactory(mandate=self.assistant_mandate, reviewer=self.reviewer1)
        self.assistant_mandate.state = assistant_mandate_state.SUPERVISION
        self.assistant_mandate.save()
        self.client.post(reverse('assistant_mandate_step_back'), {'mandate_id': self.assistant_mandate.id})
        self.assistant_mandate.refresh_from_db()
        self.assertEqual(self.assistant_mandate.state, assistant_mandate_state.RESEARCH)

    def test_assistant_mandate_step_back_from_vice_rector_to_dean_of_faculty(self):
        self.supervision_review = ReviewFactory(mandate=self.assistant_mandate, reviewer=self.reviewer2)
        self.assistant_mandate.state = assistant_mandate_state.VICE_RECTOR
        self.assistant_mandate.save()
        self.client.post(reverse('assistant_mandate_step_back'), {'mandate_id': self.assistant_mandate.id})
        self.assistant_mandate.refresh_from_db()
        self.assertEqual(self.assistant_mandate.state, assistant_mandate_state.SUPERVISION)

    def test_assistant_mandate_step_back_from_dean_of_faculty_to_assistant(self):
        # Test if assistant is teaching assistant
        self.research_review = ReviewFactory(mandate=self.assistant_mandate, reviewer=self.reviewer1)
        self.assistant_mandate.state = assistant_mandate_state.SUPERVISION
        self.assistant_mandate.save()
        self.client.post(reverse('assistant_mandate_step_back'), {'mandate_id': self.assistant_mandate2.id})
        self.assistant_mandate2.refresh_from_db()
        self.assertEqual(self.assistant_mandate2.state, assistant_mandate_state.TRTS)

    def test_assistant_mandate_step_back_from_done_to_vice_rector(self):
        self.review4 = ReviewFactory(
            reviewer=self.reviewer3,
            mandate=self.assistant_mandate2,
            status=review_status.DONE
        )
        self.review5 = ReviewFactory(
            reviewer=self.reviewer2,
            mandate=self.assistant_mandate2,
            status=review_status.DONE
        )
        self.assistant_mandate2.state = assistant_mandate_state.DONE
        self.assistant_mandate2.save()
        self.client.post(reverse('assistant_mandate_step_back'), {'mandate_id': self.assistant_mandate2.id})
        self.assistant_mandate2.refresh_from_db()
        self.assertEqual(self.assistant_mandate2.state, assistant_mandate_state.VICE_RECTOR)

    def test_add_actions_to_mandates_list(self):
        self.client.force_login(self.reviewer1.person.user)
        response = self.client.get('/assistants/reviewer/')
        context = add_actions_to_mandates_list(response.context, self.reviewer1.person)
        for mandate in context['object_list']:
            if mandate.id == self.assistant_mandate.id:
                self.assertFalse(mandate.view)
                self.assertFalse(mandate.edit)
        self.client.force_login(self.reviewer2.person.user)
        response = self.client.get('/assistants/reviewer/')
        context = add_actions_to_mandates_list(response.context, self.reviewer2.person)
        for mandate in context['object_list']:
            if mandate.id == self.assistant_mandate2.id:
                self.assertTrue(mandate.view)
                self.assertTrue(mandate.edit)
