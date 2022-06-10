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
from dal import autocomplete
from base.models.learning_unit_year import LearningUnitYear, search
from django.utils.translation import gettext as _

from assistant import models as mdl


class TutoringLearningUnitForm(ModelForm):
    learning_unit_year = forms.ModelChoiceField(
        queryset=search(),
        # queryset=LearningUnitYear.objects.none(), => no init if we use this
        label=_('Learning unit'),
        widget=autocomplete.ModelSelect2(
            url="/assistants/assistant/form/part2"
                "/get_learning_units_year",
            attrs={
                # Set some placeholder
                'data-placeholder': _('search by course acronym'),
                # Only trigger autocompletion after 2 characters have been
                # typed
                'data-minimum-input-length': 2,
                # 'onchange': (
                # ??   'clearAutocomplete("learning_unit_year");'
                # )
            },
        )
    )
    sessions_number = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'input session_number',
                                                                         'style': 'width:6ch'}))
    sessions_duration = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'input session_duration',
                                                                           'style': 'width:6ch'}))
    series_number = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'input series_numbers',
                                                                       'style': 'width:6ch'}))
    face_to_face_duration = forms.IntegerField(widget=forms.NumberInput(attrs={'readonly': 'enabled',
                                                                               'style': 'width:6ch'}))
    attendees = forms.IntegerField(widget=forms.NumberInput(attrs={'min': '1', 'max': '999', 'step': '1',
                                                                   'style': 'width:6ch'}))
    exams_supervision_duration = forms.IntegerField(
        widget=forms.NumberInput(attrs={'min': '1', 'max': '999', 'step': '1', 'style': 'width:6ch'}))
    others_delivery = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '4'}))
    mandate_id = forms.CharField(widget=forms.HiddenInput(), required=True)
    tutoring_learning_unit_year_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = mdl.tutoring_learning_unit_year.TutoringLearningUnitYear
        fields = ('learning_unit_year', 'sessions_number', 'sessions_duration', 'series_number', 'face_to_face_duration',
                  'attendees', 'exams_supervision_duration', 'others_delivery')
        exclude = ['mandate']

    def __init__(self, *args, **kwargs):
        super(TutoringLearningUnitForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
