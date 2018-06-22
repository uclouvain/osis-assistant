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
import factory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory


class TutoringLearningUnitYearFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'assistant.TutoringLearningUnitYear'
        django_get_or_create = ('mandate','learning_unit_year',)

    mandate = factory.SubFactory(AssistantMandateFactory)
    learning_unit_year = factory.SubFactory(LearningUnitYearFactory)

    sessions_duration = factory.fuzzy.FuzzyInteger(1, 4)
    sessions_number = factory.fuzzy.FuzzyInteger(10, 20)
    series_number = factory.fuzzy.FuzzyInteger(1, 3)
    face_to_face_duration = factory.fuzzy.FuzzyInteger(10, 300)
    attendees = factory.fuzzy.FuzzyInteger(5, 50)
    preparation_duration = factory.fuzzy.FuzzyInteger(5, 10)
    exams_supervision_duration = factory.fuzzy.FuzzyInteger(0, 10)
    others_delivery = factory.Faker('text', max_nb_chars=100)
