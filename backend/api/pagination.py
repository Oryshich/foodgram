from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'

    def get_page_size(self, request):
        res_page_size = request.query_params.get(self.page_size_query_param)
        if res_page_size is not None:
            return int(res_page_size)
        return super().get_page_size(request)
