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
import functools
from itertools import takewhile

from django.db import models
from django.db.models import Case, When, Value, IntegerField
from django.utils import timezone

from assistant.models.enums import review_status, review_advice_choices, reviewer_role


class Review(models.Model):
    mandate = models.ForeignKey('AssistantMandate', on_delete=models.CASCADE)
    reviewer = models.ForeignKey('Reviewer', null=True, on_delete=models.CASCADE)
    advice = models.CharField(max_length=20, choices=review_advice_choices.REVIEW_ADVICE_CHOICES)
    status = models.CharField(max_length=15, choices=review_status.REVIEW_STATUS_CHOICES, null=True)
    justification = models.TextField(null=True, blank=True)
    remark = models.TextField(null=True, blank=True)
    confidential = models.TextField(null=True, blank=True)
    comment_vice_rector = models.TextField(null=True, blank=True)
    changed = models.DateTimeField(default=timezone.now, null=True)


def find_by_id(review_id):
    return Review.objects.get(id=review_id)


def find_by_mandate(mandate_id):
    return Review.objects.filter(mandate=mandate_id).order_by('changed')


def find_review_for_mandate_by_role(mandate, role):
    return Review.objects.filter(mandate=mandate).filter(reviewer__role__icontains=role.split('_', 1)[0]).first()


def find_done_by_supervisor_for_mandate(mandate):
    return Review.objects.get(reviewer=None, mandate=mandate, status='DONE')


def get_in_progress_for_mandate(mandate):
    try:
        return Review.objects.get(mandate=mandate, status=review_status.IN_PROGRESS)
    except Review.DoesNotExist:
        return None


def find_before_mandate_state(mandate, current_roles):
    reviewers_order_list = [
        reviewer_role.RESEARCH,
        reviewer_role.SUPERVISION,
        reviewer_role.VICE_RECTOR
    ]
    roles_list_accessible_for_current_rev = [
        role for role in takewhile(lambda r: r not in current_roles, reviewers_order_list)
    ]
    roles_list_accessible_for_current_rev.append(
        next((role for role in reviewers_order_list if role in current_roles), None)
    )
    filter_clause = [
        models.Q(reviewer__role__contains=role) for role in roles_list_accessible_for_current_rev if role
    ]

    filter_clause_q = functools.reduce(lambda a, b: a | b, filter_clause, models.Q(reviewer__role=None))
    qs = Review.objects.filter(mandate=mandate).filter(
        filter_clause_q
    ).filter(
        status=review_status.DONE
    ).annotate(
        order_value=Case(
            When(reviewer__role=reviewer_role.PHD_SUPERVISOR, then=Value(1)),
            When(reviewer__role=reviewer_role.RESEARCH_ASSISTANT, then=Value(2)),
            When(reviewer__role=reviewer_role.RESEARCH, then=Value(3)),
            When(reviewer__role=reviewer_role.SUPERVISION_DAF_ASSISTANT, then=Value(4)),
            When(reviewer__role=reviewer_role.SUPERVISION_DAF, then=Value(5)),
            When(reviewer__role=reviewer_role.SUPERVISION_ASSISTANT, then=Value(6)),
            When(reviewer__role=reviewer_role.SUPERVISION, then=Value(7)),
            When(reviewer__role=reviewer_role.VICE_RECTOR_ASSISTANT_ASSISTANT, then=Value(8)),
            When(reviewer__role=reviewer_role.VICE_RECTOR_ASSISTANT, then=Value(9)),
            When(reviewer__role=reviewer_role.VICE_RECTOR, then=Value(10)),
            default=Value(0),
            output_field=IntegerField()
        )
    ).order_by("order_value")
    return qs
