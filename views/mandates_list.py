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
import django_filters.views
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import QueryDict
from django.urls import reverse

from assistant.forms.mandate import AssistantMandateFilter
from assistant.models.enums import assistant_mandate_state
from assistant.utils import manager_access
from base.models import academic_year

SELECTED_ACADEMIC_YEAR_KEY_SESSION = 'selected_academic_year'


class MandatesListView(LoginRequiredMixin, UserPassesTestMixin, django_filters.views.FilterView):
    context_object_name = 'mandates_list'
    template_name = 'mandates_list.html'
    filterset_class = AssistantMandateFilter

    def test_func(self):
        return manager_access.user_is_manager(self.request.user)

    def get_login_url(self):
        return reverse('assistants_home')

    def get_context_data(self, **kwargs):
        context = super(MandatesListView, self).get_context_data(**kwargs)
        context["form"] = context["filter"].form
        context["academic_year"] = self.academic_year_selected
        context['assistant_mandate_state'] = assistant_mandate_state
        return context

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs["data"] = QueryDict.fromkeys(["academic_year"], value=str(self.academic_year_selected.id))
        return kwargs

    @property
    def academic_year_selected(self):
        selected_academic_year_id = self.request.GET.get("academic_year") or \
                                    self.request.session.get(SELECTED_ACADEMIC_YEAR_KEY_SESSION)
        if selected_academic_year_id:
            selected_academic_year = academic_year.AcademicYear.objects.get(id=selected_academic_year_id)
        else:
            selected_academic_year = academic_year.starting_academic_year()
        self._set_academic_year_in_cache(selected_academic_year)
        return selected_academic_year

    def _set_academic_year_in_cache(self, selected_academic_year):
        self.request.session[SELECTED_ACADEMIC_YEAR_KEY_SESSION] = selected_academic_year.id
