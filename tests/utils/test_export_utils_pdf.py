##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
import functools
import operator

from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph

from assistant.models import tutoring_learning_unit_year
from assistant.models.enums import assistant_mandate_state, assistant_phd_inscription, assistant_type, \
    assistant_mandate_renewal, review_status, reviewer_role
from assistant.tests.factories.academic_assistant import AcademicAssistantFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.tests.factories.manager import ManagerFactory
from assistant.tests.factories.mandate_entity import MandateEntityFactory
from assistant.tests.factories.review import ReviewFactory
from assistant.tests.factories.reviewer import ReviewerFactory
from assistant.tests.factories.settings import SettingsFactory
from assistant.tests.factories.tutoring_learning_unit_year import TutoringLearningUnitYearFactory
from assistant.utils import export_utils_pdf
from base.models.entity import find_versions_from_entites
from base.models.enums import entity_type
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory

COLS_WIDTH_FOR_REVIEWS = [35*mm, 20*mm, 70*mm, 30*mm, 30*mm]
COLS_WIDTH_FOR_TUTORING = [40*mm, 15*mm, 15*mm, 15*mm, 15*mm, 15*mm, 15*mm, 15*mm, 40*mm]
HTTP_OK = 200
HTTP_FOUND = 302


class ExportPdfTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.settings = SettingsFactory()
        cls.manager = ManagerFactory()
        cls.current_academic_year = AcademicYearFactory(current=True)
        cls.supervisor = PersonFactory()
        cls.assistant = AcademicAssistantFactory(
            phd_inscription_date=datetime.date(cls.current_academic_year.year - 3, 10, 2),
            thesis_title='Data fitting on manifolds',
            confirmation_test_date=datetime.date(cls.current_academic_year.year - 1, 9, 14),
            remark="Deux co-promoteurs (l'application ne m'autorise à n'en renseigner qu'un)",
            supervisor=cls.supervisor
        )

        cls.styles = getSampleStyleSheet()
        cls.styles.add(ParagraphStyle(
            name='Tiny',
            fontSize=6,
            font='Helvetica',
            leading=8,
            leftIndent=0,
            rightIndent=0,
            firstLineIndent=0,
            alignment=TA_LEFT,
            spaceBefore=0,
            spaceAfter=0,
            splitLongWords=1,
        ))
        cls.reviewer3 = ReviewerFactory()

    def setUp(self):
        self.mandate = AssistantMandateFactory(
            assistant=self.assistant,
            assistant_type=assistant_type.ASSISTANT,
            sap_id='1120019',
            entry_date=datetime.date(self.current_academic_year.year - 6, 9, 15),
            end_date=datetime.date(self.current_academic_year.year, 9, 24),
            contract_duration='6 ans',
            contract_duration_fte='6 ans',
            fulltime_equivalent=1,
            other_status=None,
            renewal_type=assistant_mandate_renewal.NORMAL,
            justification=None,
            external_contract='',
            external_functions='',
        )

        self.mandate2 = AssistantMandateFactory(
            state=assistant_mandate_state.DECLINED,
            academic_year=self.current_academic_year
        )
        self.mandate3 = AssistantMandateFactory(
            state=assistant_mandate_state.DECLINED,
            academic_year=self.current_academic_year
        )
        self.tutoring_learning_unit_year = TutoringLearningUnitYearFactory(mandate=self.mandate)
        self.review3 = ReviewFactory(
            mandate=self.mandate,
            reviewer=None
        )
        self.entity_version = EntityVersionFactory()
        self.mandate_entity = MandateEntityFactory(
            assistant_mandate=self.mandate,
            entity=self.entity_version.entity
        )
        self.entity_version2 = EntityVersionFactory(
            entity_type=entity_type.FACULTY,
            end_date=None
        )
        self.mandate_entity2 = MandateEntityFactory(
            assistant_mandate=self.mandate,
            entity=self.entity_version2.entity
        )
        self.reviewer = ReviewerFactory(
            role=reviewer_role.SUPERVISION,
            entity=self.mandate_entity.entity
        )

        self.reviewer2 = ReviewerFactory(
            entity=self.mandate_entity2.entity
        )
        self.review1 = ReviewFactory(
            mandate=self.mandate,
            reviewer=self.reviewer
        )
        self.review2 = ReviewFactory(
            mandate=self.mandate,
            reviewer=self.reviewer2,
            status=review_status.IN_PROGRESS
        )
        self.review3 = ReviewFactory(
            mandate=self.mandate,
            reviewer=None
        )
        
    def test_export_mandate(self):
        self.client.force_login(self.assistant.person.user)
        response = self.client.post('/assistants/assistant/export_pdf/', {'mandate_id': self.mandate.id})
        self.assertEqual(HTTP_OK, response.status_code)

    def test_export_mandates(self):
        self.client.force_login(self.manager.person.user)
        response = self.client.post('/assistants/manager/mandates/export_pdf/')
        self.assertEqual(HTTP_OK, response.status_code)

    def test_export_mandates_to_sap(self):
        self.client.force_login(self.manager.person.user)
        response = self.client.post('/assistants/manager/mandates/export_mandates_to_sap/')
        self.assertEqual(HTTP_OK, response.status_code)

    def test_export_declined_mandates(self):
        self.client.force_login(self.manager.person.user)
        response = self.client.post('/assistants/manager/mandates/export_declined_pdf/')
        self.assertEqual(HTTP_OK, response.status_code)

    def test_export_mandates_for_entity(self):
        self.client.force_login(self.reviewer2.person.user)
        response = self.client.get(reverse("export_mandates_for_entity_pdf", args=[self.mandate.academic_year.year]))
        self.assertEqual(HTTP_OK, response.status_code)

    def test_export_mandates_for_entity_with_no_entity(self):
        self.client.force_login(self.reviewer3.person.user)
        response = self.client.get(reverse("export_mandates_for_entity_pdf", args=[self.mandate.academic_year.year]))
        self.assertEqual(HTTP_FOUND, response.status_code)

    def test_format_data(self):
        data = 'good example of data.'
        title = 'formations'
        self.assertEqual("<strong>%s :</strong> %s<br />" % (_(title), data), export_utils_pdf.format_data(data, title))

    def test_create_paragraph(self):
        data = 'good example of data.'
        title = 'formations'
        subtitle = 'my subtitle'
        style = self.styles['BodyText']
        paragraph = Paragraph("<font size=14><strong>" + title + "</strong></font>" +
                              subtitle + "<br />" + data, style)
        self.assertEqual(str(export_utils_pdf.create_paragraph(title, data, style, subtitle)), str(paragraph))

    def test_get_administrative_data(self):
        format_data_parameters_list = [
            (self.mandate.get_state_display(), _("Renewal state"), True),
            (dict(assistant_type.ASSISTANT_TYPES).get(self.mandate.assistant_type), _('Assistant type')),
            (self.mandate.sap_id, _('Registration number')),
            (self.mandate.entry_date, _('Contract start date')),
            (self.mandate.end_date, _('Contract end date')),
            (self.mandate.contract_duration, _('Contract length')),
            (self.mandate.contract_duration_fte, _('Full-time equivalent')),
            (int(self.mandate.fulltime_equivalent * 100), _('Percentage of occupancy')),
            (self.mandate.other_status, _('Other status')),
            (
                dict(assistant_mandate_renewal.ASSISTANT_MANDATE_RENEWAL_TYPES).get(self.mandate.renewal_type),
                _('Renewal type')
            ),
            (
                self.mandate.justification,
                _("Should you no longer fulfill the requirements for a 'normal' renewal, can you specify the "
                  "circumstances justifying an exceptional renewal application (art. 51 of the RAMCS)")
            ),
            (self.mandate.external_contract, _('Mandate requested externally (FNRS, FRIA, ...)')),
            (
                self.mandate.external_functions,
                _('Current positions outside the University and %% of time spent')
            )
        ]
        formated_datas = (export_utils_pdf.format_data(*parameters) for parameters in format_data_parameters_list)
        mandate_content_expected = functools.reduce(operator.add, formated_datas, "")

        self.assertEqual(
            mandate_content_expected,
            export_utils_pdf.get_administrative_data(self.mandate)
        )

    def test_get_entities(self):
        entities_id = self.mandate.mandateentity_set.all().order_by('id').values_list('entity', flat=True)
        entities = find_versions_from_entites(entities_id, self.mandate.academic_year.start_date)
        entities_data = ""
        for entity in entities:
            entities_data += "<strong>{} : </strong>{}<br />".format(
                dict(entity_type.ENTITY_TYPES).get(entity.entity_type),
                entity.acronym
            )
        self.assertEqual(entities_data, export_utils_pdf.get_entities(self.mandate))

    def test_get_absences(self):
        self.assertEqual(self.mandate.absences if self.mandate.absences else "",
                         export_utils_pdf.get_absences(self.mandate))

    def test_get_comment(self):
        self.assertEqual(self.mandate.comment if self.mandate.comment else "",
                         export_utils_pdf.get_comment(self.mandate))

    def test_get_phd_data(self):
        thesis_title = export_utils_pdf.format_data(self.assistant.thesis_title, _('Title (provisional) of the thesis'))
        phd_inscription_date = export_utils_pdf.format_data(self.assistant.phd_inscription_date,
                                                            _('Date of doctoral enrollment'))
        confirmation_test_date = export_utils_pdf.format_data(self.assistant.confirmation_test_date,
                                                              _('Programmed date of confirmation test'))
        succed_confirmation_test_date = export_utils_pdf.format_data(
            self.assistant.succeed_confirmation_test_date, _('Date of succeeded confirmation test')
        )
        thesis_date = export_utils_pdf.format_data(self.assistant.thesis_date,
                                                   _('Date of defense of thesis (if already known)'))
        expected_phd_date = export_utils_pdf.format_data(self.assistant.expected_phd_date,
                                                         _('Scheduled date of registration'))
        inscription = export_utils_pdf.format_data(
            dict(assistant_phd_inscription.PHD_INSCRIPTION_CHOICES).get(self.assistant.inscription, ''),
            _('Enrolled in the Ph.D. program')
        )
        remark = export_utils_pdf.format_data(self.assistant.remark, _('Remark'))
        self.assertEqual(
            inscription + phd_inscription_date + expected_phd_date + confirmation_test_date
            + succed_confirmation_test_date + thesis_title + thesis_date + remark,
            export_utils_pdf.get_phd_data(self.assistant)
        )

    def test_get_research_data(self):
        internships = export_utils_pdf.format_data(self.mandate.internships, _('Scientific stay(s) and/or course(s)'))
        conferences = export_utils_pdf.format_data(
            self.mandate.conferences,
            _('Conference(s) to which I have contributed by communication or post, alone or with others.')
        )
        publications = export_utils_pdf.format_data(self.mandate.publications, _('Publication(s) in preparation'))
        awards = export_utils_pdf.format_data(self.mandate.awards, _('Prize(s) and/or distinction(s)'))
        framing = export_utils_pdf.format_data(self.mandate.framing, _('Participation in thesis and/or dissertation'))
        remark = export_utils_pdf.format_data(self.mandate.remark, _('Remark'))
        self.assertEqual(internships + conferences + publications + awards + framing + remark,
                         export_utils_pdf.get_research_data(self.mandate))

    def test_get_representation_activities(self):
        faculty_representation = export_utils_pdf.format_data(
            str(self.mandate.faculty_representation),
            _('Within the faculty (program committees, faculty board, faculty council)')
        )
        institute_representation = export_utils_pdf.format_data(
            str(self.mandate.institute_representation),
            _('Within the institute (institute board, institute council,...)')
        )
        sector_representation = export_utils_pdf.format_data(
            str(self.mandate.sector_representation),
            _('Within the sector (board and/or council)')
        )
        governing_body_representation = export_utils_pdf.format_data(
            str(self.mandate.governing_body_representation),
            _('Within the organs of the University (academic council, other councils or commissions,...)')
        )
        corsci_representation = export_utils_pdf.format_data(str(self.mandate.corsci_representation),
                                                             _('Within the CORSCI'))
        self.assertEqual(faculty_representation + institute_representation + sector_representation +
                         governing_body_representation + corsci_representation,
                         export_utils_pdf.get_representation_activities(self.mandate))

    def test_get_summary(self):
        report_remark = export_utils_pdf.format_data(self.mandate.activities_report_remark,
                                                     _('Remark concerning the activity report'))
        self.assertEqual(report_remark, export_utils_pdf.get_summary(self.mandate))

    def test_get_service_activities(self):
        students_service = export_utils_pdf.format_data(
            str(self.mandate.students_service),
            _('Information for future students (CIO, shows, Campus Days, Midi Masters,...)')
        )
        infrastructure_mgmt_service = export_utils_pdf.format_data(
            str(self.mandate.infrastructure_mgmt_service),
            _('Management of collective facilities (lab, workshop, library, IT department, website,...)')
        )
        events_organisation_service = export_utils_pdf.format_data(
            str(self.mandate.events_organisation_service),
            _("Organization of seminars, conferences, visits, study tours, grounds, seminars… (not taken in account in "
              "the 'Teaching units' section)")
        )
        publishing_field_service = export_utils_pdf.format_data(
            str(self.mandate.publishing_field_service),
            _('Activities in the field of publishing (editorial board,...)')
        )
        scientific_jury_service = export_utils_pdf.format_data(
            str(self.mandate.scientific_jury_service),
            _('Participation in juries and/or scientific committees')
        )
        self.assertEqual(students_service + infrastructure_mgmt_service + events_organisation_service +
                         publishing_field_service + scientific_jury_service,
                         export_utils_pdf.get_service_activities(self.mandate))

    def test_get_formation_activities(self):
        formations = export_utils_pdf.format_data(
            self.mandate.formations,
            _('Scientific, pedagogical or other training you have attended (LLL, SMCS, RHUM, Summer School)')
        )
        self.assertEqual(formations, export_utils_pdf.get_formation_activities(self.mandate))

    def test_generate_headers(self):
        style = self.styles['BodyText']
        data = []
        titles = [
            'Course units', 'Academic year', 'Number of sessions planned for this course', 'Duration of a session (h)',
            'Number of series', 'Number of face-to-face hours', 'Number of students per series',
            'Preparation, coordination and evaluation (h)', 'Other types of services associated with this course'
        ]
        for title in titles:
            data.append(Paragraph("%s" % _(title), style))
        self.assertEqual(str([data]), str(export_utils_pdf.generate_headers(titles, style)))

    def test_get_tutoring_learning_unit_year(self):
        style = self.styles['Tiny']
        data = export_utils_pdf.generate_headers([
            'Course units', 'Academic year', 'Number of sessions planned for this course', 'Duration of a session (h)',
            'Number of series', 'Number of face-to-face hours', 'Number of students per series',
            'Preparation, coordination and evaluation (h)', 'Other types of services associated with this course'
        ], style)
        tutoring_learning_units_year = tutoring_learning_unit_year.find_by_mandate(self.mandate)
        for this_tutoring_learning_unit_year in tutoring_learning_units_year:
            academic_year = str(this_tutoring_learning_unit_year.learning_unit_year.academic_year)
            data.append([Paragraph(this_tutoring_learning_unit_year.learning_unit_year.complete_title + " (" +
                                   this_tutoring_learning_unit_year.learning_unit_year.acronym + ")", style),
                         Paragraph(academic_year, style),
                         Paragraph(str(this_tutoring_learning_unit_year.sessions_number), style),
                         Paragraph(str(this_tutoring_learning_unit_year.sessions_duration), style),
                         Paragraph(str(this_tutoring_learning_unit_year.series_number), style),
                         Paragraph(str(this_tutoring_learning_unit_year.face_to_face_duration), style),
                         Paragraph(str(this_tutoring_learning_unit_year.attendees), style),
                         Paragraph(str(this_tutoring_learning_unit_year.exams_supervision_duration), style),
                         Paragraph(this_tutoring_learning_unit_year.others_delivery or '', style)
                         ])
        self.assertEqual(str(data), str(export_utils_pdf.get_tutoring_learning_unit_year(self.mandate, style)))
