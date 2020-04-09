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
import time
import zipfile
from io import BytesIO

from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.colors import black, HexColor
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Table, TableStyle

from assistant.business import users_access
from assistant.models import academic_assistant, assistant_mandate, review, reviewer, tutoring_learning_unit_year
from assistant.models.enums import review_status, assistant_type, user_role, assistant_mandate_renewal
from assistant.models.enums.assistant_phd_inscription import PHD_INSCRIPTION_CHOICES
from assistant.models.review import find_before_mandate_state
from assistant.utils import assistant_access, manager_access
from base.models import academic_year, entity_version
from base.models.entity import find_versions_from_entites
from base.models.enums import entity_type
from base.models.person import find_by_user
from osis_common.decorators.download import set_download_cookie

PAGE_SIZE = A4
MARGIN_SIZE = 15 * mm
COLS_WIDTH_FOR_REVIEWS = [35*mm, 20*mm, 70*mm, 30*mm, 30*mm]
COLS_WIDTH_FOR_DECLINED_MANDATES = [100*mm]
COLS_WIDTH_FOR_TUTORING = [40*mm, 15*mm, 15*mm, 15*mm, 15*mm, 15*mm, 15*mm, 15*mm, 40*mm]


@user_passes_test(manager_access.user_is_manager, login_url='access_denied')
def export_mandates_to_sap(request):
    mandates = assistant_mandate.find_by_academic_year_by_excluding_declined(academic_year.starting_academic_year())
    response = HttpResponse(content_type='application/zip')
    filename = ('%s_%s_%s.zip' % (_('assistants_mandates'), mandates[0].academic_year, time.strftime("%Y%m%d_%H%M")))
    response['Content-Disposition'] = 'filename="%s"' % filename
    buffer = BytesIO()
    zip_file = zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED)
    for mandate in mandates:
        file = build_doc(request, mandates=[mandate], type='export_to_sap')
        zip_file.writestr(
            ('%s_%s_%s.pdf' % (mandate.sap_id, mandate.academic_year, mandate.assistant.person.last_name)),
            file.content
        )
    zip_file.close()
    buffer.flush()
    ret_zip = buffer.getvalue()
    buffer.close()
    response.write(ret_zip)
    return response


@login_required
@set_download_cookie
def build_doc(request, mandates, type='default'):
    if mandates:
        year = mandates[0].academic_year
    else:
        year = academic_year.starting_academic_year()
    if type is 'export_to_sap':
        filename = ('%s_%s_%s.pdf' % (mandates[0].sap_id, year, mandates[0].assistant.person))
    else:
        filename = ('%s_%s_%s.pdf' % (_('assistants_mandates'), year, time.strftime("%Y%m%d_%H%M")))
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=PAGE_SIZE, rightMargin=MARGIN_SIZE, leftMargin=MARGIN_SIZE, topMargin=70,
                            bottomMargin=25)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Tiny', fontSize=6, font='Helvetica', leading=8, leftIndent=0, rightIndent=0,
                              firstLineIndent=0, alignment=TA_LEFT, spaceBefore=0, spaceAfter=0, splitLongWords=1, ))
    styles.add(ParagraphStyle(name='StandardWithBorder', font='Helvetica', leading=18, leftIndent=10, rightIndent=10,
                              firstLineIndent=0, alignment=TA_JUSTIFY, spaceBefore=25, spaceAfter=5, splitLongWords=1,
                              borderColor='#000000', borderWidth=1, borderPadding=10, ))
    content = []
    roles = []
    if academic_assistant.find_by_person(find_by_user(request.user)):
        roles = [user_role.ASSISTANT]
    elif reviewer.find_by_person(find_by_user(request.user)):
        roles = reviewer.find_by_person(find_by_user(request.user)).values_list("role", flat=True)
    else:
        roles = [user_role.ADMINISTRATOR]
    if type is 'default' or type is 'export_to_sap':
        for mandate in mandates:
            add_mandate_content(content, mandate, styles, roles)
    else:
        content.append(create_paragraph("%s (%s)<br />" % (_('Assistants who have declined their renewal'), year),
                                        '',
                                        styles["BodyText"])
                       )
        if mandates:
            write_table(content, add_declined_mandates(mandates, styles['Tiny']), COLS_WIDTH_FOR_DECLINED_MANDATES)
            content.append(PageBreak())
    doc.build(content, add_header_footer)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


@require_http_methods(["POST"])
@user_passes_test(assistant_access.user_is_assistant_and_procedure_is_open, login_url='access_denied')
def export_mandate(request):
    mandate_id = request.POST.get("mandate_id")
    mandate = assistant_mandate.find_mandate_by_id(mandate_id)
    return build_doc(request, mandates=[mandate])


@user_passes_test(manager_access.user_is_manager, login_url='access_denied')
def export_mandates(request):
    mandates = assistant_mandate.find_by_academic_year_by_excluding_declined(academic_year.starting_academic_year())
    return build_doc(request, mandates)


@user_passes_test(manager_access.user_is_manager, login_url='access_denied')
def export_declined_mandates(request):
    mandates = assistant_mandate.find_declined_by_academic_year(academic_year.starting_academic_year())
    return build_doc(request, mandates, type='declined')


def add_declined_mandates(mandates, style):
    data = generate_headers(["%s" % (_('Assistant'))], style)
    for mandate in mandates:
        person = "{} {}".format(
            mandate.assistant.person.first_name,
            mandate.assistant.person.last_name,
        )
        data.append([Paragraph(person, style)])
    return data


@user_passes_test(users_access.user_is_reviewer_and_procedure_is_open, login_url='access_denied')
def export_mandates_for_entity(request, year):
    mandates = assistant_mandate.AssistantMandate.objects.filter(
        mandateentity__entity__in=reviewer.find_by_person(find_by_user(request.user)).values_list("entity", flat=True),
        academic_year=academic_year.find_academic_year_by_year(year)
    ).order_by(
        'assistant__person__last_name'
    )
    if mandates:
        return build_doc(request, mandates)
    return HttpResponseRedirect(reverse('reviewer_mandates_list'))


def add_mandate_content(content, mandate, styles, current_user_roles):
    content.append(
        create_paragraph(
            "%s (%s)" % (mandate.assistant.person, mandate.academic_year),
            get_administrative_data(mandate),
            styles['StandardWithBorder']
        )
    )
    content.append(create_paragraph("%s" % (_('Entities')), get_entities(mandate), styles['StandardWithBorder']))
    content.append(create_paragraph("<strong>%s</strong>" % (_('Absences')), get_absences(mandate),
                                    styles['StandardWithBorder']))
    content.append(create_paragraph("<strong>%s</strong>" % (_('Comment')), get_comment(mandate),
                                    styles['StandardWithBorder']))
    content.append(PageBreak())
    if mandate.assistant_type == assistant_type.ASSISTANT:
        content.append(create_paragraph("%s" % (_('Ph.D.')), get_phd_data(mandate.assistant),
                                        styles['StandardWithBorder']))
        content.append(create_paragraph("%s" % (_('Research')), get_research_data(mandate),
                                        styles['StandardWithBorder']))
        content.append(PageBreak())
    content.append(create_paragraph("%s<br />" % (_('Course units')), '', styles["BodyText"]))
    write_table(content, get_tutoring_learning_unit_year(mandate, styles['Tiny']), COLS_WIDTH_FOR_TUTORING)
    content.append(PageBreak())
    content.append(create_paragraph("%s" % (_('Representation activities at UCL')),
                                    get_representation_activities(mandate),
                                    styles['StandardWithBorder'], " (%s)" % (_('number of hours per year'))))
    content.append(create_paragraph("%s" % (_('Service activities')), get_service_activities(mandate),
                                    styles['StandardWithBorder'], " (%s)" % (_('number of hours per year'))))
    content.append(create_paragraph("%s" % (_('Training activities')), get_formation_activities(mandate),
                                    styles['StandardWithBorder']))
    content.append(PageBreak())
    content.append(create_paragraph("%s" % (_('Summary')), get_summary(mandate), styles['StandardWithBorder']))
    content += [draw_time_repartition(mandate)]
    content.append(PageBreak())
    if user_role.ASSISTANT not in current_user_roles:
        content.append(create_paragraph("%s<br />" % (_('Opinions')), '', styles["BodyText"]))
        if user_role.ADMINISTRATOR in current_user_roles:
            reviews = review.find_by_mandate(mandate.id)
        else:
            reviews = find_before_mandate_state(mandate, current_user_roles)
        for rev in reviews:
            if rev.status == review_status.IN_PROGRESS:
                break
            content.append(create_paragraph(
                str(_(rev.advice)),
                get_review_details_for_mandate(mandate, rev),
                styles['StandardWithBorder'])
            )
        content.append(PageBreak())


def format_data(data, title):
    if isinstance(data, datetime.date):
        data = data.strftime("%d-%m-%Y")
    return "<strong>%s :</strong> %s<br />" % (title, data) \
        if data and data != 'None' else "<strong>%s :</strong><br />" % (title)


def create_paragraph(title, data, style, subtitle=''):
    paragraph = Paragraph("<font size=14><strong>" + title + "</strong></font>" +
                          subtitle + "<br />" + data, style)
    return paragraph


def get_summary(mandate):
    report_remark = format_data(mandate.activities_report_remark, _('Remark concerning the activity report'))
    return report_remark


def get_administrative_data(mandate):
    assistant_type_name = format_data(dict(assistant_type.ASSISTANT_TYPES)[mandate.assistant_type],
                                      _('Assistant type'))
    matricule = format_data(mandate.sap_id, _('Registration number'))
    entry_date = format_data(mandate.entry_date, _('Contract start date'))
    end_date = format_data(mandate.end_date, _('Contract end date'))
    contract_duration = format_data(mandate.contract_duration, _('Contract length'))
    contract_duration_fte = format_data(mandate.contract_duration_fte, _('Full-time equivalent'))
    fulltime_equivalent = format_data(int(mandate.fulltime_equivalent * 100), _('Percentage of occupancy'))
    other_status = format_data(mandate.other_status, _('Other status'))
    renewal_type = format_data(_(dict(assistant_mandate_renewal.ASSISTANT_MANDATE_RENEWAL_TYPES)[mandate.renewal_type]),
                               _('Renewal type'))
    justification = format_data(
        mandate.justification,
        _("Should you no longer fulfill the requirements for a 'normal' renewal, can you specify the circumstances "
          "justifying an exceptional renewal application (art. 51 of the RAMCS)")
    )
    external_contract = format_data(mandate.external_contract, _('Mandate requested externally (FNRS, FRIA, ...)'))
    external_functions = format_data(mandate.external_functions,
                                     _('Current positions outside the University and %% of time spent'))

    return assistant_type_name + matricule + entry_date + end_date + contract_duration + contract_duration_fte \
           + fulltime_equivalent + other_status + renewal_type + justification + external_contract + external_functions


def get_entities(mandate):
    start_date = academic_year.starting_academic_year().start_date
    entities_id = mandate.mandateentity_set.all().order_by('id').values_list('entity', flat=True)
    entities = find_versions_from_entites(entities_id, start_date)
    entities_data = ""
    for entity in entities:
        entities_data += "<strong>{} : </strong>{}<br />".format(dict(entity_type.ENTITY_TYPES)[entity.entity_type],
                                                                 entity.acronym)
    return entities_data


def get_absences(mandate):
    return mandate.absences if mandate.absences and mandate.absences != 'None' else ""


def get_comment(mandate):
    return mandate.comment if mandate.comment and mandate.comment != 'None' else ""


def get_phd_data(assistant):
    thesis_title = format_data(assistant.thesis_title, _('Title (provisional) of the thesis'))
    phd_inscription_date = format_data(assistant.phd_inscription_date, _('Date of doctoral enrollment'))
    confirmation_test_date = format_data(assistant.confirmation_test_date, _('Date of confirmation test'))
    thesis_date = format_data(assistant.thesis_date, _('Date of defense of thesis (if already known)'))
    expected_phd_date = format_data(assistant.expected_phd_date, _('Scheduled date of registration'))
    inscription = format_data(
        _(dict(PHD_INSCRIPTION_CHOICES)[assistant.inscription]) if assistant.inscription else None,
        _('Enrolled in the Ph.D. program')
    )
    remark = format_data(assistant.remark, _('Remark'))
    return inscription + phd_inscription_date + expected_phd_date + confirmation_test_date \
           + thesis_title + thesis_date + remark


def get_research_data(mandate):
    internships = format_data(mandate.internships, _('Scientific stay(s) and/or course(s)'))
    conferences = format_data(
        mandate.conferences,
        _('Conference(s) to which I have contributed by communication or post, alone or with others.')
    )
    publications = format_data(mandate.publications, _('Publication(s) in preparation'))
    awards = format_data(mandate.awards, _('Prize(s) and/or distinction(s)'))
    framing = format_data(mandate.framing, _('Participation in thesis and/or dissertation'))
    remark = format_data(mandate.remark, _('Remark'))
    return internships + conferences + publications + awards + framing + remark


def get_tutoring_learning_unit_year(mandate, style):
    data = generate_headers([
        'Course units', 'Academic year', 'Number of sessions planned for this course', 'Duration of a session (h)',
        'Number of series', 'Number of face-to-face hours', 'Number of students per series',
        'Preparation, coordination and evaluation (h)', 'Other types of services associated with this course'
    ], style)
    tutoring_learning_units_year = tutoring_learning_unit_year.find_by_mandate(mandate)
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
                     Paragraph(this_tutoring_learning_unit_year.others_delivery[0:3500] or '', style)
                     ])
    return data


def generate_headers(titles, style):
    data = []
    for title in titles:
        data.append(Paragraph("%s" % _(title), style))
    return [data]


def get_representation_activities(mandate):
    faculty_representation = format_data(str(mandate.faculty_representation),
                                         _('Within the faculty (program committees, faculty board, faculty council)'))
    institute_representation = format_data(
        str(mandate.institute_representation),
        _('Within the institute (institute board, institute council,...)')
    )
    sector_representation = format_data(str(mandate.sector_representation),
                                        _('Within the sector (board and/or council)'))
    governing_body_representation = format_data(
        str(mandate.governing_body_representation),
        _('Within the organs of the University (academic council, other councils or commissions,...)')
    )
    corsci_representation = format_data(str(mandate.corsci_representation), _('Within the CORSCI'))
    return faculty_representation + institute_representation + sector_representation + governing_body_representation \
           + corsci_representation


def get_service_activities(mandate):
    students_service = format_data(str(mandate.students_service),
                                   _('Information for future students (CIO, shows, Campus Days, Midi Masters,...)'))
    infrastructure_mgmt_service = format_data(
        str(mandate.infrastructure_mgmt_service),
        _('Management of collective facilities (lab, workshop, library, IT department, website,...)')
    )
    events_organisation_service = format_data(
        str(mandate.events_organisation_service),
        _("Organization of seminars, conferences, visits, study tours, grounds, seminars… (not taken in account in "
          "the 'Teaching units' section)")
    )
    publishing_field_service = format_data(str(mandate.publishing_field_service),
                                           _('Activities in the field of publishing (editorial board,...)'))
    scientific_jury_service = format_data(str(mandate.scientific_jury_service),
                                          _('Participation in juries and/or scientific committees'))
    return students_service + infrastructure_mgmt_service + events_organisation_service + publishing_field_service \
           + scientific_jury_service


def get_formation_activities(mandate):
    return format_data(mandate.formations,
                       _('Scientific, pedagogical or other training you have attended (LLL, SMCS, RHUM, Summer School)')
                       )


def get_review_details_for_mandate(mandate, rev):
    if rev.reviewer is None:
        person = "{} {}<br/>({})".format(
            mandate.assistant.supervisor.first_name,
            mandate.assistant.supervisor.last_name,
            str(_('Promoter'))
        )
    else:
        person = "{} {}<br/>({})".format(
            rev.reviewer.person.first_name,
            rev.reviewer.person.last_name,
            entity_version.get_last_version(rev.reviewer.entity).acronym
        )
    reviewer = format_data(person, _('Reviewer'))
    remark = format_data(rev.remark, _('Remark'))
    justification = format_data(rev.justification, _('Justification'))
    confidential = format_data(rev.confidential, _('Confidential'))
    return reviewer + remark + justification + confidential


def write_table(content, data, cols_width):
    t = Table(data, cols_width, repeatRows=1)
    t.setStyle(TableStyle([
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), HexColor("#f6f6f6"))]))
    content.append(t)


def set_items(n, obj, attr, values):
    m = len(values)
    i = m // n
    for j in range(n):
        setattr(obj[j], attr, values[j*i % m])


def draw_time_repartition(mandate):
    drawing = Drawing(width=180*mm, height=120*mm)
    pdf_chart_colors = [HexColor("#fa9d00"), HexColor("#006884"), HexColor("#00909e"), HexColor("#ffd08d"), ]
    pie = Pie()
    pie.x = 60*mm
    pie.y = 35*mm
    pie.width = 60*mm
    pie.height = 60*mm
    pie.slices.strokeWidth = 0.5
    pie.slices.fontName = 'Helvetica'
    pie.slices.fontSize = 8
    pie.data = []
    pie.labels = []
    titles = []
    add_data_and_titles_to_pie(pie, titles, mandate.research_percent, 'Percentage for research and Ph.D.')
    add_data_and_titles_to_pie(pie, titles, mandate.tutoring_percent, 'Percentage for teaching')
    add_data_and_titles_to_pie(pie, titles, mandate.service_activities_percent, 'Percentage for service activities')
    add_data_and_titles_to_pie(pie, titles, mandate.formation_activities_percent,
                               'Percentage of involvement as beneficiary in training activities')
    if len(pie.data) > 0:
        drawing.add(pie)
        add_legend_to_pie(drawing)
        n = len(pie.data)
        set_items(n, pie.slices, 'fillColor', pdf_chart_colors)
        drawing.legend.colorNamePairs = \
            [(pie.slices[i].fillColor, (titles[i], '%0.f' % pie.data[i] + '%')) for i in range(n)]
    return drawing


def add_legend_to_pie(drawing):
    drawing.add(Legend(), name='legend')
    drawing.legend.x = 90
    drawing.legend.y = 50
    drawing.legend.dx = 8
    drawing.legend.dy = 8
    drawing.legend.fontName = 'Helvetica'
    drawing.legend.fontSize = 8
    drawing.legend.boxAnchor = 'w'
    drawing.legend.columnMaximum = 10
    drawing.legend.strokeWidth = 1
    drawing.legend.strokeColor = black
    drawing.legend.deltax = 75
    drawing.legend.deltay = 10
    drawing.legend.autoXPadding = 5
    drawing.legend.yGap = 0
    drawing.legend.dxTextSpace = 5
    drawing.legend.alignment = 'right'
    drawing.legend.dividerOffsY = 5
    drawing.legend.subCols.rpad = 30


def add_data_and_titles_to_pie(pie, titles, data, title):
    if data != 0:
        pie.data.append(data)
        pie.labels.append(str(data) + "%")
        titles.append(_(title))


def add_header_footer(canvas, doc):
    styles = getSampleStyleSheet()
    canvas.saveState()
    header_building(canvas, doc)
    footer_building(canvas, doc, styles)
    canvas.restoreState()


def header_building(canvas, doc):
    canvas.line(doc.leftMargin, 790, doc.width+doc.leftMargin, 790)
    canvas.drawString(110, 800, "%s" % (_('Assistant mandate renewal application processing')))


def footer_building(canvas, doc, styles):
    printing_date = timezone.now()
    printing_date = printing_date.strftime("%d/%m/%Y")
    pageinfo = "%s : %s" % (_('Printing date'), printing_date)
    footer = Paragraph(''' <para align=right>Page %d - %s </para>''' % (doc.page, pageinfo), styles['Normal'])
    w, h = footer.wrap(doc.width, doc.bottomMargin)
    footer.drawOn(canvas, doc.leftMargin, h)
