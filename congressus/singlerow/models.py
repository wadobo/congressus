import os
from django.db import models
from django.db.models.signals import post_save
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from gtts import gTTS

from events.models import Event
from windows.models import TicketWindow


class SingleRowTail(models.Model):
    event = models.ForeignKey(Event, related_name='single_row_tail', verbose_name=_('event'), on_delete=models.CASCADE)
    window = models.ForeignKey(TicketWindow, related_name='single_row_tail', verbose_name=_('window'), on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']


def generate_voice(sender, instance, **kwargs):
    window_ticket_name = instance.window.name
    path = settings.MEDIA_ROOT + "/voice/" + window_ticket_name + ".mp3"
    if not os.path.exists(path):
        tts = gTTS(text=window_ticket_name, lang=settings.SINGLEROW_LANG)
        tts.save(path)

post_save.connect(generate_voice, sender=SingleRowTail)
