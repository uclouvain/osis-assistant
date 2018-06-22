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
from django.utils import timezone
from django.test import TestCase

from assistant.tests.factories.settings import SettingsFactory
from assistant.models.settings import access_to_procedure_is_open

class TestSettingsFactory(TestCase):
    def setUp(self):
        self.settings = SettingsFactory()

    def test_access_to_procedure_is_open(self):
        self.assertEqual(access_to_procedure_is_open(), True)

    def test_access_to_procedure_is_not_open(self):
        self.settings.starting_date = timezone.now() + timezone.timedelta(days=10)
        self.settings.ending_date = timezone.now() + timezone.timedelta(days=50)
        self.settings.save()
        self.assertFalse(access_to_procedure_is_open())
