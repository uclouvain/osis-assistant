import collections

from django.http import Http404
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from cms.models.translated_text import TranslatedText
from cms.models.translated_text_label import TranslatedTextLabel
from webservices.utils import to_int_or_404, convert_sections_to_list_of_dict

LANGUAGES = {'fr': 'fr-be', 'en': 'en'}
ENTITY = 'offer_year'

Context = collections.namedtuple(
    'Context',
    ['year', 'language', 'acronym',
     'title', 'description', 'translated_labels',
     'academic_year', 'education_group_year']
)


def find_translated_labels_for_entity_and_language(entity, language):
    queryset = TranslatedTextLabel.objects.filter(
        text_label__entity=entity, language=language)

    return {item.text_label.label: item.label for item in queryset}


def get_common_education_group(academic_year, language, acronym):
    education_group_year = EducationGroupYear.objects.filter(
        academic_year=academic_year, acronym__iexact=acronym).first()

    values = {}
    if education_group_year:
        queryset = TranslatedText.objects.filter(
            entity='offer_year',
            reference=education_group_year.id,
            language=language)

        for translated_text in queryset.order_by('text_label__order'):
            label = translated_text.text_label.label

            values[label] = translated_text

    return values


def get_cleaned_parameters(type_acronym):
    def wrapper(function):
        def inner_wrapper(request, year, language, acronym):
            year = to_int_or_404(year)

            if language not in LANGUAGES:
                raise Http404

            academic_year = get_object_or_404(AcademicYear, year=year)

            parameters = {
                'academic_year': academic_year,
                'partial_acronym__iexact' if type_acronym == 'partial' else 'acronym__iexact': acronym
            }

            education_group_year = get_object_or_404(EducationGroupYear, **parameters)
            iso_language = LANGUAGES[language]

            title = get_title_of_education_group_year(education_group_year, iso_language)
            translated_labels = find_translated_labels_for_entity_and_language(ENTITY, iso_language)
            
            description = new_description(education_group_year, language, title, year)

            if type_acronym == 'partial':
                description['partial_acronym'] = education_group_year.partial_acronym

            context = Context(
                year=year,
                language=iso_language,
                acronym=acronym,
                title=title,
                academic_year=academic_year,
                education_group_year=education_group_year,
                translated_labels=translated_labels,
                description=description
            )

            return function(request, context)
        return inner_wrapper
    return wrapper


@api_view(['GET'])
@renderer_classes((JSONRenderer,))
@get_cleaned_parameters(type_acronym='acronym')
def ws_catalog_offer(request, context):
    description = dict(context.description)

    sections = compute_sections_for_offer(context)
    description['sections'] = convert_sections_to_list_of_dict(sections)

    return Response(description, content_type='application/json')


def compute_sections_for_offer(context):
    sections = {}

    common_terms = get_common_education_group(context.academic_year, context.language, 'common')

    queryset = find_translated_texts_by_entity_and_language(
        context.education_group_year,
        ENTITY,
        context.language
    )

    for translated_text in queryset:
        insert_section(sections, translated_text, context)

    common_sections = [
        ('caap', 'caap'),
        ('programme', 'agregations'),
        ('prerequis', 'prerequis'),
        ('module_complementaire', 'module_complementaire')
    ]
    for name, common_term in common_sections:
        if name in sections and common_term in common_terms:
            term = common_terms[common_term]
            if name == 'programme':
                common_name = common_term
            else:
                common_name = '{name}-commun'.format(name=name)
            sections[common_name] = {
                'label': get_translated_label_from_translated_text(term),
                'content': term.text,
            }

    if context.acronym.lower().endswith('2m') and 'finalites_didactiques' in common_terms:
        term = common_terms['finalites_didactiques']
        sections['finalites_didactiques-commun'] = {
            'label': get_translated_label_from_translated_text(term),
            'content': term.text,
        }

    return sections

def insert_section(sections, translated_text, context):
    translated_label = get_label(context.translated_labels, translated_text)
    name = translated_text.text_label.label
    content = translated_text.text

    sections[name] = {
        'label': translated_label,
        'content': content
    }


def find_translated_texts_by_entity_and_language(education_group_year, entity, iso_language):
    queryset = TranslatedText.objects.filter(
        entity=entity,
        reference=education_group_year.id,
        language=iso_language)

    return queryset.order_by('text_label__order')


def new_description(education_group_year, language, title, year):
    return {
        'language': language,
        'acronym': education_group_year.acronym,
        'title': title,
        'year': year,
        'sections': [],
    }


def get_label(translated_labels, translated_text):
    label = translated_labels.get(translated_text.text_label.label)
    if not label:
        label = translated_text.text_label.label
        if label.startswith('welcome_'):
            label = label.split('_')[-1]
        label = ' '.join(label.title().split('_'))
    return label


@api_view(['GET'])
@renderer_classes((JSONRenderer,))
@get_cleaned_parameters(type_acronym='partial')
def ws_catalog_group(request, context):
    section_append = context.description['sections'].append

    queryset = find_translated_texts_by_entity_and_language(context.education_group_year,
                                                            ENTITY,
                                                            context.language)

    for translated_text in queryset:
        insert_section_group(section_append, context.translated_labels, translated_text)

    return Response(context.description, content_type='application/json')


def insert_section_group(section_append, translated_labels, translated_text):
    label = translated_labels.get(translated_text.text_label.label)
    content = translated_text.text
    name = translated_text.text_label.label
    section_append({
        'id': name,
        'label': label,
        'content': content,
    })


def get_title_of_education_group_year(education_group_year, iso_language):
    if iso_language == 'fr-be':
        title = education_group_year.title
    else:
        title = education_group_year.title_english
    return title


def get_translated_label_from_translated_text(translated_text):
    record = TranslatedTextLabel.objects.filter(text_label=translated_text.text_label).first()

    if record:
        return record.label
    else:
        return 'Unknown'
