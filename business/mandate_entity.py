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
from base.models import academic_year
from base.models import entity_version
from base.models.entity import find_versions_from_entites


def get_entities_for_mandate(mandate):
    entities = []
    entities_id = mandate.mandateentity_set.all().order_by('id')
    for this_entity in entities_id:
        current_entity_versions = entity_version.get_by_entity_and_date(
            this_entity.entity, academic_year.current_academic_year().start_date)
        current_entity_version = current_entity_versions[0] if current_entity_versions \
            else entity_version.get_last_version(this_entity.entity)
        entities.append(current_entity_version)
    return entities


def add_entities_version_to_mandates_list(context):
    for mandate in context['object_list']:
        entities_id = mandate.mandateentity_set.all().order_by('id').values_list('entity', flat=True)
        mandate.entities = find_versions_from_entites(entities_id, None)
    return context
