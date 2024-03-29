# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
import datetime

from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from base.models.person import Person
from base.models.learning_unit_year import LearningUnitYear, search


class TutorAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Person.objects.none()
        if self.q:
            qs = Person.objects.filter(
                Q(email__icontains=self.q) | Q(last_name__icontains=self.q),
                tutor__isnull=False
            )
        return qs.order_by("last_name", "first_name")

    def get_result_label(self, result: 'Person'):
        return "{person.last_name} {person.first_name} ({person.email})".format(person=result)


class LearningUnitYearAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = LearningUnitYear.objects.none()
        if self.q:
            qs = LearningUnitYear.objects.filter(academic_year__year__lte=datetime.date.today().strftime("%Y"),
                                                 acronym__icontains=self.q)
        return qs.order_by("-academic_year")

    def get_result_label(self, result):
        return "{learningUnit.acronym} ({learningUnit.academic_year})".format(learningUnit=result)

    def get_result_value(self, result):
        return "{learningUnit.id}".format(learningUnit=result)
