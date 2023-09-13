def get_sold_invs(session):
    from invs.models import Invitation, InvitationType
    types = InvitationType.objects.filter(sessions__in=[session])
    types = types.filter(is_pass=False)
    return Invitation.objects.filter(type__in=types).count()
