import os
from django.db import models
from django.db.models.signals import post_save
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from gtts import gTTS

from events.models import Event
from windows.models import TicketWindow


class SingleRowConfig(models.Model):
    event = models.ForeignKey(Event, related_name='single_row_config', verbose_name=_('event'), on_delete=models.CASCADE)
    extra_text = models.TextField(blank=True, null=True, verbose_name=_('extra text'))
    say_direction = models.BooleanField(default=True, verbose_name=_('say direction'))

    last_window = models.ForeignKey(TicketWindow, blank=True, null=True,
                                    verbose_name=_('last ticket window'),
                                    related_name="config_last",
                                    on_delete=models.SET_NULL)
    waiting = models.ManyToManyField(TicketWindow, related_name="config_waiting", verbose_name=_('waiting ticket windows'), blank=True)
    logo = models.CharField(_('logo'), max_length=1024, default="")
    video = models.CharField(_('video'), max_length=1024, default="")

    class Meta:
        verbose_name = _("Single Row Config")


class SingleRowTail(models.Model):
    event = models.ForeignKey(Event, related_name='single_row_tail', verbose_name=_('event'), on_delete=models.CASCADE)
    window = models.ForeignKey(TicketWindow, related_name='single_row_tail', verbose_name=_('window'), on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def get_config(self):
        config = SingleRowConfig.objects.filter(event=self.event)
        if config:
            return config.first()

        return None

    def voice_url(self, full_path=False):
        path = "{media}/voice/{name}-{lang}"
        config = self.get_config()
        if config and config.say_direction:
            path += "-{dir}"
        path += ".mp3"

        path = path.format(**{
            "media": settings.MEDIA_ROOT if full_path else settings.MEDIA_URL,
            "name": self.window.name,
            "lang": settings.SINGLEROW_LANG,
            "dir": self.window.singlerow_pos,
        })

        return path

    def text_to_say(self):
        text = self.window.name
        if self.window.number:
            text = _('Ticket window {}').format(self.window.number)
        config = self.get_config()
        if config and config.say_direction:
            text += ", " + self.window.get_singlerow_pos_display()
        return text

    class Meta:
        ordering = ['date']
        verbose_name = _("Single Row Tail")


def generate_voice(sender, instance, **kwargs):
    path = instance.voice_url(full_path=True)
    text = instance.text_to_say()

    if not os.path.exists(path):
        tts = gTTS(text=text, lang=settings.SINGLEROW_LANG)
        tts.save(path)

post_save.connect(generate_voice, sender=SingleRowTail)
