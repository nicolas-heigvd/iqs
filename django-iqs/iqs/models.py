import datetime

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Create your models here.


class AttributeType(models.Model):
    """Attribute types"""

    name = models.CharField(
        max_length=1024,
        unique=True,
        null=False,
        verbose_name=_("Attribute type"),
    )

    def __str__(self):
        return self.name


class GeometryType(models.Model):
    """Geometry type of the geolayer"""

    name = models.CharField(
        max_length=1024,
        unique=True,
        null=False,
        verbose_name=_("Geometry type"),
        choices=[
            ("Point", "Point"),
            ("Linestring", "Linestring"),
            ("Polygon", "Polygon"),
            ("PointZ", "PointZ"),
            ("LinestringZ", "LinestringZ"),
            ("PolygonZ", "PolygonZ"),
            ("MultiPoint", "MultiPoint"),
            ("MultiLinestring", "MultiLinestring"),
            ("MultiPolygon", "MultiPolygon"),
            ("MultiPointZ", "MultiPointZ"),
            ("MultiLinestringZ", "MultiLinestringZ"),
            ("MultiPolygonZ", "MultiPolygonZ"),
        ],
    )

    def __str__(self):
        return self.name


class GeoLayer(models.Model):
    """Geographic layers"""

    name = models.CharField(
        max_length=1024,
        unique=True,
        null=False,
    )
    geom = models.ForeignKey(
        GeometryType,
        on_delete=models.CASCADE,
    )
    epsg_code = models.IntegerField(default=4326)

    def __str__(self):
        return self.name


class AttributePriorityLevel(models.Model):
    """Attribute level of priority"""

    name = models.CharField(
        max_length=24,
        unique=True,
        null=True,
        verbose_name=_("Attribute priority level"),
        choices=[
            ("1", "Level N1"),
            ("2", "Level N2"),
            ("3", "Level N3"),
            ("4", "Level N4"),
            (None, "Level not set"),
        ],
    )

    class Meta:
        verbose_name = _("Attribute priority level")
        verbose_name_plural = _("Attribute priority levels")

    def __str__(self):
        return self.name


class Attribute(models.Model):
    """Attributes of the geolayer"""

    name = models.CharField(
        max_length=1024,
        unique=True,
        null=False,
    )
    geolayer = models.ForeignKey(
        GeoLayer,
        on_delete=models.CASCADE,
        related_name="attributes",
    )
    type = models.ForeignKey(
        AttributeType,
        on_delete=models.CASCADE,
    )
    # priority_level = models.ForeignKey(
    #    AttributePriorityLevel,
    #    on_delete=models.CASCADE,
    #    null=True,
    #    blank=True,
    #)

    #class Meta:
    #    unique_together = ("geolayer", "priority_level")

    def __str__(self):
        return self.name


class AttributeValue(models.Model):
    """Attribute values for a given attribute of a geolayer"""

    content = models.CharField(
        max_length=1024,
        unique=False,
        null=False,
    )
    geolayer = models.ForeignKey(
        GeoLayer,
        on_delete=models.CASCADE,
    )
    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
    )
    priority_level = models.ForeignKey(
        AttributePriorityLevel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        unique_together = ("content", "geolayer", "attribute")

    def __str__(self):
        return self.content


class OgcRelationType(models.Model):
    """Attributes of the geolayers"""

    name = models.CharField(
        max_length=1024,
        unique=True,
        null=False,
        verbose_name=_("OGC relation type"),
        choices=[
            ("disjoint", "disjoint"),
            ("intersects", "intersects"),
            ("contains", "contains"),
            ("within", "within"),
            ("touches", "touches"),
            ("equals", "equals"),
        ],
    )

    class Meta:
        verbose_name = _("OGC relation type")
        verbose_name_plural = _("OGC relation types")

    def __str__(self):
        return self.name
