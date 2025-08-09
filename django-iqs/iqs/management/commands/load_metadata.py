import re
from pathlib import Path

from sqlalchemy import create_engine, text, select, Table, MetaData
import pandas as pd
from pyproj import CRS
from django.conf import settings
from django.core.management.base import BaseCommand
from iqs.models import Attribute, AttributeType, GeoLayer, GeometryType, AttributeValue
# %%
# Define your Class commands here
class Command(BaseCommand):
    help = """Import layer and attribute data from a data directory holding
    ESRI Shapefiles and Geopackages"""

    def handle(self, *args, **kwargs):
        """Docstring"""
        directory = settings.DATA_DIR
        print(f"Data {directory=}")
        data_extensions_to_fetch = {".shp", ".gpkg"}
        metadata_extensions_to_fetch = {".db"}
        data_filepaths = list(
            p.resolve()
            for p in Path(directory).glob("**/*")
            if p.suffix in data_extensions_to_fetch
        )
        metadata_filepaths = list(
            p.resolve()
            for p in Path(directory).glob("**/*")
            if p.suffix in metadata_extensions_to_fetch
        )


        def load_data_filepath(filepaths: list) -> pd.DataFrame:
            return pd.DataFrame({
                "filepath": filepaths,
                "filename": [p.name for p in filepaths],
                "filename_without_extension": [p.stem for p in filepaths],  # filename without extension
                "extension": [p.suffix for p in filepaths]
            })


        def compare_filenames(df_files, df_metadata, db_column="nom_bdd", filename_col="filename_without_extension"):
            """Compare two dataframes and tell if a file is present on disk or in the metadata"""
            db_filenames = set(df_metadata[db_column])
            disk_filenames = set(df_files[filename_col])
            # Copy to avoid mutating input DataFrames
            df_files = df_files.copy()
            df_metadata = df_metadata.copy()

            # Add boolean columns
            df_files["in_metadata"] = df_files[filename_col].isin(db_filenames)
            df_metadata["on_disk"] = df_metadata[db_column].isin(disk_filenames)
            
            not_in_db = disk_filenames - db_filenames
            not_on_disk = db_filenames - disk_filenames
            
            return_dataset = False
            if return_dataset:
                return (
                    df_files[df_files[filename_col].isin(not_in_db)],
                    df_metadata[df_metadata[db_column].isin(not_on_disk)]
                )
            else:
                df_files.to_csv(f"{directory}/files.csv", sep=";")
                df_metadata.to_csv(f"{directory}/metadata.csv", sep=";")
                return df_files, df_metadata


        def load_metadata(filepath: Path) -> dict:
            """Load metadata tables into a dict containing DataFrames"""
            engine = create_engine(f"sqlite:////{filepath.as_posix()}", future=True)
            metadata = MetaData()
            metadata.reflect(bind=engine)
            # Reflect all available table names from the DB
            available_tables = metadata.tables.keys()
            print(f"Detected tables: {list(available_tables)}")

            return {
                table: pd.read_sql(
                    f'SELECT * FROM "{table}"',  # quotes for safety
                    con=engine,
                )
                for table in available_tables
            }

        # Connect to the SQLite database
        tables = load_metadata(metadata_filepaths[0])
        df_metadata = tables['metadonnees']
        df_files = load_data_filepath(data_filepaths)
        
        res = compare_filenames(df_files, df_metadata, db_column="nom_bdd", filename_col="filename")

        self.stdout.write(self.style.SUCCESS("Metadata parsed successfully."))

# %%
