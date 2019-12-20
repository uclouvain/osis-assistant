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
import datetime

from django.contrib import auth
from django.test import TestCase

from assistant.business.users_access import user_is_phd_supervisor_and_procedure_is_open
from assistant.business.users_access import user_is_reviewer_and_procedure_is_open
from assistant.models.enums import assistant_mandate_state
from assistant.models.enums import review_status
from assistant.models.enums import reviewer_role
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.mandate_entity import MandateEntityFactory
from assistant.tests.factories.review import ReviewFactory
from assistant.tests.factories.reviewer import ReviewerFactory
from assistant.tests.factories.settings import SettingsFactory
from base.models.enums import entity_type
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory


class TestUsersAccess(TestCase):
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
        cls.entity = EntityFactory()
        cls.entity_version = EntityVersionFactory(entity=cls.entity, entity_type=entity_type.INSTITUTE)
        cls.mandate_entity = MandateEntityFactory(assistant_mandate=cls.assistant_mandate, entity=cls.entity)

        cls.reviewer = ReviewerFactory(role=reviewer_role.RESEARCH,
                                       entity=cls.entity_version.entity)

    def test_user_is_reviewer_and_procedure_is_open(self):
        auth.signals.user_logged_in.disconnect(auth.models.update_last_login)
        self.client.force_login(self.reviewer.person.user)
        self.assertTrue(user_is_reviewer_and_procedure_is_open(self.reviewer.person.user))

    def test_user_is_not_reviewer_and_procedure_is_open(self):
        auth.signals.user_logged_in.disconnect(auth.models.update_last_login)
        self.client.force_login(self.assistant.person.user)
        self.assertFalse(user_is_reviewer_and_procedure_is_open(self.assistant.person.user))

    def test_user_is_phd_supervisor_and_procedure_is_open(self):
        auth.signals.user_logged_in.disconnect(auth.models.update_last_login)
        self.client.force_login(self.phd_supervisor.user)
        self.assertTrue(user_is_phd_supervisor_and_procedure_is_open(self.phd_supervisor.user))

    def test_user_is_not_phd_supervisor_and_procedure_is_open(self):
        auth.signals.user_logged_in.disconnect(auth.models.update_last_login)
        self.client.force_login(self.assistant.person.user)
        self.assertFalse(user_is_phd_supervisor_and_procedure_is_open(self.assistant.person.user))
