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
import django_filters
from django import forms
from django.db.models import Prefetch
from django.forms import ModelForm, Textarea, inlineformset_factory
from django.utils.translation import pgettext_lazy, ugettext_lazy as _

import base.models
from assistant import models as mdl
from assistant.forms.common import EntityChoiceField
from assistant.models import assistant_mandate, mandate_entity, review
from assistant.models.enums import assistant_mandate_renewal, assistant_type, review_status
from base.models import academic_year, entity, entity_version
from base.models.enums import entity_type


class MandateForm(ModelForm):
    comment = forms.CharField(required=False, widget=Textarea(
        attrs={'rows': '4', 'cols': '80'}))
    absences = forms.CharField(required=False, widget=Textarea(
        attrs={'rows': '4', 'cols': '80'}))
    other_status = forms.CharField(max_length=50, required=False)
    renewal_type = forms.ChoiceField(
        choices=assistant_mandate_renewal.ASSISTANT_MANDATE_RENEWAL_TYPES)
    assistant_type = forms.ChoiceField(
        choices=assistant_type.ASSISTANT_TYPES)
    sap_id = forms.CharField(required=True, max_length=12, strip=True)
    contract_duration = forms.CharField(
        required=True, max_length=30, strip=True)
    contract_duration_fte = forms.CharField(
        required=True, max_length=30, strip=True)
    fulltime_equivalent = forms.NumberInput()

    class Meta:
        model = mdl.assistant_mandate.AssistantMandate
        fields = ('comment', 'absences', 'other_status', 'renewal_type', 'assistant_type', 'sap_id',
                  'contract_duration', 'contract_duration_fte', 'fulltime_equivalent')

    def __init__(self, *args, **kwargs):
        super(MandateForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class AssistantMandateFilter(django_filters.FilterSet):
    academic_year = django_filters.filters.ModelChoiceFilter(
        queryset=academic_year.AcademicYear.objects.all(),
        required=False,
        label=_('Ac yr.'),
        empty_label=pgettext_lazy("plural", "All"),
    )

    class Meta:
        model = assistant_mandate.AssistantMandate
        fields = [
            "academic_year"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = self.get_queryset()

    def get_queryset(self):
        qs = assistant_mandate.AssistantMandate.objects.all(

        ).select_related(
            'academic_year',
            'assistant__person',
            'assistant__supervisor'
        ).prefetch_related(
            Prefetch(
                'review_set',
                queryset=review.Review.objects.filter(status=review_status.DONE).select_related('reviewer__person')
            ),
            Prefetch(
                "mandateentity_set",
                queryset=mandate_entity.MandateEntity.objects.prefetch_related(
                    Prefetch(
                        "entity",
                        queryset=entity.Entity.objects.prefetch_related(
                            Prefetch(
                                "entityversion_set",
                                queryset=entity_version.EntityVersion.objects.current(
                                    academic_year.starting_academic_year().start_date
                                ),
                                to_attr="versions"
                            )
                        )
                    )
                ).order_by("id"),
                to_attr="mandate_entitites"
            ),
        )
        return qs


class MandatesArchivesForm(ModelForm):
    academic_year = forms.ModelChoiceField(queryset=academic_year.AcademicYear.objects.all())

    class Meta:
        model = mdl.assistant_mandate.AssistantMandate
        fields = ('academic_year',)


def get_field_qs(field, **kwargs):
    if field.name == 'entity':
        return EntityChoiceField(queryset=base.models.entity.find_versions_from_entites(
            entity.search(entity_type=entity_type.SECTOR) |
            entity.search(entity_type=entity_type.FACULTY) |
            entity.search(entity_type=entity_type.LOGISTICS_ENTITY) |
            entity.search(entity_type=entity_type.SCHOOL) |
            entity.search(entity_type=entity_type.INSTITUTE) |
            entity.search(entity_type=entity_type.POLE), None))
    return field.formfield(**kwargs)


entity_inline_formset = inlineformset_factory(mdl.assistant_mandate.AssistantMandate,
                                              mdl.mandate_entity.MandateEntity,
                                              formfield_callback=get_field_qs,
                                              fields=('entity', 'assistant_mandate'),
                                              extra=1, can_delete=True, min_num=1, max_num=5)
