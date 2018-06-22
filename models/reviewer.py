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
from django.contrib import admin
from django.db import models

from assistant.models.enums import reviewer_role
from base.models import entity_version
from base.models.enums import entity_type


class ReviewerAdmin(admin.ModelAdmin):
    list_display = ('person', 'entity', 'role')
    fieldsets = (
        (None, {'fields': ('person', 'entity', 'role')}),)
    raw_id_fields = ('person', )
    search_fields = ['person__first_name', 'person__last_name',
                     'person__global_id', 'entity__entityversion__acronym']

    def get_form(self, request, obj=None, **kwargs):
        form = super(ReviewerAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['entity'].queryset = \
            entity_version.search_entities(entity_type=entity_type.INSTITUTE) | \
            entity_version.search_entities(entity_type=entity_type.FACULTY) | \
            entity_version.search_entities(entity_type=entity_type.SECTOR) | \
            entity_version.search_entities(entity_type=entity_type.POLE) | \
            entity_version.search_entities(entity_type=entity_type.SCHOOL)
        return form


class Reviewer(models.Model):
    person = models.ForeignKey('base.Person')
    role = models.CharField(max_length=30, choices=reviewer_role.ROLE_CHOICES)
    entity = models.ForeignKey('base.Entity', blank=True, null=True)

    def __str__(self):
        version = entity_version.get_last_version(self.entity)
        return u"%s - %s : %s" % (self.person, version.entity, self.role)


def find_reviewers():
    return Reviewer.objects.all().order_by('person__last_name')


def find_by_id(reviewer_id):
    return Reviewer.objects.get(id=reviewer_id)


def find_by_person(person):
    try:
        return Reviewer.objects.get(person=person)
    except Reviewer.DoesNotExist:
        return False


def find_by_role(role):
    return Reviewer.objects.filter(role=role)


def find_by_entity_and_role(entity, role):
    return Reviewer.objects.filter(entity=entity, role=role)


def can_delegate_to_entity(reviewer, entity):
    if not can_delegate(reviewer):
        return False
    current_version = entity_version.get_last_version(entity)
    if entity == reviewer.entity:
        return True
    if current_version.parent == reviewer.entity:
        return True
    else:
        return False


def can_delegate(reviewer):
    roles_who_can_delegate = [reviewer_role.SUPERVISION, reviewer_role.RESEARCH, reviewer_role.SUPERVISION_DAF]
    return reviewer.role in roles_who_can_delegate


def can_validate(reviewer):
    roles_who_can_validate = [reviewer_role.SUPERVISION, reviewer_role.RESEARCH, reviewer_role.RESEARCH_ASSISTANT,
                              reviewer_role.PHD_SUPERVISOR, reviewer_role.VICE_RECTOR,
                              reviewer_role.VICE_RECTOR_ASSISTANT]
    return reviewer.role in roles_who_can_validate


def get_delegate_for_entity(reviewer, entity):
    delegate_role = reviewer.role + '_ASSISTANT'
    try:
        return Reviewer.objects.get(role=delegate_role, entity=entity)
    except Reviewer.DoesNotExist:
        return None
