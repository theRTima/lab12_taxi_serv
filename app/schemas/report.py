from pydantic import BaseModel


class RevenueByTariff(BaseModel):
    tariff_id: int
    tariff_name: str
    revenue: float


class TopDriver(BaseModel):
    driver_id: int
    driver_name: str
    order_count: int


class OrdersPerDay(BaseModel):
    date: str
    count: int


class ReportSummary(BaseModel):
    total_orders: int
    revenue_by_tariff: list[RevenueByTariff]
    top_drivers: list[TopDriver]
    orders_per_day: list[OrdersPerDay]
