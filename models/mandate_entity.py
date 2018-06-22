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
from base.models import entity_version

class MandateEntity(models.Model):
    assistant_mandate = models.ForeignKey('AssistantMandate')
    entity = models.ForeignKey('base.Entity')

    @property
    def name(self):
        return self.__str__()

    def __str__(self):
        version = entity_version.get_by_entity_and_date(self.entity, self.assistant_mandate.academic_year.start_date)
        if version is None:
            version = entity_version.get_last_version(self.entity)
        return u"%s - %s" % (self.assistant_mandate.assistant, version[0].acronym)


def find_by_mandate(mandate):
    return MandateEntity.objects.filter(assistant_mandate=mandate)


def find_by_mandate_and_entity(mandate, entity):
    return MandateEntity.objects.filter(assistant_mandate=mandate, entity=entity)


def find_by_mandate_and_type(mandate, type):
    return MandateEntity.objects.filter(assistant_mandate=mandate, entity__entityversion__entity_type=type)


def find_by_mandate_and_part_of_entity(mandate, entity):
    return MandateEntity.objects.filter(assistant_mandate=mandate, entity__entityversion__parent=entity)


def find_by_entity(entity):
    return MandateEntity.objects.filter(entity=entity)
