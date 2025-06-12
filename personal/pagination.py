from rest_framework.pagination import PageNumberPagination


class EmpleadoPagination(PageNumberPagination):
    page_size = 5  # por defecto
    page_size_query_param = "page_size"
    max_page_size = 100
