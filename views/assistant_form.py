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
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext as _
from base.models import person_address, person, learning_unit_year
from base.models.learning_unit_year import search
from assistant.models import *
from assistant.utils.send_email import send_message
from assistant.forms import *
from assistant.models.enums import document_type
from assistant.models.enums import assistant_mandate_state, assistant_phd_inscription
from assistant.utils.assistant_access import user_is_assistant_and_procedure_is_open_and_workflow_is_assistant


@login_required
def get_learning_units_year(request):
    if request.is_ajax() and 'term' in request.GET:
        q = request.GET.get('term')
        learning_units_year = search(acronym=q)[:50]
        response_data = []
        for learning_unit_year in learning_units_year:
            response_data.append({'value': learning_unit_year.acronym,
                                  'title': learning_unit_year.complete_title,
                                  'academic_year': str(learning_unit_year.academic_year),
                                  'id': learning_unit_year.id
                                  })
    else:
        response_data = []
    return JsonResponse(response_data, safe=False)


@user_passes_test(user_is_assistant_and_procedure_is_open_and_workflow_is_assistant, login_url='access_denied')
def form_part1_edit(request, msg=None):
    mandate = assistant_mandate.find_mandate_by_assistant_for_academic_year(
        academic_assistant.find_by_person(request.user.person), academic_year.current_academic_year())
    assistant = mandate.assistant
    form = AssistantFormPart1(initial={'external_functions': mandate.external_functions,
                                       'external_contract': mandate.external_contract,
                                       'justification': mandate.justification})

    return render(request, "assistant_form_part1.html", {'assistant': assistant,
                                                         'mandate': mandate,
                                                         'form': form,
                                                         'msg': msg,
                                                         'supervisor': assistant.supervisor})


@user_passes_test(user_is_assistant_and_procedure_is_open_and_workflow_is_assistant, login_url='access_denied')
@require_http_methods(["POST"])
def form_part1_save(request):
    mandate = assistant_mandate.find_mandate_by_id(request.POST.get("mandate_id"))
    if mandate:
        assistant = mandate.assistant
        pers = person.find_by_id(assistant.person.id)
        addresses = person_address.find_by_person(pers)
        form = AssistantFormPart1(data=request.POST, instance=mandate)
        if form.is_valid():
            form.save()
            return form_part1_edit(request)
        else:
            return render(request, "assistant_form_part1.html", {'assistant': assistant, 'mandate': mandate,
                                                                 'addresses': addresses, 'form': form})
    else:
        return form_part1_edit(request, msg=_("data_not_saved"))


@user_passes_test(user_is_assistant_and_procedure_is_open_and_workflow_is_assistant, login_url='access_denied')
def tutoring_learning_unit_add(request):
    mandate = assistant_mandate.find_mandate_by_assistant_for_academic_year(
        academic_assistant.find_by_person(request.user.person), academic_year.current_academic_year())
    form = TutoringLearningUnitForm(initial={'tutoring_learning_unit_year_id': None
                                             })
    return render(request, "tutoring_learning_unit_year.html", {'form': form,
                                                                'mandate_id': mandate.id,
                                                                'assistant_type': mandate.assistant_type
                                                                })


@user_passes_test(user_is_assistant_and_procedure_is_open_and_workflow_is_assistant, login_url='access_denied')
def tutoring_learning_unit_edit(request, tutoring_learning_unit_id=None):
    edited_tutoring_learning_unit_year = mdl.tutoring_learning_unit_year.find_by_id(tutoring_learning_unit_id)
    mandate_id = edited_tutoring_learning_unit_year.mandate_id
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    assistant = mandate.assistant
    if request.user.person != assistant.person:
        return HttpResponseRedirect(reverse('access_denied'))
    search_learning_units_year = edited_tutoring_learning_unit_year.learning_unit_year.acronym + \
        ' (' + str(edited_tutoring_learning_unit_year.learning_unit_year.academic_year) + ')'

    form = TutoringLearningUnitForm(
        initial={
            'mandate_id': edited_tutoring_learning_unit_year.mandate_id,
            'tutoring_learning_unit_year_id': edited_tutoring_learning_unit_year.id,
            'sessions_duration': edited_tutoring_learning_unit_year.sessions_duration,
            'sessions_number': edited_tutoring_learning_unit_year.sessions_number,
            'series_number': edited_tutoring_learning_unit_year.series_number,
            'face_to_face_duration': edited_tutoring_learning_unit_year.face_to_face_duration,
            'attendees': edited_tutoring_learning_unit_year.attendees,
            'preparation_duration': edited_tutoring_learning_unit_year.preparation_duration,
            'exams_supervision_duration': edited_tutoring_learning_unit_year.exams_supervision_duration,
            'others_delivery': edited_tutoring_learning_unit_year.others_delivery
        })
    return render(request, "tutoring_learning_unit_year.html",
                  {
                      'form': form,
                      'assistant_type': mandate.assistant_type,
                      'mandate_id': mandate_id,
                      'learning_unit_year_id': edited_tutoring_learning_unit_year.learning_unit_year.id,
                      'search_learning_units_year': search_learning_units_year
                  })


@user_passes_test(user_is_assistant_and_procedure_is_open_and_workflow_is_assistant, login_url='access_denied')
@require_http_methods(["POST"])
def tutoring_learning_unit_save(request):
    tutoring_learning_unit_year_id = request.POST.get('tutoring_learning_unit_year_id')
    mandate_id = request.POST.get('mandate_id')
    learning_unit_year_id = request.POST.get('learning_unit_year_id')
    if tutoring_learning_unit_year_id:
        current_tutoring_learning_unit = mdl.tutoring_learning_unit_year.find_by_id(tutoring_learning_unit_year_id)
    else:
        current_tutoring_learning_unit = None
    form = TutoringLearningUnitForm(data=request.POST, instance=current_tutoring_learning_unit)
    if form.is_valid():
        this_mandate = assistant_mandate.find_mandate_by_id(mandate_id)
        current_tutoring_learning_unit = form.save(commit=False)
        if not learning_unit_year_id:
            msg = _("must_enter_learning_unit_year")
            form.add_error(None, msg)
        else:
            this_learning_unit_year = learning_unit_year.get_by_id(learning_unit_year_id)
            current_tutoring_learning_unit.learning_unit_year = this_learning_unit_year
            current_tutoring_learning_unit.mandate = this_mandate
            current_tutoring_learning_unit.save()
            return HttpResponseRedirect(reverse('mandate_learning_units'))
    return render(request, "tutoring_learning_unit_year.html", {'form': form, 'mandate_id': mandate_id})


@user_passes_test(user_is_assistant_and_procedure_is_open_and_workflow_is_assistant, login_url='access_denied')
def tutoring_learning_unit_delete(request, tutoring_learning_unit_id):
    mdl.tutoring_learning_unit_year.find_by_id(tutoring_learning_unit_id).delete()
    return HttpResponseRedirect(reverse('mandate_learning_units'))


@user_passes_test(user_is_assistant_and_procedure_is_open_and_workflow_is_assistant, login_url='access_denied')
def form_part3_edit(request, msg=None):
    mandate = assistant_mandate.find_mandate_by_assistant_for_academic_year(
        academic_assistant.find_by_person(request.user.person), academic_year.current_academic_year())
    assistant = mandate.assistant
    files = assistant_document_file.find_by_assistant_mandate_and_description(mandate, document_type.PHD_DOCUMENT)
    form = AssistantFormPart3(initial={'inscription': assistant.inscription,
                                       'expected_phd_date': assistant.expected_phd_date,
                                       'confirmation_test_date': assistant.confirmation_test_date,
                                       'thesis_date': assistant.thesis_date,
                                       'phd_inscription_date': assistant.phd_inscription_date,
                                       'thesis_title': assistant.thesis_title,
                                       'remark': assistant.remark,
                                       }, prefix='mand')

    return render(request, "assistant_form_part3.html", {'assistant': assistant,
                                                         'mandate': mandate,
                                                         'document_type': document_type.PHD_DOCUMENT,
                                                         'supervisor': assistant.supervisor,
                                                         'files': files,
                                                         'msg': msg,
                                                         'form': form})


@user_passes_test(user_is_assistant_and_procedure_is_open_and_workflow_is_assistant, login_url='access_denied')
@require_http_methods(["POST"])
def form_part3_save(request):
    mandate = assistant_mandate.find_mandate_by_id(request.POST.get("mandate_id"))
    if mandate:
        assistant = mandate.assistant
        files = assistant_document_file.find_by_assistant_mandate_and_description(mandate, document_type.PHD_DOCUMENT)
        form = AssistantFormPart3(data=request.POST, instance=assistant, prefix='mand')
        if form.is_valid():
            current_assistant = form.save(commit=False)
            if current_assistant.inscription != assistant_phd_inscription.NO \
                    and (not request.POST.get('person_id') and current_assistant.supervisor is None):
                msg = _("must_enter_supervisor_if_registered_or_in_progress")
                form.add_error('inscription', msg)
                return render(request, "assistant_form_part3.html", {'assistant': assistant, 'mandate': mandate,
                                                                     'files': files, 'form': form})
            if current_assistant.inscription is None:
                msg = _("phd_inscription_choice_required")
                form.add_error('inscription', msg)
                return render(request, "assistant_form_part3.html", {'assistant': assistant, 'mandate': mandate,
                                                                     'files': files, 'form': form})
            if request.POST.get('person_id'):
                current_assistant.supervisor = person.find_by_id(request.POST.get('person_id'))
                current_assistant.save()
            else:
                form.save()
            return form_part3_edit(request)
        else:
            return render(request, "assistant_form_part3.html", {'assistant': assistant, 'mandate': mandate,
                                                                 'files': files, 'form': form})
    else:
        return form_part3_edit(request, msg=_("data_not_saved"))


@user_passes_test(user_is_assistant_and_procedure_is_open_and_workflow_is_assistant, login_url='access_denied')
def form_part4_edit(request):
    mandate = assistant_mandate.find_mandate_by_assistant_for_academic_year(
        academic_assistant.find_by_person(request.user.person), academic_year.current_academic_year())
    assistant = mandate.assistant
    files = assistant_document_file.find_by_assistant_mandate_and_description(mandate, document_type.RESEARCH_DOCUMENT)
    form = AssistantFormPart4(initial={'internships': mandate.internships,
                                       'conferences': mandate.conferences,
                                       'publications': mandate.publications,
                                       'awards': mandate.awards,
                                       'framing': mandate.framing,
                                       'remark': mandate.remark,
                                       }, prefix='mand')
    return render(request, "assistant_form_part4.html", {'assistant': assistant,
                                                         'mandate': mandate,
                                                         'document_type': document_type.RESEARCH_DOCUMENT,
                                                         'files': files,
                                                         'form': form})


@user_passes_test(user_is_assistant_and_procedure_is_open_and_workflow_is_assistant, login_url='access_denied')
@require_http_methods(["POST"])
def form_part4_save(request):
    mandate = assistant_mandate.find_mandate_by_assistant_for_academic_year(
        academic_assistant.find_by_person(request.user.person), academic_year.current_academic_year())
    assistant = mandate.assistant
    files = assistant_document_file.find_by_assistant_mandate_and_description(mandate, document_type.RESEARCH_DOCUMENT)
    form = AssistantFormPart4(data=request.POST, instance=mandate, prefix='mand')
    if form.is_valid():
        form.save()
        return form_part4_edit(request)
    else:
        return render(request, "assistant_form_part4.html", {
            'assistant': assistant,
            'mandate': mandate,
            'files': files,
            'form': form
        })


@user_passes_test(user_is_assistant_and_procedure_is_open_and_workflow_is_assistant, login_url='access_denied')
def form_part6_edit(request, msg=None):
    mandate = assistant_mandate.find_mandate_by_assistant_for_academic_year(
        academic_assistant.find_by_person(request.user.person), academic_year.current_academic_year())
    assistant = mandate.assistant
    form = AssistantFormPart6(initial={'tutoring_percent': mandate.tutoring_percent,
                                       'service_activities_percent': mandate.service_activities_percent,
                                       'formation_activities_percent': mandate.formation_activities_percent,
                                       'research_percent': mandate.research_percent,
                                       'activities_report_remark': mandate.activities_report_remark
                                       }, prefix='mand')
    return render(request, "assistant_form_part6.html", {'assistant': assistant,
                                                         'mandate': mandate,
                                                         'msg': msg,
                                                         'form': form})


@user_passes_test(user_is_assistant_and_procedure_is_open_and_workflow_is_assistant, login_url='access_denied')
@require_http_methods(["POST"])
def form_part6_save(request):
    mandate = assistant_mandate.find_mandate_by_id(request.POST.get("mandate_id"))
    if mandate:
        assistant = mandate.assistant
        form = AssistantFormPart6(data=request.POST, instance=mandate, prefix='mand')
        if form.is_valid():
            errors_in_form = False
            if 'validate_and_submit' in request.POST:
                current_mandate = form.save(commit=False)
                if assistant.inscription is None:
                    errors_in_form = True
                    msg = _("phd_inscription_choice_required")
                    form.add_error(None, msg)
                learning_units_nbr = tutoring_learning_unit_year.find_by_mandate(current_mandate).count()
                if learning_units_nbr == 0:
                    errors_in_form = True
                    msg = _("at_least_one_learning_unit")
                    form.add_error(None, msg)
                if errors_in_form:
                    current_mandate.save()
                    return render(request, "assistant_form_part6.html", {'assistant': assistant, 'mandate': mandate,
                                                                         'form': form})
                if assistant.supervisor:
                    mandate.state = assistant_mandate_state.PHD_SUPERVISOR
                    html_template_ref = 'assistant_phd_supervisor_html'
                    txt_template_ref = 'assistant_phd_supervisor_txt'
                    send_message(person=assistant.supervisor, html_template_ref=html_template_ref,
                                 txt_template_ref=txt_template_ref, assistant=assistant)
                elif mandate_entity.find_by_mandate_and_type(mandate, entity_type.INSTITUTE):
                    mandate.state = assistant_mandate_state.RESEARCH
                elif mandate_entity.find_by_mandate_and_type(mandate, entity_type.POLE):
                    mandate.state = assistant_mandate_state.RESEARCH
                else:
                    mandate.state = assistant_mandate_state.SUPERVISION
                current_mandate.save()
                return HttpResponseRedirect(reverse('assistant_mandates'))
            else:
                form.save()
                return form_part6_edit(request)
        else:
            return render(request, "assistant_form_part6.html", {'assistant': assistant, 'mandate': mandate,
                                                                 'form': form})
    return form_part6_edit(request, msg=_("data_not_saved"))


@user_passes_test(user_is_assistant_and_procedure_is_open_and_workflow_is_assistant, login_url='access_denied')
def form_part5_edit(request, msg=None):
    mandate = assistant_mandate.find_mandate_by_assistant_for_academic_year(
        academic_assistant.find_by_person(request.user.person), academic_year.current_academic_year())
    assistant = mandate.assistant
    form = AssistantFormPart5(initial={'faculty_representation': mandate.faculty_representation,
                                       'institute_representation': mandate.institute_representation,
                                       'sector_representation': mandate.sector_representation,
                                       'governing_body_representation': mandate.governing_body_representation,
                                       'corsci_representation': mandate.corsci_representation,
                                       'students_service': mandate.students_service,
                                       'infrastructure_mgmt_service': mandate.infrastructure_mgmt_service,
                                       'events_organisation_service': mandate.events_organisation_service,
                                       'publishing_field_service': mandate.publishing_field_service,
                                       'scientific_jury_service': mandate.scientific_jury_service,
                                       'formations': mandate.formations
                                       }, prefix='mand')
    return render(request, "assistant_form_part5.html", {'assistant': assistant,
                                                         'mandate': mandate,
                                                         'msg': msg,
                                                         'form': form}) 


@user_passes_test(user_is_assistant_and_procedure_is_open_and_workflow_is_assistant, login_url='access_denied')
@require_http_methods(["POST"])
def form_part5_save(request):
    mandate = assistant_mandate.find_mandate_by_id(request.POST.get("mandate_id"))
    if mandate:
        assistant = mandate.assistant
        form = AssistantFormPart5(data=request.POST, instance=mandate, prefix='mand')
        if form.is_valid():
            form.save()
            return form_part5_edit(request)
        else:
            return render(request, "assistant_form_part5.html", {'assistant': assistant, 'mandate': mandate,
                                                                 'form': form})
    else:
        return form_part5_edit(request, msg=_("data_not_saved"))
