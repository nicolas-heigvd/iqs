import re
from pathlib import Path

import chardet
import fiona
import geopandas as gpd
from pyproj import CRS
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
        print(f"Data {directory=}")
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

        def extract_epsg_from_crs(crs_input):
            """
            Given a Fiona CRS input (dict, WKT string, pyproj CRS, etc.),
            return the EPSG code as int if found, else None.
            """
            if crs_input is None:
                return None

            try:
                # Parse input into a pyproj CRS object
                py_crs = CRS.from_user_input(crs_input)
                epsg = py_crs.to_epsg()
                return epsg  # will be int or None
            except Exception:
                return None


        def load_metadata_with_fiona(filepath, layer=None):
            # Open a file for reading. We'll call this the source.
            with fiona.open(filepath, layer=layer) as src:
                return {
                    "layer_name": src.name,
                    "driver": src.driver,
                    "crs": extract_epsg_from_crs(src.crs),
                    "attributes": src.schema["properties"],
                    "geometry_type": src.schema["geometry"],
                }


        def guess_encoding(filepath, sample_bytes=100000):
            """Detect the encoding of a file using chardet on the first `sample_bytes` bytes."""
            try:
                with open(filepath, "rb") as f:
                    raw = f.read(sample_bytes)
                detected = chardet.detect(raw)
                encoding = detected['encoding']
                confidence = detected['confidence']
                print(f"Chardet guess: {encoding} (confidence: {confidence:.2f})")
                return encoding, confidence
            except Exception as err:
                print(f"Error detecting encoding of {filepath.name} with chardet: {err}")
                return None, 0.0


        def get_layer(filepath):
            layers = fiona.listlayers(filepath)
            for layer in layers:
                with fiona.open(filepath, layer=layer) as src:
                    if src.schema["geometry"] != "None":
                        return layer # returns the first valid layer, assuming there is only one
            return None


        def load_data(filepath):
            # Open a file for reading. We'll call this the source.
            common_encodings = ['utf-8', 'cp1252', 'ISO-8859-1']
            layer = get_layer(filepath)
            for encoding in common_encodings:
                print(f"Testing {encoding=} to open file: {filepath.name}...")
                try:
                    gdf = gpd.read_file(
                        filepath,
                        layer=layer,
                        encoding=encoding,
                    )
                    print(f"Successfully loaded {filepath.name} with encoding: {encoding}")
                    return gdf
                except UnicodeDecodeError as err:
                      print(f"UnicodeDecodeError: failed loading {filepath.name} with encoding {encoding}: error={err}")

            if filepath.suffix[1:] == 'shp':
                dbf_filepath = filepath.with_suffix(".dbf")
                if not dbf_filepath.is_file():
                    print(f"{dbf_filepath} does not exist!")
                    pass

                encoding, confidence = guess_encoding(dbf_filepath)
                if encoding and confidence > 0.8:
                    try:
                        gdf = gpd.read_file(
                            filepath,
                            layer=layer,
                            encoding=encoding,
                        )
                        print(f"Successfully loaded {filepath.name} with guessed encoding: {encoding}")
                        return gdf
                    except UnicodeDecodeError as err:
                        print(f"UnicodeDecodeError: failed loading {filepath.name} with guessed encoding {encoding}: error={err}")

            raise UnicodeDecodeError(f"Failed to decode {filepath.name} with all tried encodings, including guessed one.")


        def make_columns_unique(gdf):
            new_cols = []
            counts = {}

            for i, col in enumerate(gdf.columns):
                if not gdf.columns.duplicated()[i]:
                    counts[col] = 1
                    new_cols.append(col)
                else: # we've got a duplicate column name
                    counts[col] += 1
                    new_cols.append(f"{col.rstrip('_')}_{counts[col]-1}")

            new_gdf = gdf.copy()
            new_gdf.columns = new_cols

            return new_gdf


        def get_unique_values(gdf):
            # do not take the geometry column into consideration
            gdf = make_columns_unique(gdf)
            print("Extracting unique values for each attribute, please wait...")
            return dict([(column, gdf[column].unique()) for column in gdf.columns if column != 'geometry'])


        def extract_unique_value(filepath):
            gdf = load_data(filepath)
            return get_unique_values(gdf)


        for filepath in filepaths:
            layer_name, driver, crs, attributes, geometry_type = (
                load_metadata_with_fiona(filepath).values()
            )
            print(
                f"{80*'#'}\nScanning file \"{filepath}\":\n"
                f"{80*'#'}\n{driver=}\n{crs=}\n{attributes=}\n{geometry_type=}"
            )
            geometry, _ = GeometryType.objects.get_or_create(
                name=geometry_type,
            )
            geolayer, _ = GeoLayer.objects.get_or_create(
                name=layer_name,
                epsg_code=crs,
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
