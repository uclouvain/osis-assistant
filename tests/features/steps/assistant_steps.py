############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from urllib import request

from behave import *
from behave.runner import Context
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from assistant.business.mandate_entity import fetch_entities
from assistant.models.enums import reviewer_role
from assistant.models.reviewer import Reviewer
from assistant.tests.functional.pages import manager
from base.models import entity
from base.models.enums import entity_type
from base.models.person import Person
from features.steps.utils.pages import LoginPage

use_step_matcher("parse")


@given("The manager is logged")
def step_impl(context: Context):
    page = LoginPage(driver=context.browser, base_url=context.get_url('/login/')).open()
    page.login(context.data.manager.person.user.username)


@step("Go to assistant home page")
def step_impl(context: Context):
    base_url = get_url_by_name(context.test.live_server_url, "manager_home")
    manager.Home(driver=context.browser, base_url=base_url).open()

    context.test.assertURLEqual(context.browser.current_url, base_url)


@step("Click on dashboard link")
def step_impl(context: Context):
    base_url = get_url_by_name(context.test.live_server_url, "manager_home")
    page = manager.Home(driver=context.browser, base_url=base_url)
    page.dashboard.click()

    base_url = get_url_by_name(context.test.live_server_url, "mandates_list")
    page = manager.MandatesList(driver=context.browser, base_url=base_url)
    context.test.assertURLEqual(context.browser.current_url, base_url)
    context.test.assertEqual(len(page.results), 10)

    assistant_mandate = context.data.assistant_mandates[0]
    expected_result = page.get_result(assistant_mandate.sap_id)

    # TODO test entities and opinions
    context.test.assertIn(str(assistant_mandate.assistant), expected_result.name)
    context.test.assertEqual(expected_result.type, assistant_mandate.get_assistant_type_display())
    context.test.assertIn(assistant_mandate.get_state_display(), expected_result.status)
    context.test.assertEqual(
        expected_result.phd,
        _("Yes") if assistant_mandate.assistant.inscription else _("No")
    )
    context.test.assertEqual(expected_result.mandate, assistant_mandate.contract_duration)
    context.test.assertEqual(expected_result.fte, assistant_mandate.contract_duration_fte)
    context.test.assertEqual(
        float(expected_result.fte_percent.replace(",", ".")),
        assistant_mandate.fulltime_equivalent
    )


@step("Click on reviewers link")
def step_impl(context: Context):
    base_url = get_url_by_name(context.test.live_server_url, "manager_home")
    page = manager.Home(driver=context.browser, base_url=base_url)
    page.reviewers.click()

    base_url = get_url_by_name(context.test.live_server_url, "reviewers_list")
    page = manager.ReviewersList(driver=context.browser, base_url=base_url)
    context.test.assertURLEqual(context.browser.current_url, base_url)


@step("Add reviewer")
def step_impl(context: Context):
    base_url = get_url_by_name(context.test.live_server_url, "reviewers_list")
    page = manager.ReviewersList(driver=context.browser, base_url=base_url)
    context.test.assertURLEqual(context.browser.current_url, base_url)
    page.add_reviewer()

    random_person = Person.objects.filter(reviewer__isnull=True).order_by("?")[0]
    random_entity = entity.Entity.objects.filter(entityversion__entity_type=entity_type.SECTOR).order_by('?')[0].id
    page = manager.AddReviewer(driver=context.browser)
    page.person = random_person.email
    page.entity = random_entity
    page.role = reviewer_role.VICE_RECTOR_ASSISTANT
    page.submit()

    base_url = get_url_by_name(context.test.live_server_url, "reviewers_list")
    page = manager.ReviewersList(driver=context.browser, base_url=base_url)
    context.test.assertURLEqual(context.browser.current_url, base_url)

    context.test.assertTrue(
        Reviewer.objects.filter(
            person=random_person,
            entity=random_entity,
            role=reviewer_role.VICE_RECTOR_ASSISTANT
        ).exists()
    )


@step("Add duplicate reviewer")
def step_impl(context: Context):
    base_url = get_url_by_name(context.test.live_server_url, "reviewers_list")
    page = manager.ReviewersList(driver=context.browser, base_url=base_url)
    context.test.assertURLEqual(context.browser.current_url, base_url)
    page.add_reviewer()

    random_person = Person.objects.filter(reviewer__isnull=True).order_by("?")[0]
    random_entity = entity.Entity.objects.filter(entityversion__entity_type=entity_type.SECTOR).order_by('?')[0].id
    page = manager.AddReviewer(driver=context.browser)
    page.person = random_person.email
    page.entity = random_entity
    page.role = reviewer_role.VICE_RECTOR
    page.submit()

    page.has_error()


@step("Substitute reviewer")
def step_impl(context: Context):
    base_url = get_url_by_name(context.test.live_server_url, "reviewers_list")
    page = manager.ReviewersList(driver=context.browser, base_url=base_url)
    context.test.assertURLEqual(context.browser.current_url, base_url)

    random.choice(page.results).replace()

    random_person = Person.objects.filter(reviewer__isnull=True).order_by("?")[0]
    page = manager.SubstituteReviewer(driver=context.browser)
    page.person = random_person.email
    page.submit()

    base_url = get_url_by_name(context.test.live_server_url, "reviewers_list")
    page = manager.ReviewersList(driver=context.browser, base_url=base_url)
    context.test.assertURLEqual(context.browser.current_url, base_url)

    context.test.assertTrue(Reviewer.objects.filter(person=random_person).exists())


@step("Delete reviewer")
def step_impl(context: Context):
    base_url = get_url_by_name(context.test.live_server_url, "reviewers_list")
    page = manager.ReviewersList(driver=context.browser, base_url=base_url)
    context.test.assertURLEqual(context.browser.current_url, base_url)
    reviewer_count = Reviewer.objects.all().count()
    random.choice(page.results).delete()
    context.test.assertEqual(Reviewer.objects.all().count(), reviewer_count-1)


@step("Click randomly on edit assistant link")
def step_impl(context: Context):
    base_url = get_url_by_name(context.test.live_server_url, "mandates_list")
    page = manager.MandatesList(driver=context.browser, base_url=base_url)
    random.choice(page.results).modify_button.click()


@step("Edit assistant administrative data")
def step_impl(context: Context):
    page = manager.EditAssistantAdministrativeData(driver=context.browser)

    random_entity = fetch_entities().order_by("?")[0]
    page.comment = "Selenium"
    page.entity_3 = random_entity.id
    page.submit()

    page = manager.EditAssistantAdministrativeData(driver=context.browser)

    context.test.assertEqual(page.comment.text, "Selenium")
    context.test.assertEqual(page.entity_3.element.get_property("value"), str(random_entity.id))

    page.entity_3_delete = True
    page.submit()

    page = manager.EditAssistantAdministrativeData(
        driver=context.browser,
    )
    context.test.assertNotEqual(page.entity_3.element.get_property("value"), str(random_entity.id))


def get_url_by_name(live_server_url, url_name, *args, **kwargs):
    return request.urljoin(live_server_url, reverse(url_name, args=args, kwargs=kwargs))
