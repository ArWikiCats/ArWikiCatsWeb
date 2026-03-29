from dataclasses import dataclass, field


@dataclass
class ViewLogsRequestHandler:
    page: int
    per_page: int
    order: str
    order_by: str
    day: str
    status: str
    like: str
    table_name: str
    offset: int = field(init=False)

    ALLOWED_ORDERS: frozenset = field(default_factory=lambda: frozenset({"ASC", "DESC"}), init=False, repr=False)
    ALLOWED_ORDER_BY: frozenset = field(
        default_factory=lambda: frozenset(
            {
                "id",
                "endpoint",
                "request_data",
                "response_status",
                "response_time",
                "response_count",
                "timestamp",
                "date_only",
            }
        ),
        init=False,
        repr=False,
    )
    ALLOWED_STATUS: frozenset = field(
        default_factory=lambda: frozenset({"no_result", "All", "Category"}),
        init=False,
        repr=False,
    )

    def __post_init__(self):
        self.page = max(1, self.page)
        self.per_page = max(1, min(200, self.per_page))
        self.order = self.order if self.order in self.ALLOWED_ORDERS else "DESC"
        self.order_by = self.order_by if self.order_by in self.ALLOWED_ORDER_BY else "timestamp"
        self.status = self.status if self.status in self.ALLOWED_STATUS else ""
        self.offset = (self.page - 1) * self.per_page

    @property
    def order_by_types(self) -> list[str]:
        """Return allowed order-by columns as a sorted list (for UI rendering)."""
        return sorted(self.ALLOWED_ORDER_BY)

    @property
    def status_table(self) -> list[str]:
        """Allowed status values as a sorted list (for UI rendering)."""
        return sorted(self.ALLOWED_STATUS)


def view_logs_request_handler(request, allowed_tables) -> ViewLogsRequestHandler:

    table_name = request.args.get("table_name", "")
    if table_name not in allowed_tables:
        table_name = "logs"

    return ViewLogsRequestHandler(
        page=request.args.get("page", 1, type=int),
        per_page=request.args.get("per_page", 10, type=int),
        order=request.args.get("order", "DESC").upper(),
        order_by=request.args.get("order_by", "response_count"),
        day=request.args.get("day", ""),
        status=request.args.get("status", ""),
        like=request.args.get("like", ""),
        table_name=table_name,
    )
