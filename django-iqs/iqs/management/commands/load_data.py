import re
from pathlib import Path

import fiona
import geopandas as gpd
from django.conf import settings
from django.core.management.base import BaseCommand
from iqs.models import Attribute, AttributeType, GeoLayer, GeometryType, AttributeValue


def fiona_to_postgres_type(fiona_type):
    """
    Convert Fiona attribute type string to PostgreSQL data type string.
    Examples:
      'str' -> 'TEXT'
      'str:20' -> 'VARCHAR(20)'
      'int' -> 'INTEGER'
      'float' -> 'DOUBLE PRECISION'
      'bool' -> 'BOOLEAN'
      'datetime' -> 'TIMESTAMP'
      'date' -> 'DATE'
      'time' -> 'TIME'
      'object' -> 'JSONB'
    """
    # Check if the type includes a length, e.g. 'str:20'
    match = re.match(r"str:(\d+)", fiona_type)
    if match:
        length = int(match.group(1))
        return f"VARCHAR({length})"

    # Map simple types
    mapping = {
        "str": "TEXT",
        "int": "INTEGER",
        "float": "DOUBLE PRECISION",
        "bool": "BOOLEAN",
        "datetime": "TIMESTAMP",
        "date": "DATE",
        "time": "TIME",
        "object": "JSONB",  # for JSON-like or complex objects
        # Add more if needed
    }

    return mapping.get(fiona_type, "TEXT")


# Define your Class commands here
class Command(BaseCommand):
    help = """Import layer and attribute data from a data directory holding
    ESRI Shapefiles and Geopackages"""

    def handle(self, *args, **kwargs):
        """Docstring"""
        directory = settings.DATA_DIR
        print(f"{directory=}")
        extensions_to_fetch = {".shp", ".gpkg"}
        filepaths = list(
            p.resolve()
            for p in Path(directory).glob("**/*")
            if p.suffix in extensions_to_fetch
        )
        # Delete all objects in tables before writing data
        GeoLayer.objects.all().delete()
        Attribute.objects.all().delete()
        AttributeType.objects.all().delete()
        GeometryType.objects.all().delete()

        def load_metadata_with_fiona(filepath):
            # Open a file for reading. We'll call this the source.
            with fiona.open(filepath) as src:
                return {
                    "layer_name": src.name,
                    "driver": src.driver,
                    "crs": src.crs.to_string(),
                    "attributes": src.schema["properties"],
                    "geometry_type": src.schema["geometry"],
                }

        def load_data(filepath):
            # Open a file for reading. We'll call this the source.
            return gpd.read_file(filepath)
        
        def get_unique_values(gdf):
            # do not take the geometry column into consideration
            return dict([(column, gdf[column].unique()) for column in gdf.columns if column != 'geometry'])

        def extract_unique_value(filepath):
            gdf = load_data(filepath)
            return get_unique_values(gdf)

        for filepath in filepaths:
            layer_name, driver, crs, attributes, geometry_type = (
                load_metadata_with_fiona(filepath).values()
            )
            print(
                f"{80*'#'}\nScanning layer \"{filepath}\":\n"
                f"{80*'#'}\n{driver=}\n{crs=}\n{attributes=}\n{geometry_type=}"
            )
            geometry, _ = GeometryType.objects.get_or_create(
                name=geometry_type,
            )
            geolayer, _ = GeoLayer.objects.get_or_create(
                name=layer_name,
                epsg_code=crs.split(":")[1],
                geom=geometry,
            )
            
            data = extract_unique_value(filepath)
            
            # Write attributes and their type
            for attr_name, attr_type in attributes.items():
                attr_type, _ = AttributeType.objects.get_or_create(
                    name=fiona_to_postgres_type(attr_type),
                )
                attribute = Attribute.objects.create(
                    name=str(attr_name),
                    geolayer=geolayer,
                    type=attr_type,
                )
                value_array = data[attr_name]
                for value in value_array:
                    attribute_value = AttributeValue.objects.create(
                        content=str(value),
                        geolayer=geolayer,
                        attribute=attribute,
                    )

        self.stdout.write(self.style.SUCCESS("Data imported successfully."))
