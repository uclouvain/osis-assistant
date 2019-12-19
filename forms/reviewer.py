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
from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext as _

import base.models
from assistant import models as mdl
from assistant.forms.common import EntityChoiceField
from assistant.models.enums import reviewer_role
from base.models import entity
from base.models.enums import entity_type


class ReviewerForm(ModelForm):
    role = forms.ChoiceField(required=True, choices=reviewer_role.ROLE_CHOICES)
    entities = \
        entity.search(entity_type=entity_type.INSTITUTE) | entity.search(entity_type=entity_type.FACULTY) | \
        entity.search(entity_type=entity_type.SECTOR) | entity.search(entity_type=entity_type.LOGISTICS_ENTITY)
    entity = EntityChoiceField(required=True, queryset=base.models.entity.find_versions_from_entites(entities, None))

    class Meta:
        model = mdl.reviewer.Reviewer
        fields = ('entity', 'role')
        exclude = ['person']

    def __init__(self, *args, **kwargs):
        super(ReviewerForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class ReviewerDelegationForm(ModelForm):
    role = forms.CharField(widget=forms.HiddenInput(), required=True)
    entities = \
        entity.search(entity_type=entity_type.INSTITUTE) | entity.search(entity_type=entity_type.FACULTY) | \
        entity.search(entity_type=entity_type.SCHOOL) | entity.search(entity_type=entity_type.PLATFORM) | \
        entity.search(entity_type=entity_type.POLE)
    entity = EntityChoiceField(required=True, queryset=base.models.entity.find_versions_from_entites(entities, None))

    class Meta:
        model = mdl.reviewer.Reviewer
        fields = ('entity', 'role')
        exclude = ['person']
        widgets = {
            'entity': forms.HiddenInput()
        }


class ReviewerReplacementForm(ModelForm):
    person = forms.ChoiceField(required=False)
    id = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = mdl.reviewer.Reviewer
        fields = ('id',)
        exclude = ('person', 'entity', 'role')


class ReviewersFormset(ModelForm):
    ACTIONS = (
        ('-----', '-----'),
        ('DELETE', _('Delete')),
        ('REPLACE', _('Replace'))
    )

    role = forms.ChoiceField(required=False)
    entity = forms.CharField(required=False)
    entity_version = forms.CharField(required=False)
    person = forms.ChoiceField(required=False)
    id = forms.IntegerField(required=False)
    action = forms.ChoiceField(
        required=False,
        choices=ACTIONS,
        widget=forms.Select(attrs={'class': 'selector', 'onchange': 'this.form.submit();'})
    )

    class Meta:
        model = mdl.reviewer.Reviewer
        exclude = ('entity', 'role', 'person')
