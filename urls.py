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
from django.urls import include
from django.urls import re_path, path

from assistant.business.assistant_mandate import find_assistant_mandate_step_backward_state
from assistant.utils import get_persons
from assistant.utils import import_xls_file_data, export_utils_pdf
from assistant.views import assistant_mandate_reviews, autocomplete, mails
from assistant.views import manager_assistant_form
from assistant.views import manager_reviews_view
from assistant.views import manager_settings, reviewers_management, upload_assistant_file
from assistant.views import mandate, home, assistant_form, assistant, phd_supervisor_review
from assistant.views import mandates_list, reviewer_mandates_list, reviewer_review, reviewer_delegation
from assistant.views import phd_supervisor_assistants_list
from assistant.views.history import ReviewHistoryView

urlpatterns = [
    path('', home.assistant_home, name='assistants_home'),
    path('access_denied', home.access_denied, name='access_denied'),
    path('api/get_persons/', get_persons.get_persons, name='get_persons'),

    path('autocomplete/', include([
        path("tutor/", autocomplete.TutorAutocomplete.as_view(), name="assistant_tutor_autocomplete")
    ])),


    path('assistant/', include([
        path('', assistant.AssistantMandatesListView.as_view(), name='assistant_mandates'),
        path('document_file/', include([
            re_path(r'^delete/(?P<document_file_id>\d+)/(?P<url>[\w\-]+)/$',
                upload_assistant_file.delete, name='assistant_file_delete'),
            path('download/<int:document_file_id>/', upload_assistant_file.download,
                name='assistant_file_download'),
            path('upload/', upload_assistant_file.save_uploaded_file, name='assistant_file_upload'),
        ])),
        path('export_pdf/', export_utils_pdf.export_mandate, name='export_mandate_pdf'),
        path('form/', include([
            path('part1/', include([
                path('edit/', assistant_form.form_part1_edit, name='form_part1_edit'),
                path('save/', assistant_form.form_part1_save, name='form_part1_save'),
            ])),
            path('part2/', include([
                path('get_learning_units_year/', autocomplete.LearningUnitYearAutocomplete.as_view(),
                    name='get_learning_units_year'),
                path('', assistant.AssistantLearningUnitsListView.as_view(),
                    name='mandate_learning_units'),
                path('add/', assistant_form.tutoring_learning_unit_add,
                    name='tutoring_learning_unit_add'),
                path('<int:tutoring_learning_unit_id>/delete/', assistant_form.tutoring_learning_unit_delete,
                    name='tutoring_learning_unit_delete'),
                path('<int:tutoring_learning_unit_id>/edit/', assistant_form.tutoring_learning_unit_edit,
                    name='tutoring_learning_unit_edit'),
                path('save/', assistant_form.tutoring_learning_unit_save,
                    name='tutoring_learning_unit_save'),
            ])),
            path('part3/', include([
                path('edit/', assistant_form.form_part3_edit, name='form_part3_edit'),
                path('save/', assistant_form.form_part3_save, name='form_part3_save'),
            ])),
            path('part4/', include([
                path('edit/', assistant_form.form_part4_edit, name='form_part4_edit'),
                path('save/', assistant_form.form_part4_save, name='form_part4_save'),
            ])),
            path('part5/', include([
                path('edit/', assistant_form.form_part5_edit, name='form_part5_edit'),
                path('save/', assistant_form.form_part5_save, name='form_part5_save'),
            ])),
            path('part6/', include([
                path('edit/', assistant_form.form_part6_edit, name='form_part6_edit'),
                path('save/', assistant_form.form_part6_save, name='form_part6_save'),
            ])),
        ])),
        path('mandate/', include([
            path('change_state/', assistant.mandate_change_state, name='mandate_change_state'),
            path('reviews/<int:mandate_id>/', assistant_mandate_reviews.reviews_view,
                name='assistant_mandate_reviews'),
        ])),
    ])),

    path('manager/', include([
        path('', home.manager_home, name='manager_home'),
        path('assistant_form/<int:mandate_id>/', manager_assistant_form.assistant_form_view,
            name='manager_assistant_form_view'),
        path('mandates/', include([
            path('', mandates_list.MandatesListView.as_view(), name='mandates_list'),
            path('edit/', include([
                path('', mandate.mandate_edit, name='mandate_read'),
                path('<int:mandate_id>/', mandate.mandate_edit, name='mandate_read'),
            ])),
            path('change_state/', mandate.mandate_change_state, name='assistant_mandate_change_state'),
            path('save/', mandate.mandate_save, name='mandate_save'),
            path('go_backward/', find_assistant_mandate_step_backward_state, name='assistant_mandate_step_back'),
            path('load/', mandate.load_mandates, name='load_mandates'),
            re_path(r'^delete/(?P<document_file_id>\d+)/(?P<url>[\w\-]+)/(?P<mandate_id>\d+)/',
                upload_assistant_file.delete, name='delete_pdf_file'),
            path('upload/', import_xls_file_data.upload_mandates_file, name='upload_mandates_file'),
            path('export/', mandate.export_mandates, name='export_mandates'),
            path('export_mandates_to_sap/', export_utils_pdf.export_mandates_to_sap,
                name='export_mandates_to_sap'),
            path('export_pdf/', export_utils_pdf.export_mandates, name='export_mandates_pdf'),
            path('export_list_declined_pdf/', export_utils_pdf.export_list_declined_mandates,
                name='export_list_declined_mandates_pdf'),
            path('export_declined_pdf/', export_utils_pdf.export_declined_mandates,
                name='export_declined_mandates_pdf'),
            path('download_declined_pdf/', export_utils_pdf.download_declined_mandates,
                name='download_declined_mandates_pdf'),
        ])),
        path('messages/', include([
            path('history/', mails.show_history, name='messages_history'),
            path('send/to_all_assistants/', mails.send_message_to_assistants, name='send_message_to_assistants'),
            path('send/to_reviewers/', mails.send_message_to_reviewers, name='send_message_to_reviewers'),
        ])),
        path('reviewers/', include([
            path('', reviewers_management.reviewers_index, name='reviewers_list'),
            path('action/', reviewers_management.reviewer_action, name="reviewer_action"),
            path('add/', reviewers_management.reviewer_add, name='reviewer_add'),
            path('replace/', reviewers_management.reviewer_replace, name='reviewer_replace'),
        ])),
        path('reviews/<int:mandate_id>/', manager_reviews_view.reviews_view, name='manager_reviews_view'),
        path("history/<uuid:uuid>/", ReviewHistoryView.as_view(), name="review_history"),
        path('settings/', include([
            path('edit/', manager_settings.settings_edit, name='settings_edit'),
            path('save/', manager_settings.settings_save, name='settings_save'),
        ])),
    ])),

    path('phd_supervisor/', include([
        path('assistants/', phd_supervisor_assistants_list.AssistantsListView.as_view(),
            name='phd_supervisor_assistants_list'),
        path('pst_form/', phd_supervisor_review.pst_form_view,
            name='phd_supervisor_pst_form_view'),
        path('review/', include([
            path('view/', phd_supervisor_review.review_view, name='phd_supervisor_review_view'),
            path('edit/', phd_supervisor_review.review_edit, name='phd_supervisor_review_edit'),
            path('save/', phd_supervisor_review.review_save,
                name='phd_supervisor_review_save'),
        ])),
    ])),

    path('reviewer/', include([
        path('', reviewer_mandates_list.MandatesListView.as_view(), {'filter': False},
            name='reviewer_mandates_list'),
        path('delegate/add/', reviewer_delegation.add_reviewer_for_structure,
            name='reviewer_delegation_add'),
        path('delegation/', reviewer_delegation.StructuresListView.as_view(), name='reviewer_delegation'),
        path('export_pdf/<int:year>/', export_utils_pdf.export_mandates_for_entity,
            name='export_mandates_for_entity_pdf'),
        path('pst_form/', reviewer_review.pst_form_view, name='pst_form_view'),
        path('review/', include([
            path('view/', reviewer_review.review_view, name='review_view'),
            path('edit/', reviewer_review.review_edit, name='review_edit'),
            path('save/', reviewer_review.review_save, name='review_save'),
        ])),
        path('todo/', reviewer_mandates_list.MandatesListView.as_view(), {'filter': True},
            name='reviewer_mandates_list_todo'),
    ])),
]
