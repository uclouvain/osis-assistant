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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime

from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.test import TestCase
from django.urls import reverse

from assistant.forms.reviewer import ReviewersFormset
from assistant.models.enums import reviewer_role
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.manager import ManagerFactory
from assistant.tests.factories.review import ReviewFactory
from assistant.tests.factories.reviewer import ReviewerFactory
from base.models.entity import find_versions_from_entites
from base.models.enums import entity_type
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory


class TestReviewersIndex(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.past_acy, cls.current_acy, cls.next_acy = AcademicYearFactory.produce()

        cls.manager = ManagerFactory()
        cls.url = reverse("reviewers_list")

    def setUp(self) -> None:
        self.client.force_login(self.manager.person.user)

    def test_when_no_reviewer(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "reviewers_list.html")

        context = response.context
        self.assertEqual(len(context['reviewers_formset']), 0)

    def test_when_reviewers(self):
        reviewers = ReviewerFactory.create_batch(5)
        for reviewer in reviewers:
            EntityVersionFactory(entity=reviewer.entity)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "reviewers_list.html")

        context = response.context
        self.assertCountEqual(
            [form['id'].value() for form in context['reviewers_formset']],
            [reviewer.id for reviewer in reviewers]
        )


class ReviewersManagementViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person2 = PersonFactory()
        cls.manager = ManagerFactory()
        cls.person = cls.manager.person
        cls.entity_factory = EntityFactory()
        cls.entity_factory2 = EntityFactory()
        cls.entity_version = EntityVersionFactory(entity_type=entity_type.INSTITUTE,
                                                  end_date=None,
                                                  entity=cls.entity_factory)
        cls.entity_version2 = EntityVersionFactory(entity_type=entity_type.INSTITUTE,
                                                   end_date=None,
                                                   entity=cls.entity_factory2)
        cls.phd_supervisor = PersonFactory()

        cls.assistant = AcademicAssistantFactory(supervisor=cls.phd_supervisor)
        today = datetime.date.today()
        cls.current_academic_year = AcademicYearFactory(start_date=today,
                                                        end_date=today.replace(year=today.year + 1),
                                                        year=today.year)
        cls.assistant_mandate = AssistantMandateFactory(academic_year=cls.current_academic_year,
                                                        assistant=cls.assistant)
        cls.reviewer = ReviewerFactory(role=reviewer_role.RESEARCH_ASSISTANT,
                                       entity=cls.entity_version.entity)
        cls.reviewer2 = ReviewerFactory(role=reviewer_role.RESEARCH,
                                        entity=cls.entity_version.entity)
        cls.reviewer3 = ReviewerFactory(role=reviewer_role.RESEARCH,
                                        entity=cls.entity_version.entity)
        cls.review = ReviewFactory(reviewer=cls.reviewer2)
        cls.formset = formset_factory(ReviewersFormset)
        cls.current_academic_year = AcademicYearFactory(start_date=today,
                                                        end_date=today.replace(year=today.year + 1),
                                                        year=today.year)

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_reviewer_action(self):
        form_data = {
            'form-0-action': 'DELETE',
            'form-0-entity_version': self.entity_version,
            'form-0-id': self.reviewer.id,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
            'form-TOTAL_FORMS': '1'
        }
        response = self.client.post('/assistants/manager/reviewers/action/', form_data)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

    def test_reviewer_action_with_bad_method_and_invalid_data(self):
        form_data = {
            'form-0-action': "",
            'form-0-entity_version': self.entity_version,
            'form-0-id': "",
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
            'form-TOTAL_FORMS': '1'
        }
        response = self.client.post('/assistants/manager/reviewers/action/', form_data)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

    def test_reviewer_action_with_replace(self):
        form_data = {
            'form-0-action': 'REPLACE',
            'form-0-entity_version': self.entity_version,
            'form-0-id': self.reviewer.id,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': '1000',
            'form-MIN_NUM_FORMS': '0',
            'form-TOTAL_FORMS': '1'
        }
        response = self.client.post('/assistants/manager/reviewers/action/', form_data)
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_reviewer_add(self):
        this_entity = find_versions_from_entites([self.entity_factory.id], date=None)[0]
        this_entity2 = find_versions_from_entites([self.entity_factory2.id], date=None)[0]
        response = self.client.post('/assistants/manager/reviewers/add/', {'entity': this_entity.id,
                                                                           'role': self.reviewer.role,
                                                                           'person_id': self.reviewer.person.id,
                                                                           })
        self.assertEqual(response.status_code, HttpResponse.status_code)
        response = self.client.post('/assistants/manager/reviewers/add/', {'entity': this_entity.id,
                                                                           'role': self.reviewer.role,
                                                                           'person_id': self.person2.id,
                                                                           })
        self.assertEqual(response.status_code, HttpResponse.status_code)
        response = self.client.post('/assistants/manager/reviewers/add/', {'entity': this_entity2.id,
                                                                           'role': self.reviewer.role,
                                                                           'person_id': self.person2.id,
                                                                           })
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

    def test_reviewer_add_with_bad_method(self):
        this_entity = find_versions_from_entites([self.entity_factory.id], date=None)[0]
        response = self.client.get('/assistants/manager/reviewers/add/', {'entity': this_entity.id,
                                                                          'role': self.reviewer.role,
                                                                          'person_id': self.person2.id,
                                                                          })
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_reviewer_add_without_person(self):
        this_entity = find_versions_from_entites([self.entity_factory.id], date=None)[0]
        response = self.client.post('/assistants/manager/reviewers/add/', {'entity': this_entity.id,
                                                                           'role': self.reviewer.role,
                                                                           'person_id': '',
                                                                           })
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_reviewer_add_with_invalid_form(self):
        response = self.client.post('/assistants/manager/reviewers/add/', {
            'entity': "",
            'role': self.reviewer.role,
            'person_id': self.person2.id,
        })
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_reviewer_replace(self):
        response = self.client.post('/assistants/manager/reviewers/replace/', {
            'person_id': "",
            'reviewer_id': self.reviewer.id,
        })
        self.assertEqual(response.status_code, HttpResponse.status_code)
        response = self.client.post('/assistants/manager/reviewers/replace/', {
            'rev-id': self.reviewer.id,
            'person_id': self.person2.id,
            'reviewer_id': self.reviewer.id,
        })
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)
        response = self.client.post('/assistants/manager/reviewers/replace/', {
            'rev-id': self.reviewer.id,
            'person_id': self.person2.id,
            'reviewer_id': self.reviewer.id,
        })
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)
        response = self.client.post('/assistants/manager/reviewers/replace/', {
            'person_id': self.person2.id,
            'reviewer_id': self.reviewer.id,
        })
        self.assertEqual(response.status_code, HttpResponse.status_code)
