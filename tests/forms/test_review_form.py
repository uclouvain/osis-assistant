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
from django.test import TestCase

from assistant.forms import ReviewForm
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.review import ReviewFactory

class TestReviewForm(TestCase):

    def setUp(self):
        self.mandate = AssistantMandateFactory()
        self.review = ReviewFactory(mandate=self.mandate)

    def test_with_valid_data(self):
        form = ReviewForm(data={
            'mandate': self.mandate.id,
            'advice': self.review.advice,
            'status': self.review.status,
            'remark': self.review.remark,
            'justification': self.review.justification,
            'changed': self.review.changed
        }, instance=self.review)
        self.assertTrue(form.is_valid())

    def test_without_advice(self):
        form = ReviewForm(data={
            'mandate': self.mandate.id,
            'advice': None,
            'status': self.review.status,
            'remark': self.review.remark,
            'justification': None,
            'changed': self.review.changed
        }, instance=self.review)
        self.assertFalse(form.is_valid())

