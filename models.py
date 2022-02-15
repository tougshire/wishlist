from django.db import models
from django.conf import settings
from datetime import datetime
from django.apps import apps
from libtekin.models import Item, Location
from django.contrib.auth import get_user_model
from djmoney.models.fields import MoneyField

class ItemRequest(models.Model):
    URGENCY_CHOICES = (
        (1, '1) Safety Hazard or Work Stoppage'),
        (2, '2) Major Work Impediment'),
        (3, '3) Highly Important Issue'),
        (4, '4) Moderately Important Issue'),
        (5, '5) Minor Issue or Suggestion')
    )
    SUBSTITUTABILITY_CHOICES = (
        (1, 'E) Exclusive: Only this item will suffice'),
        (2, 'V) This item or a close variation will suffice'),
        (3, 'M) Many items that serve the intended purpose will suffice'),
    )
    STATUS_CHOICES = (
        (1, '1) Under Consideration'),
        (2, '2) Approved'),
        (3, '3) Received'),
        (5, '5) Canceled or Denied'),
    )
    description = models.CharField(
        'Description',
        max_length=75,
        help_text='A description of the item',
    )
    purpose = models.CharField(
        'Purpose',
        max_length=75,
        blank=True,
        help_text='A description of the purpose for which this item is desired',
    )
    notes = models.TextField(
        'Description',
        blank=True,
        help_text='Additional notes if the short description and purpose are inadequate'
    )
    price = MoneyField(
        'price',
        blank=True,
        null=True,
        help_text='The estimated cost of the item'
    )
    link = models.URLField(
        'link',
        blank=True,
        help_text = 'A link to more information about the item'
    )
    substitutability = models.IntegerField(
        'Substitutability',
        choices=SUBSTITUTABILITY_CHOICES,
        default=2,
        help_text='To what degree a substitute would be suitable'
    )
    urgency = models.IntegerField(
        'Urgency',
        choices=URGENCY_CHOICES,
        default=4,
        help_text='The urgency, on a scale of 1 to 5, where 1 is the most urgent'
    )
    status = models.IntegerField(
        'Status',
        choices=URGENCY_CHOICES,
        default=1,
        help_text='The status of the request'
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='submitted by',
        null=True,
        on_delete=models.PROTECT,
        help_text='The user who submitted this ticket'
    )
    resolution_notes = models.TextField(
        'resolution notes',
        blank=True,
        help_text='How the problem was resolved'
    )

    def __str__(self):
        return self.short_description

    def user_is_editor(self, user):
        return user == self.submitted_by or user.has_perm('wishlist.change_ticket')

    class Meta:
        ordering=['is_resolved', '-when', 'urgency']


class History(models.Model):

    when = models.DateTimeField(
        'when',
        auto_now_add=True,
        help_text='The date this change was made'
    )
    modelname = models.CharField(
        'model',
        max_length=50,
        help_text='The model to which this change applies'
    )
    objectid = models.BigIntegerField(
        'object id',
        null=True,
        blank=True,
        help_text='The id of the record that was changed'
    )
    fieldname = models.CharField(
        'field',
        max_length=50,
        help_text='The that was changed',
    )
    old_value = models.TextField(
        'old value',
        blank=True,
        null=True,
        help_text='The value of the field before the change'
    )
    new_value = models.TextField(
        'new value',
        blank=True,
        help_text='The value of the field after the change'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='libtektiket_history',
        null=True,
        help_text='The user who made this change'
    )

    class Meta:
        ordering = ('-when', 'modelname', 'objectid')

    def __str__(self):

        new_value_trunc = self.new_value[:17:]+'...' if len(self.new_value) > 20 else self.new_value

        try:
            model = apps.get_model('wishlist', self.modelname)
            object = model.objects.get(pk=self.objectid)
            return f'{self.when.strftime("%Y-%m-%d")}: {self.modelname}: [{object}] [{self.fieldname}] changed to "{new_value_trunc}"'

        except Exception as e:
            print (e)

        return f'{"mdy".format(self.when.strftime("%Y-%m-%d"))}: {self.modelname}: {self.objectid} [{self.fieldname}] changed to "{new_value_trunc}"'


