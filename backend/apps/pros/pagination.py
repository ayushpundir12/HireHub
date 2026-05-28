from rest_framework.pagination import CursorPagination


class ProCursorPagination(CursorPagination):
    page_size          = 12
    ordering           = '-avg_rating'
    cursor_query_param = 'cursor'