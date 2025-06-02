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

import factory
from django.test import TestCase
import random

from assistant.models import assistant_mandate
from assistant.models.assistant_mandate import find_by_academic_year_by_excluding_declined
from assistant.models.assistant_mandate import find_declined_by_academic_year
from assistant.models.enums import assistant_mandate_state
from assistant.models.enums.assistant_mandate_state import ASSISTANT_MANDATE_STATES
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from base.tests.factories.academic_year import AcademicYearFactory


class TestAssistantMandateFactory(TestCase):
    def setUp(self):
        etat_valide = random.choice(
            [state for state,_ in ASSISTANT_MANDATE_STATES if state != assistant_mandate_state.DECLINED]
        )
        self.mandate = AssistantMandateFactory(
            academic_year=factory.SubFactory(AcademicYearFactory, year=datetime.date.today().year - 1),
            state=etat_valide,
        )
        self.mandate2 = AssistantMandateFactory(
            academic_year=factory.SubFactory(AcademicYearFactory, year=datetime.date.today().year))
        self.researched_academic_year = self.mandate.academic_year
        self.mandate3 = AssistantMandateFactory(
            academic_year=factory.SubFactory(AcademicYearFactory, year=datetime.date.today().year),
            state=assistant_mandate_state.DECLINED
        )

    def test_find_mandate_by_id(self):
        self.assertEqual(self.mandate, assistant_mandate.find_mandate_by_id(self.mandate.id))
        self.mandate.delete()
        self.assertEqual(None, assistant_mandate.find_mandate_by_id(self.mandate.id))

    def test_find_by_academic_year(self):
        for current_mandate in assistant_mandate.find_by_academic_year(self.researched_academic_year):
            self.assertEqual(self.researched_academic_year, current_mandate.academic_year)

    def test_find_by_academic_year_by_excluding_declined(self):
        self.assertEqual(
            list(find_by_academic_year_by_excluding_declined(self.researched_academic_year)),
            [self.mandate]
        )

    def test_find_declined_by_academic_year(self):
        self.assertEqual(
            list(find_declined_by_academic_year(self.mandate3.academic_year)),
            [self.mandate3]
        )
