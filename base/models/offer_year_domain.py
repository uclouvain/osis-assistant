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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.db import models
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin


class OfferYearDomainAdmin(SerializableModelAdmin):
    list_display = ('domain', 'offer_year', 'education_group_year', 'changed')
    fieldsets = ((None, {'fields': ('domain', 'offer_year', 'education_group_year')}),)
    list_filter = ('offer_year__academic_year',)
    raw_id_fields = ('domain', 'offer_year')
    search_fields = ['domain__name', 'offer_year__acronym']


class OfferYearDomain(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    domain = models.ForeignKey('reference.Domain', blank=True, null=True)
    offer_year = models.ForeignKey('base.OfferYear', blank=True, null=True)
    education_group_year = models.ForeignKey('base.EducationGroupYear', blank=True, null=True)

    def __str__(self):
        return u"%s - %s" % (self.domain, self.offer_year)


def find_by_education_group_year(education_group_yr):
    return OfferYearDomain.objects.filter(education_group_year=education_group_yr)