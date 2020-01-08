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

from django.test import TestCase

from assistant.models.enums import assistant_mandate_state, review_status
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.mandate_entity import MandateEntityFactory
from assistant.tests.factories.review import ReviewFactory
from assistant.tests.factories.settings import SettingsFactory
from assistant.views.phd_supervisor_review import generate_phd_supervisor_menu_tabs
from assistant.views.phd_supervisor_review import validate_review_and_update_mandate
from base.models.enums import entity_type
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory

HTTP_OK = 200
HTTP_FOUND = 302


class PhdSupervisorReviewViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.settings = SettingsFactory()
        today = datetime.date.today()
        cls.current_academic_year = AcademicYearFactory(start_date=today,
                                                        end_date=today.replace(year=today.year + 1),
                                                        year=today.year)
        cls.phd_supervisor = PersonFactory()
        cls.assistant = AcademicAssistantFactory(supervisor=cls.phd_supervisor)
        cls.assistant_mandate = AssistantMandateFactory(academic_year=cls.current_academic_year,
                                                        assistant=cls.assistant)
        cls.assistant_mandate.state = assistant_mandate_state.PHD_SUPERVISOR
        cls.assistant_mandate.save()
        cls.review = ReviewFactory(reviewer=None, mandate=cls.assistant_mandate,
                                   status=review_status.IN_PROGRESS)
        cls.entity1 = EntityFactory()
        cls.entity_version1 = EntityVersionFactory(entity=cls.entity1, entity_type=entity_type.INSTITUTE)
        cls.mandate_entity = MandateEntityFactory(assistant_mandate=cls.assistant_mandate, entity=cls.entity1)

    def setUp(self):
        self.client.force_login(self.phd_supervisor.user)

    def test_generate_phd_supervisor_menu_tabs(self):
        # Review has not been completed -> supervisor can edit
        self.assertEqual(generate_phd_supervisor_menu_tabs(self.assistant_mandate, None),
                         [{'item': assistant_mandate_state.PHD_SUPERVISOR, 'class': '',
                           'action': 'edit'}])
        self.assertEqual(generate_phd_supervisor_menu_tabs(self.assistant_mandate,
                                                           assistant_mandate_state.PHD_SUPERVISOR),
                         [{'item': assistant_mandate_state.PHD_SUPERVISOR, 'class': 'active',
                           'action': 'edit'}])
        # Review has been completed -> supervisor can only view his review
        self.review.status = review_status.DONE
        self.review.save()
        self.assistant_mandate.state = assistant_mandate_state.RESEARCH
        self.assistant_mandate.save()
        self.assertEqual(generate_phd_supervisor_menu_tabs(self.assistant_mandate, None),
                         [{'item': assistant_mandate_state.PHD_SUPERVISOR, 'class': '',
                           'action': 'view'}])
        self.assertEqual(generate_phd_supervisor_menu_tabs(self.assistant_mandate,
                                                           assistant_mandate_state.PHD_SUPERVISOR),
                         [{'item': assistant_mandate_state.PHD_SUPERVISOR, 'class': 'active',
                           'action': 'view'}])

    def test_pst_form_view(self):
        response = self.client.post('/assistants/phd_supervisor/pst_form/', {'mandate_id': self.assistant_mandate.id})
        self.assertEqual(response.status_code, HTTP_OK)

    def test_review_view(self):
        response = self.client.post('/assistants/phd_supervisor/review/view/',
                                    {'mandate_id': self.assistant_mandate.id})
        self.assertEqual(response.status_code, HTTP_OK)

    def test_review_edit(self):
        response = self.client.post('/assistants/phd_supervisor/review/edit/',
                                    {'mandate_id': self.assistant_mandate.id})
        self.assertEqual(response.status_code, HTTP_OK)
        self.review.status = review_status.DONE
        self.review.save()
        response = self.client.post('/assistants/phd_supervisor/review/edit/',
                                    {'mandate_id': self.assistant_mandate.id})
        self.assertEqual(response.status_code, HTTP_FOUND)

    def test_review_save(self):
        response = self.client.post('/assistants/phd_supervisor/review/save/', {'mandate_id': self.assistant_mandate.id,
                                                                                'review_id': self.review.id
                                                                                })
        self.assertEqual(response.status_code, HTTP_OK)

    def test_validate_review_and_update_mandate(self):
        validate_review_and_update_mandate(self.review, self.assistant_mandate)
        self.assertEqual(self.review.status, review_status.DONE)
        self.assertEqual(self.assistant_mandate.state, assistant_mandate_state.RESEARCH)
        self.entity_version1.entity_type = entity_type.POLE
        self.entity_version1.save()
        validate_review_and_update_mandate(self.review, self.assistant_mandate)
        self.assertEqual(self.assistant_mandate.state, assistant_mandate_state.RESEARCH)
        self.entity_version1.entity_type = entity_type.FACULTY
        self.entity_version1.save()
        validate_review_and_update_mandate(self.review, self.assistant_mandate)
        self.assertEqual(self.assistant_mandate.state, assistant_mandate_state.SUPERVISION)
