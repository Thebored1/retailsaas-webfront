from django.urls import path
from . import views

urlpatterns = [
    path("sync/products", views.SyncProductsView.as_view(), name="sync_products"),
    path("sync/inventory", views.SyncInventoryView.as_view(), name="sync_inventory"),
    path("sync/batches", views.SyncBatchesView.as_view(), name="sync_batches"),
    path("sync/customers", views.SyncCustomersView.as_view(), name="sync_customers"),
    path("sync/reset", views.SyncResetView.as_view(), name="sync_reset"),
    path("orders/pending", views.PendingOrdersView.as_view(), name="pending_orders"),
    path("orders/list", views.OrdersListView.as_view(), name="orders_list"),
    path("orders/decision", views.OrderDecisionView.as_view(), name="order_decision"),
    path("orders/status", views.OrderStatusUpdateView.as_view(), name="order_status"),
    path("sync/sales", views.SyncSalesView.as_view(), name="sync_sales"),
    path("sync/config", views.SyncConfigView.as_view(), name="sync_config"),
    path("sync/delivery-agents", views.DeliveryAgentCreateView.as_view(), name="sync_delivery_agents"),
    path("sync/delivery-agents/list", views.DeliveryAgentListView.as_view(), name="sync_delivery_agents_list"),
    path("sync/delivery-agents/update", views.DeliveryAgentUpdateView.as_view(), name="sync_delivery_agents_update"),
    path("sync/delivery-agents/delete", views.DeliveryAgentDeleteView.as_view(), name="sync_delivery_agents_delete"),
]
