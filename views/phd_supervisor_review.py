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
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from base.models.enums import entity_type

from assistant.business.mandate_entity import get_entities_for_mandate
from assistant.business.users_access import user_is_phd_supervisor_and_procedure_is_open
from assistant.forms import ReviewForm
from assistant.models import assistant_document_file
from assistant.models import assistant_mandate
from assistant.models import mandate_entity
from assistant.models import review
from assistant.models import tutoring_learning_unit_year
from assistant.models.enums import assistant_mandate_renewal
from assistant.models.enums import assistant_mandate_state
from assistant.models.enums import document_type
from assistant.models.enums import review_status
from assistant.models.enums import reviewer_role


@require_http_methods(["POST"])
@user_passes_test(user_is_phd_supervisor_and_procedure_is_open, login_url='access_denied')
def review_view(request):
    mandate_id = request.POST.get("mandate_id")
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    current_role = reviewer_role.PHD_SUPERVISOR
    try:
        current_review = review.find_done_by_supervisor_for_mandate(mandate)
    except ObjectDoesNotExist:
        current_review = None
    assistant = mandate.assistant
    current_person = request.user.person
    menu = generate_phd_supervisor_menu_tabs(mandate, current_role)
    return render(request, 'review_view.html', {'review': current_review,
                                                'role': current_role,
                                                'menu': menu,
                                                'menu_type': 'phd_supervisor_menu',
                                                'mandate_id': mandate.id,
                                                'mandate_state': mandate.state,
                                                'current_person': current_person,
                                                'assistant': assistant,
                                                'year': mandate.academic_year.year + 1
                                                })


@require_http_methods(["POST"])
@user_passes_test(user_is_phd_supervisor_and_procedure_is_open, login_url='access_denied')
def review_edit(request):
    mandate_id = request.POST.get("mandate_id")
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    try:
        review.find_done_by_supervisor_for_mandate(mandate)
        return HttpResponseRedirect(reverse("assistants_home"))
    except:
        existing_review, created = review.Review.objects.get_or_create(
            mandate=mandate,
            reviewer=None,
            status=review_status.IN_PROGRESS
        )
    previous_mandates = assistant_mandate.find_before_year_for_assistant(mandate.academic_year.year, mandate.assistant)
    menu = generate_phd_supervisor_menu_tabs(mandate, reviewer_role.PHD_SUPERVISOR)
    assistant = mandate.assistant
    current_person = request.user.person
    form = ReviewForm(initial={'mandate': mandate,
                               'reviewer': existing_review.reviewer,
                               'status': existing_review.status,
                               'advice': existing_review.advice,
                               'changed': timezone.now,
                               'confidential': existing_review.confidential,
                               'remark': existing_review.remark
                               }, prefix="rev", instance=existing_review)
    return render(request, 'review_form.html', {'review': existing_review,
                                                'role': reviewer_role.PHD_SUPERVISOR,
                                                'year': mandate.academic_year.year + 1,
                                                'absences': mandate.absences,
                                                'comment': mandate.comment,
                                                'mandate_id': mandate.id,
                                                'previous_mandates': previous_mandates,
                                                'current_person': current_person,
                                                'can_validate': True,
                                                'assistant': assistant,
                                                'menu': menu,
                                                'menu_type': 'phd_supervisor_menu',
                                                'form': form})


@require_http_methods(["POST"])
@user_passes_test(user_is_phd_supervisor_and_procedure_is_open, login_url='access_denied')
def review_save(request):
    mandate_id = request.POST.get("mandate_id")
    review_id = request.POST.get("review_id")
    rev = review.find_by_id(review_id)
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    current_person = request.user.person
    form = ReviewForm(data=request.POST, instance=rev, prefix='rev')
    menu = generate_phd_supervisor_menu_tabs(mandate, reviewer_role.PHD_SUPERVISOR)
    previous_mandates = assistant_mandate.find_before_year_for_assistant(mandate.academic_year.year, mandate.assistant)
    if form.is_valid():
        current_review = form.save(commit=False)
        if 'validate_and_submit' in request.POST:
            validate_review_and_update_mandate(current_review, mandate)
            return HttpResponseRedirect(reverse("phd_supervisor_assistants_list"))
        elif 'save' in request.POST:
            current_review.status = review_status.IN_PROGRESS
            current_review.save()
            return review_edit(request)
    else:
        return render(request, "review_form.html", {'review': rev,
                                                    'role': mandate.state,
                                                    'year': mandate.academic_year.year + 1,
                                                    'current_person': current_person,
                                                    'absences': mandate.absences,
                                                    'comment': mandate.comment,
                                                    'mandate_id': mandate.id,
                                                    'previous_mandates': previous_mandates,
                                                    'assistant': mandate.assistant,
                                                    'menu': menu,
                                                    'menu_type': 'phd_supervisor_menu',
                                                    'form': form})


def validate_review_and_update_mandate(review, mandate):
    review.status = review_status.DONE
    review.save()
    if mandate_entity.find_by_mandate_and_type(mandate, entity_type.INSTITUTE):
        mandate.state = assistant_mandate_state.RESEARCH
    elif mandate_entity.find_by_mandate_and_type(mandate, entity_type.POLE):
        mandate.state = assistant_mandate_state.RESEARCH
    else:
        mandate.state = assistant_mandate_state.SUPERVISION
    mandate.save()


@require_http_methods(["POST"])
@user_passes_test(user_is_phd_supervisor_and_procedure_is_open, login_url='access_denied')
def pst_form_view(request):
    mandate_id = request.POST.get("mandate_id")
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    current_role = reviewer_role.PHD_SUPERVISOR
    current_person = request.user.person
    learning_units = tutoring_learning_unit_year.find_by_mandate(mandate)
    assistant = mandate.assistant
    entities = get_entities_for_mandate(mandate)
    phd_files = assistant_document_file.find_by_assistant_mandate_and_description(mandate,
                                                                                  document_type.PHD_DOCUMENT)
    research_files = assistant_document_file.find_by_assistant_mandate_and_description(mandate,
                                                                                       document_type.RESEARCH_DOCUMENT)
    tutoring_files = assistant_document_file.find_by_assistant_mandate_and_description(mandate,
                                                                                       document_type.TUTORING_DOCUMENT)
    menu = generate_phd_supervisor_menu_tabs(mandate, None)
    return render(request, 'pst_form_view.html', {'menu': menu, 'mandate_id': mandate.id, 'assistant': assistant,
                                                  'mandate': mandate, 'learning_units': learning_units,
                                                  'current_person': current_person, 'phd_files': phd_files,
                                                  'entities': entities, 'research_files': research_files,
                                                  'tutoring_files': tutoring_files, 'role': current_role,
                                                  'assistant_mandate_renewal': assistant_mandate_renewal,
                                                  'menu_type': 'phd_supervisor_menu',
                                                  'year': mandate.academic_year.year + 1})


def generate_phd_supervisor_menu_tabs(mandate, active_item=None):
    try:
        latest_review_done = review.find_done_by_supervisor_for_mandate(mandate)
        review_is_done = latest_review_done.status == review_status.DONE
    except ObjectDoesNotExist:
        review_is_done = False

    is_active = active_item == assistant_mandate_state.PHD_SUPERVISOR
    return [{
        'item': assistant_mandate_state.PHD_SUPERVISOR,
        'class': 'active' if is_active else '',
        'action': 'view' if review_is_done else 'edit'
    }]
