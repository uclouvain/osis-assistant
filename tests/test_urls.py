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
from django.test import TestCase
from django.urls import resolve, reverse

from assistant.business.assistant_mandate import find_assistant_mandate_step_backward_state
from assistant.utils.export_utils_pdf import export_list_declined_mandates
from assistant.utils.export_utils_pdf import export_mandates_for_entity
from assistant.utils.export_utils_pdf import export_mandates_to_sap
from assistant.views.mails import show_history, send_message_to_assistants, send_message_to_reviewers
from assistant.views.manager_reviews_view import reviews_view


class AssistantURLsTestCase(TestCase):

    def test_url_resolves_to_manager_messages_view(self):
        found = resolve('/assistants/manager/messages/history/')
        self.assertEqual(found.func, show_history)

    def test_url_resolves_to_manager_message_send_to_assistants(self):
        found = resolve(reverse('send_message_to_assistants'))
        self.assertEqual(found.func, send_message_to_assistants)

    def test_url_resolves_to_manager_message_send_to_reviewers(self):
        found = resolve(reverse('send_message_to_reviewers'))
        self.assertEqual(found.func, send_message_to_reviewers)

    def test_url_resolves_to_manager_reviews_view(self):
        found = resolve(reverse('manager_reviews_view', args=[1]))
        self.assertEqual(found.func, reviews_view)

    def test_url_resolves_to_manager_assistant_mandate_go_backward(self):
        found = resolve(reverse('assistant_mandate_step_back'))
        self.assertEqual(found.func, find_assistant_mandate_step_backward_state)

    def test_url_resolves_to_manager_export_declined_mandates(self):
        found = resolve(reverse('export_list_declined_mandates_pdf'))
        self.assertEqual(found.func, export_list_declined_mandates)

    def test_url_resolves_to_reviewer_export_mandates(self):
        found = resolve(reverse('export_mandates_for_entity_pdf', args=[1]))
        self.assertEqual(found.func, export_mandates_for_entity)

    def test_url_resolves_to_manager_export_mandates_to_sap(self):
        found = resolve(reverse('export_mandates_to_sap'))
        self.assertEqual(found.func, export_mandates_to_sap)
