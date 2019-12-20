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
from django.urls import reverse
from django.views.generic import ListView
from django.views.generic.edit import FormMixin

from assistant.business.assistant_mandate import add_actions_to_mandates_list
from assistant.business.mandate_entity import add_entities_version_to_mandates_list
from assistant.business.users_access import user_is_reviewer_and_procedure_is_open
from assistant.forms.mandate import MandatesArchivesForm
from assistant.models import assistant_mandate
from assistant.models import reviewer, mandate_entity
from assistant.models.enums import review_status, review_advice_choices
from base.models import academic_year, entity_version


class MandatesListView(LoginRequiredMixin, UserPassesTestMixin, ListView, FormMixin):
    context_object_name = 'reviewer_mandates_list'
    template_name = 'reviewer_mandates_list.html'

    form_class = MandatesArchivesForm
    is_supervisor = False

    def test_func(self):
        return user_is_reviewer_and_procedure_is_open(self.request.user)

    def get_login_url(self):
        return reverse('access_denied')

    def get_queryset(self):
        form_class = MandatesArchivesForm
        form = form_class(self.request.GET)
        if len(assistant_mandate.find_for_supervisor_for_academic_year(self.request.user.person,
                                                                       academic_year.starting_academic_year())) > 0:
            self.is_supervisor = True

        mandates_id = mandate_entity.MandateEntity.objects.filter(
            entity__reviewer__person=self.request.user.person
        ).values_list(
            'assistant_mandate_id',
            flat=True
        )

        if form.is_valid():
            selected_academic_year = form.cleaned_data['academic_year']
        elif self.request.session.get('selected_academic_year'):
            selected_academic_year = academic_year.AcademicYear.objects.get(
                id=self.request.session.get('selected_academic_year')
            )
        else:
            selected_academic_year = academic_year.starting_academic_year()

        self.request.session['selected_academic_year'] = selected_academic_year.id

        if self.kwargs.get("filter", None):
            selected_academic_year = academic_year.starting_academic_year()
            self.request.session['selected_academic_year'] = selected_academic_year.id
            reviewers = reviewer.Reviewer.objects.filter(person=self.request.user.person)
            roles = [rev.role.replace('_ASSISTANT', '').replace('_DAF', '') for rev in reviewers]
            queryset = assistant_mandate.find_by_academic_year(
                selected_academic_year
            ).filter(
                id__in=mandates_id,
                state__in=roles
            )
        else:
            queryset = assistant_mandate.find_by_academic_year(selected_academic_year).filter(id__in=mandates_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(MandatesListView, self).get_context_data(**kwargs)
        current_reviewer = reviewer.find_by_person(self.request.user.person)[0]
        can_delegate = reviewer.can_delegate(current_reviewer)
        context['can_delegate'] = can_delegate
        context['reviewer'] = current_reviewer
        entity = entity_version.get_last_version(current_reviewer.entity)
        context['entity'] = entity
        context['is_supervisor'] = self.is_supervisor
        context['review_status'] = review_status
        context['review_advice_choices'] = review_advice_choices
        context['filter'] = self.kwargs.get("filter", None)
        context['year'] = academic_year.find_academic_year_by_id(
            self.request.session.get('selected_academic_year')).year
        context = add_entities_version_to_mandates_list(context)
        return add_actions_to_mandates_list(context, self.request.user.person)

    def get_initial(self):
        if self.request.session.get('selected_academic_year'):
            selected_academic_year = academic_year.find_academic_year_by_id(
                self.request.session.get('selected_academic_year'))
        else:
            selected_academic_year = academic_year.starting_academic_year()
            self.request.session[
                'selected_academic_year'] = selected_academic_year.id
        return {'academic_year': selected_academic_year}
