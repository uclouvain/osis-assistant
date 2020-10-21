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

from assistant.models.enums import assistant_phd_inscription


class AcademicAssistantAdmin(admin.ModelAdmin):
    list_display = ('person', 'supervisor')
    raw_id_fields = ('person', 'supervisor',)


class AcademicAssistant(models.Model):
    person = models.ForeignKey('base.Person', on_delete=models.CASCADE)
    supervisor = models.ForeignKey('base.Person', blank=True, null=True, related_name='person_supervisor',
                                   on_delete=models.CASCADE)
    thesis_title = models.CharField(max_length=255, null=True, blank=True)
    phd_inscription_date = models.DateField(null=True, blank=True)
    confirmation_test_date = models.DateField(null=True, blank=True)
    thesis_date = models.DateField(null=True, blank=True)
    expected_phd_date = models.DateField(null=True, blank=True)
    remark = models.TextField(null=True, blank=True)
    inscription = models.CharField(max_length=12, choices=assistant_phd_inscription.PHD_INSCRIPTION_CHOICES,
                                   null=True, default=None)
    succeed_confirmation_test_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return u"%s %s" % (self.person.last_name.upper() if self.person.last_name else '', self.person.first_name)


def find_by_person(person):
    try:
        return AcademicAssistant.objects.get(person=person)
    except AcademicAssistant.DoesNotExist:
        return None


def is_supervisor(person):
    return AcademicAssistant.objects.filter(supervisor=person).first()
