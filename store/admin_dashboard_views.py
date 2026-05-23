from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from store.models import Order, Product, OrderLifecycleLog
from django.db.models import Sum
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

@staff_member_required
def admin_dashboard(request):
    order_count = Order.objects.count()
    total_sales = Order.objects.aggregate(total=Sum('total'))['total'] or 0
    product_count = Product.objects.count()
    recent_orders = Order.objects.order_by('-created_at')[:5]
    all_orders = Order.objects.order_by('-created_at')
    return render(request, 'admin_dashboard.html', {
        'order_count': order_count,
        'total_sales': total_sales,
        'product_count': product_count,
        'recent_orders': recent_orders,
        'all_orders': all_orders,
    })

# Map: status value → timestamp field to auto-fill
_STATUS_TS_MAP = {
    'packed':           'packed_at',
    'shipped':          'shipped_at',
    'out_for_delivery': 'out_for_delivery_at',
    'delivered':        'delivered_at',
}

@staff_member_required
@csrf_exempt
def admin_update_order_status(request, order_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    try:
        data = json.loads(request.body)
        new_status = data.get('status')

        # All valid statuses (must match Order.STATUS_CHOICES)
        valid_statuses = [s[0] for s in Order.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'error': f'Invalid status: {new_status}'})

        order = get_object_or_404(Order, id=order_id)
        old_status = order.status
        order.status = new_status

        # Auto-stamp the matching timestamp the FIRST time this status is set
        update_fields = ['status', 'updated_at']
        if new_status in _STATUS_TS_MAP:
            ts_field = _STATUS_TS_MAP[new_status]
            if not getattr(order, ts_field):   # only set once
                setattr(order, ts_field, timezone.now())
                update_fields.append(ts_field)

        order.save(update_fields=update_fields)

        OrderLifecycleLog.objects.create(
            order=order,
            event_type='status_change',
            previous_status=old_status,
            new_status=new_status,
            note=f'Status changed from {old_status} to {new_status}',
            created_by=request.user if request.user.is_authenticated else None,
        )

        return JsonResponse({
            'success': True,
            'message': f'Order #{order_id} status updated to {new_status}',
            'new_status': new_status,
            'order_id': order_id,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
