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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.contrib import admin
from django.db import models


class TutoringLearningUnitYearAdmin(admin.ModelAdmin):
    list_display = ("mandate", "learning_unit_year")
    search_fields = [
        "mandate__assistant__person__first_name",
        "mandate__assistant__person__last_name",
        "mandate__assistant__person__global_id",
        "learning_unit_year__acronym"
    ]
    list_filter = ('mandate__academic_year',)


class TutoringLearningUnitYear(models.Model):
    mandate = models.ForeignKey('AssistantMandate', on_delete=models.CASCADE)
    learning_unit_year = models.ForeignKey('base.LearningUnitYear', on_delete=models.CASCADE)
    sessions_duration = models.PositiveIntegerField(null=True, blank=True)
    sessions_number = models.PositiveIntegerField(null=True, blank=True)
    series_number = models.PositiveIntegerField(null=True, blank=True)
    face_to_face_duration = models.PositiveIntegerField(null=True, blank=True)
    attendees = models.PositiveIntegerField(null=True, blank=True)
    preparation_duration = models.PositiveIntegerField(null=True, blank=True)
    exams_supervision_duration = models.PositiveIntegerField(null=True, blank=True)
    others_delivery = models.TextField(null=True, blank=True)


def find_by_id(tutoring_learning_unit_id):
    return TutoringLearningUnitYear.objects.get(id=tutoring_learning_unit_id)


def find_by_mandate(mandate):
    return TutoringLearningUnitYear.objects.filter(mandate=mandate).select_related(
        'learning_unit_year__academic_year', 'learning_unit_year__learning_container_year'
    ).order_by(
        'learning_unit_year__academic_year'
    )


def find_learning_unit_year(learning_unit_year):
    return TutoringLearningUnitYear.objects.filter(learning_unit_year=learning_unit_year)
