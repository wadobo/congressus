from tickets.models import MultiPurchase
from .models import TicketWindowSale
from .models import TicketWindow


def online_sale(mp):
    if not isinstance(mp, MultiPurchase):
        return

    online_window = TicketWindow.objects.filter(event=mp.event(), online=True)
    if not online_window:
        return

    w = online_window[0]

    price = mp.get_price()
    payed = mp.get_price()
    sale = TicketWindowSale(purchase=mp, window=w,
                            price=price, payed=payed, payment='card')
    sale.save()
