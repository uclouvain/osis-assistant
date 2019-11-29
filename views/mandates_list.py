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
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Prefetch
from django.urls import reverse
from django.views.generic import ListView
from django.views.generic.edit import FormMixin

from assistant.forms.mandate import MandatesArchivesForm
from assistant.models import assistant_mandate
from assistant.models.enums import assistant_mandate_state, review_advice_choices, review_status
from assistant.models.mandate_entity import MandateEntity
from assistant.models.review import Review
from assistant.utils import manager_access
from base.models import academic_year
from base.models.entity import Entity
from base.models.entity_version import EntityVersion

SELECTED_ACADEMIC_YEAR_KEY_SESSION = 'selected_academic_year'


class MandatesListView(LoginRequiredMixin, UserPassesTestMixin, ListView, FormMixin):
    context_object_name = 'mandates_list'
    template_name = 'assistant/mandates_list.html'
    form_class = MandatesArchivesForm

    def test_func(self):
        return manager_access.user_is_manager(self.request.user)

    def get_login_url(self):
        return reverse('assistants_home')

    def get_queryset(self):
        form = self.form_class(self.request.GET)

        if form.is_valid():
            selected_academic_year_id = form.cleaned_data['academic_year'].id
        elif self.request.session.get(SELECTED_ACADEMIC_YEAR_KEY_SESSION):
            selected_academic_year_id = self.request.session.get(SELECTED_ACADEMIC_YEAR_KEY_SESSION)
        else:
            selected_academic_year_id = academic_year.starting_academic_year().id

        selected_academic_year = academic_year.AcademicYear.objects.get(id=selected_academic_year_id)
        self.request.session[SELECTED_ACADEMIC_YEAR_KEY_SESSION] = selected_academic_year_id
        qs = assistant_mandate.AssistantMandate.objects.filter(
            academic_year__id=selected_academic_year_id
        ).select_related(
            'academic_year',
            'assistant__person',
            'assistant__supervisor'
        ).prefetch_related(
            Prefetch(
                'review_set',
                queryset=Review.objects.all().select_related('reviewer__person')
            ),
            Prefetch(
                "mandateentity_set",
                queryset=MandateEntity.objects.prefetch_related(
                    Prefetch(
                        "entity",
                        queryset=Entity.objects.prefetch_related(
                            Prefetch(
                                "entityversion_set",
                                queryset=EntityVersion.objects.current(selected_academic_year.start_date),
                                to_attr="versions"
                            )
                        )
                    )
                ).order_by("id"),
                to_attr="mandate_entitites"
            ),
        )
        return qs

    def get_context_data(self, **kwargs):
        context = super(MandatesListView, self).get_context_data(**kwargs)
        context['year'] = academic_year.find_academic_year_by_id(
                self.request.session.get('selected_academic_year')
        ).year
        context['assistant_mandate_state'] = assistant_mandate_state
        context['review_advice_choices'] = review_advice_choices
        context['review_status'] = review_status
        return context

    def get_initial(self):
        if self.request.session.get('selected_academic_year'):
            selected_academic_year = academic_year.find_academic_year_by_id(
                self.request.session.get('selected_academic_year'))
        else:
            selected_academic_year = academic_year.starting_academic_year()
            self.request.session[
                'selected_academic_year'] = selected_academic_year.id
        return {'academic_year': selected_academic_year}
