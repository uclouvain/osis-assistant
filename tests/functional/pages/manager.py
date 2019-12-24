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
import pypom
from selenium.webdriver.common.by import By

from features.steps.utils import fields


class MandatesList(pypom.Page):
    @property
    def results(self):
        return [MandatesListElement(self, el) for el in self.find_elements(By.CSS_SELECTOR, ".result")]

    def get_result(self, sap_id):
        return next(
            (result for result in self.results if result.registration_number == sap_id)
        )


class MandatesListElement(pypom.Region):
    _registration_number_locator = (By.CSS_SELECTOR, "[headers=registration-number]")
    _name_locator = (By.CSS_SELECTOR, "[headers=name]")
    _entities_locator = (By.CSS_SELECTOR, "[headers=entities]")
    _type_locator = (By.CSS_SELECTOR, "[headers=type]")
    _status_locator = (By.CSS_SELECTOR, "[headers=status]")
    _phd_locator = (By.CSS_SELECTOR, "[headers=phd]")
    _mandate_locator = (By.CSS_SELECTOR, "[headers=mandate]")
    _fte_locator = (By.CSS_SELECTOR, "[headers=fte]")
    _fte_percent_locator = (By.CSS_SELECTOR, "[headers=fte-percent]")
    _opinions_locator = (By.CSS_SELECTOR, "[headers=opinions]")

    _modify_button_locator = (By.CLASS_NAME, "fa-edit")

    @property
    def registration_number(self):
        return self.find_element(*self._registration_number_locator).text

    @property
    def name(self):
        return self.find_element(*self._name_locator).text

    @property
    def entities(self):
        return self.find_element(*self._entities_locator).text

    @property
    def type(self):
        return self.find_element(*self._type_locator).text

    @property
    def status(self):
        return self.find_element(*self._status_locator).text

    @property
    def phd(self):
        return self.find_element(*self._phd_locator).text

    @property
    def mandate(self):
        return self.find_element(*self._mandate_locator).text

    @property
    def fte(self):
        return self.find_element(*self._fte_locator).text

    @property
    def fte_percent(self):
        return self.find_element(*self._fte_percent_locator).text

    @property
    def opinions(self):
        return self.find_element(*self._opinions_locator).text

    @property
    def modify_button(self):
        return self.find_element(*self._modify_button_locator)


class EditAssistantAdministrativeData(pypom.Page):
    assistant_type = fields.SelectField(By.ID, "id_mand-assistant_type")
    registration_number = fields.InputField(By.ID, "id_mand-sap_id")
    renewal_type = fields.SelectField(By.ID, "id_mand-renewal_type")
    contract_duration = fields.InputField(By.ID, "id_mand-contract_duration")
    contract_duration_fte = fields.InputField(By.ID, "id_mand-contract_duration_fte")
    fulltime_equivalent = fields.InputField(By.ID, "id_mand-fulltime_equivalent")

    supervisor = fields.Select2Field(By.ID, "id_supervisor-supervisor")

    entity_1 = fields.SelectField(By.ID, "id_entity-0-entity")
    entity_1_delete = fields.Checkbox(By.ID, "id_entity-0-DELETE")
    entity_2 = fields.SelectField(By.ID, "id_entity-1-entity")
    entity_2_delete = fields.Checkbox(By.ID, "id_entity-1-DELETE")
    entity_3 = fields.SelectField(By.ID, "id_entity-2-entity")
    entity_3_delete = fields.Checkbox(By.ID, "id_entity-2-DELETE")
    entity_4 = fields.SelectField(By.ID, "id_entity-3-entity")
    entity_4_delete = fields.Checkbox(By.ID, "id_entity-3-DELETE")
    entity_5 = fields.SelectField(By.ID, "id_entity-4-entity")
    entity_5_delete = fields.Checkbox(By.ID, "id_entity-4-DELETE")

    comment = fields.InputField(By.ID, "id_mand-comment")
    absences = fields.InputField(By.ID, "id_mand-absences")
    other_status = fields.InputField(By.ID, "id_mand-other_status")

    submit_button = fields.ButtonField(By.ID, "bt_mandate_save")

    def submit(self):
        self.submit_button.click()


class Home(pypom.Page):
    dashboard = fields.Link(MandatesList, By.ID, "lnk_dashboard")
