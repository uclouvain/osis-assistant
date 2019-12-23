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
import decimal

from django.utils.translation import gettext_lazy as _
from assessments.tests.functionals.test_score_encoding import SeleniumTestCase
from assistant.tests.factories.business import BusinessFactory
from assistant.tests.functional.pages import manager
from features.steps.utils.pages import LoginPage


class TestManager(SeleniumTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data = BusinessFactory()

    def setUp(self) -> None:
        LoginPage(
            driver=self.driver,
            base_url=self.live_server_url
        ).open().login(
            self.data.manager.person.user.username
        )

    def test_manager_should_be_able_to_see_mandates(self):
        page = manager.Home(driver=self.driver, base_url=self.get_url_by_name("manager_home")).open()
        page.dashboard.click()

        page = manager.MandatesList(driver=self.driver, base_url=self.get_url_by_name("mandates_list"))
        self.assertEqual(page.count_result(), 10)

        assistant_mandate = self.data.assistant_mandates[0]
        expected_result = page.get_result(assistant_mandate.sap_id)

        # TODO test entities and opinions
        self.assertIn(str(assistant_mandate.assistant), expected_result.name)
        self.assertEqual(expected_result.type, assistant_mandate.get_assistant_type_display())
        self.assertIn(assistant_mandate.get_state_display(), expected_result.status)
        self.assertEqual(
            expected_result.phd,
            _("Yes") if assistant_mandate.assistant.inscription else _("No")
        )
        self.assertEqual(expected_result.mandate, assistant_mandate.contract_duration)
        self.assertEqual(expected_result.fte, assistant_mandate.contract_duration_fte)
        self.assertEqual(
            float(expected_result.fte_percent.replace(",", ".")),
            assistant_mandate.fulltime_equivalent
        )

