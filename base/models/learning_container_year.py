##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from base.models import learning_unit_year
from base.models.enums import learning_unit_year_subtypes, learning_container_year_types


class LearningContainerYearAdmin(admin.ModelAdmin):
    list_display = ('learning_container', 'academic_year', 'container_type', 'acronym', 'title')
    fieldsets = ((None, {'fields': ('learning_container', 'academic_year', 'container_type', 'acronym', 'title')}),)
    search_fields = ['acronym']


class LearningContainerYear(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    academic_year = models.ForeignKey('AcademicYear')
    learning_container = models.ForeignKey('LearningContainer')
    container_type = models.CharField(max_length=20, blank=True, null=True,
                                      choices=learning_container_year_types.LEARNING_CONTAINER_YEAR_TYPES)
    title = models.CharField(max_length=255)
    acronym = models.CharField(max_length=10)
    changed = models.DateTimeField(null=True)


    def __str__(self):
        return u"%s - %s" % (self.acronym, self.title)

    class Meta:
        permissions = (
            ("can_access_learningcontaineryear", "Can access learning container year"),
        )


def find_by_id(learning_container_year_id):
    return LearningContainerYear.objects.get(pk=learning_container_year_id)


def find_all_partims(learning_container_year_id):
    return learning_unit_year.search(learning_container_year_id=learning_container_year_id,
                                     subtype=learning_unit_year_subtypes.PARTIM)\
                             .exclude(learning_container_year__isnull=True)