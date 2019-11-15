from collections import OrderedDict

from rest_framework.authentication import SessionAuthentication

from wagtail.api.v2.utils import filter_page_type
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.core.models import Page

from .filters import ForExplorerFilter, HasChildrenFilter
from .serializers import AdminPageSerializer


class PagesAdminAPIViewSet(PagesAPIViewSet):
    base_serializer_class = AdminPageSerializer
    authentication_classes = [SessionAuthentication]

    # Add has_children and for_explorer filters
    filter_backends = PagesAPIViewSet.filter_backends + [
        HasChildrenFilter,
        ForExplorerFilter,
    ]

    meta_fields = PagesAPIViewSet.meta_fields + [
        'latest_revision_created_at',
        'status',
        'children',
        'descendants',
        'parent',
        'ancestors',
    ]

    body_fields = PagesAPIViewSet.body_fields + [
        'admin_display_title',
    ]

    listing_default_fields = PagesAPIViewSet.listing_default_fields + [
        'latest_revision_created_at',
        'status',
        'children',
        'admin_display_title',
    ]

    # Allow the parent field to appear on listings
    detail_only_fields = []

    known_query_parameters = PagesAPIViewSet.known_query_parameters.union([
        'for_explorer',
        'has_children'
    ])

    def get_root_page(self):
        """
        Returns the page that is used when the `&child_of=root` filter is used.
        """
        return Page.get_first_root_node()

    def get_base_queryset(self, models=None):
        """
        Returns a queryset containing all pages that can be seen by this user.

        This is used as the base for get_queryset and is also used to find the
        parent pages when using the child_of and descendant_of filters as well.
        """
        if models is None:
            models = [Page]

        if len(models) == 1:
            queryset = models[0].objects.all()
        else:
            queryset = Page.objects.all()

            # Filter pages by specified models
            queryset = filter_page_type(queryset, models)

        return queryset

    def get_queryset(self):
        queryset = super().get_queryset()

        # Hide root page
        # TODO: Add "include_root" flag
        queryset = queryset.exclude(depth=1).specific()

        return queryset

    def get_type_info(self):
        types = OrderedDict()

        for name, model in self.seen_types.items():
            types[name] = OrderedDict([
                ('verbose_name', model._meta.verbose_name),
                ('verbose_name_plural', model._meta.verbose_name_plural),
            ])

        return types

    def listing_view(self, request):
        response = super().listing_view(request)
        response.data['__types'] = self.get_type_info()
        return response

    def detail_view(self, request, pk):
        response = super().detail_view(request, pk)
        response.data['__types'] = self.get_type_info()
        return response