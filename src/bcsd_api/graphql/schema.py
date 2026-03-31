import logging
from typing import List

import strawberry
from graphql import GraphQLError
from strawberry.types import ExecutionContext

from bcsd_api.domain.apply import resolver as apply_resolvers
from bcsd_api.domain.apply.types import (
    BatchResult,
    MyApplication,
    PagedApplications,
)
from bcsd_api.global_.exception.base import AppException
from bcsd_api.domain.form import resolver as form_resolvers
from bcsd_api.domain.form.types import FormTemplateType
from bcsd_api.domain.member import resolver as member_resolvers
from bcsd_api.domain.member.types import (
    FiltersType,
    MeType,
    MemberDetailType,
    PagedMembers,
)
from bcsd_api.domain.recruit import resolver as recruit_resolvers
from bcsd_api.domain.recruit.types import RecruitmentPeriodType
from bcsd_api.domain.setting import resolver as setting_resolvers
from bcsd_api.domain.shorten import resolver as link_resolvers
from bcsd_api.domain.shorten.types import (
    LinkDetailType,
    LinkFiltersType,
    LinkType,
    PagedLinks,
)

from .errors import AppErrorExtension


@strawberry.type
class Query:
    @strawberry.field
    def health(self) -> str:
        return "ok"

    members: PagedMembers = strawberry.field(resolver=member_resolvers.resolve_members)
    member: MemberDetailType = strawberry.field(resolver=member_resolvers.resolve_member)
    member_filters: FiltersType = strawberry.field(resolver=member_resolvers.resolve_filters)
    tracks: list[str] = strawberry.field(resolver=member_resolvers.resolve_tracks)
    me: MeType = strawberry.field(resolver=member_resolvers.resolve_me)

    links: PagedLinks = strawberry.field(resolver=link_resolvers.resolve_links)
    link: LinkDetailType = strawberry.field(resolver=link_resolvers.resolve_link)
    link_filters: LinkFiltersType = strawberry.field(resolver=link_resolvers.resolve_link_filters)

    setting: str | None = strawberry.field(resolver=setting_resolvers.resolve_setting)

    periods: list[RecruitmentPeriodType] = strawberry.field(resolver=recruit_resolvers.resolve_periods)
    recruitment_period: RecruitmentPeriodType | None = strawberry.field(resolver=recruit_resolvers.resolve_recruitment_period)

    form_template: FormTemplateType | None = strawberry.field(resolver=form_resolvers.resolve_form_template)
    forms: list[FormTemplateType] = strawberry.field(resolver=form_resolvers.resolve_forms)

    my_application: MyApplication | None = strawberry.field(resolver=apply_resolvers.resolve_my_application)
    applications: PagedApplications = strawberry.field(resolver=apply_resolvers.resolve_applications)


@strawberry.type
class Mutation:
    create_link: LinkType = strawberry.mutation(resolver=link_resolvers.resolve_create)
    update_link: LinkType = strawberry.mutation(resolver=link_resolvers.resolve_update)
    toggle_link: LinkType = strawberry.mutation(resolver=link_resolvers.resolve_toggle)
    delete_link: bool = strawberry.mutation(resolver=link_resolvers.resolve_delete)

    set_setting: bool = strawberry.mutation(resolver=setting_resolvers.resolve_set_setting)

    create_period: RecruitmentPeriodType = strawberry.mutation(resolver=recruit_resolvers.resolve_create_period)
    update_period: RecruitmentPeriodType = strawberry.mutation(resolver=recruit_resolvers.resolve_update_period)

    create_form: FormTemplateType = strawberry.mutation(resolver=form_resolvers.resolve_create_form)
    update_form: FormTemplateType = strawberry.mutation(resolver=form_resolvers.resolve_update_form)

    submit_application: MyApplication = strawberry.mutation(resolver=apply_resolvers.resolve_submit)
    cancel_application: MyApplication = strawberry.mutation(resolver=apply_resolvers.resolve_cancel)
    approve_application: MyApplication = strawberry.mutation(resolver=apply_resolvers.resolve_approve)
    batch_approve_applications: BatchResult = strawberry.mutation(resolver=apply_resolvers.resolve_batch_approve)


logger = logging.getLogger("strawberry.execution")


class _Schema(strawberry.Schema):
    def process_errors(self, errors: List[GraphQLError], execution_context: ExecutionContext | None = None) -> None:
        for err in errors:
            if not err.original_error:
                continue
            if isinstance(err.original_error, AppException):
                continue
            logger.error(err.message, exc_info=err.original_error)


schema = _Schema(
    query=Query,
    mutation=Mutation,
    extensions=[AppErrorExtension],
)
