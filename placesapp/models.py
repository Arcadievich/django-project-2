from django.db import models


class PlaceCoordinates(models.Model):
    address = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name='Адрес',
    )
    lat = models.DecimalField('Широта', max_digits=9, decimal_places=6, null=True)
    lon = models.DecimalField('Долгота', max_digits=9, decimal_places=6, null=True)
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата создания',
    )

    def __str__(self):
        return f'{self.address[:20]} ({self.lat}, {self.lon})'
    
    class Meta:
        verbose_name = 'Место'
        verbose_name_plural = 'Места'