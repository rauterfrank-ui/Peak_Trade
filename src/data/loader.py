"""
Data Loader: CSV-Loader für verschiedene Datenquellen.

Wave A (Stability): Data Contract Validation at CSV Load Boundaries
"""
import os
import logging
import pandas as pd

from .contracts import validate_ohlcv
from ..core.errors import DataContractError

logger = logging.getLogger(__name__)


class CsvLoader:
    """
    Generischer CSV-Loader.

    Liest CSV-Dateien und gibt rohe DataFrames zurück.
    Keine Annahmen über Spaltenformat – das macht der Normalizer.
    """

    def __init__(
        self,
        delimiter: str = ",",
        decimal: str = ".",
        parse_dates: bool = True,
        validate_contract: bool = False,
    ) -> None:
        """
        Args:
            delimiter: CSV-Trennzeichen (default: ",")
            decimal: Dezimalzeichen (default: ".")
            parse_dates: Automatisches Datum-Parsing (default: True)
            validate_contract: Data contract validation durchführen (default: False for backward compatibility)
            
        Note:
            For production use with OHLCV data, it's recommended to enable validation:
            loader = CsvLoader(validate_contract=True)
        """
        self.delimiter = delimiter
        self.decimal = decimal
        self.parse_dates = parse_dates
        self.validate_contract = validate_contract

    def load(self, filepath: str) -> pd.DataFrame:
        """
        Lädt eine CSV-Datei.

        Args:
            filepath: Pfad zur CSV-Datei

        Returns:
            Roher DataFrame (noch nicht normalisiert)

        Raises:
            FileNotFoundError: Wenn Datei nicht existiert
            ValueError: Wenn CSV nicht lesbar ist
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"CSV-Datei nicht gefunden: {filepath}")

        try:
            if self.parse_dates:
                df = pd.read_csv(
                    filepath,
                    delimiter=self.delimiter,
                    decimal=self.decimal,
                    index_col=0,
                    parse_dates=True,
                )
            else:
                df = pd.read_csv(
                    filepath,
                    delimiter=self.delimiter,
                    decimal=self.decimal,
                )
            return df
        except Exception as exc:  # pragma: no cover
            raise ValueError(f"Fehler beim Laden der CSV-Datei: {exc}") from exc


class KrakenCsvLoader(CsvLoader):
    """
    Spezialisierter Loader für Kraken OHLC CSV-Exporte.

    Kraken-Format (typisch):
    - Spalten: time, open, high, low, close, vwap, volume, count
    - time: Unix-Timestamp (Sekunden)
    """

    def __init__(self, validate_contract: bool = False) -> None:
        """
        Initialisiert mit Kraken-spezifischen Settings.
        
        Args:
            validate_contract: Data contract validation durchführen (default: False for backward compatibility)
            
        Note:
            For production use, it's recommended to enable validation:
            loader = KrakenCsvLoader(validate_contract=True)
        """
        super().__init__(delimiter=",", decimal=".", parse_dates=False, validate_contract=validate_contract)

    def load(self, filepath: str) -> pd.DataFrame:
        """
        Lädt Kraken CSV.

        Args:
            filepath: Pfad zur Kraken CSV

        Returns:
            DataFrame mit DatetimeIndex (UTC) und Kraken-Spalten

        Raises:
            FileNotFoundError: Wenn Datei nicht existiert
            ValueError: Wenn CSV nicht lesbar ist oder 'time'-Spalte fehlt
            DataContractError: Wenn Validierung fehlschlägt (validate_contract=True)
        """
        df = super().load(filepath)

        if "time" not in df.columns:
            raise ValueError(
                "Kraken CSV muss eine 'time'-Spalte enthalten. "
                f"Gefundene Spalten: {list(df.columns)}"
            )

        df.index = pd.to_datetime(df["time"], unit="s", utc=True)
        df = df.drop(columns=["time"])
        
        # Wave A (Stability): Data Contract Validation after CSV Load
        if self.validate_contract:
            # Only validate if we have OHLCV columns
            from . import REQUIRED_OHLCV_COLUMNS
            if all(col in df.columns for col in REQUIRED_OHLCV_COLUMNS):
                is_valid, errors = validate_ohlcv(df, strict=True, require_tz=True)
                if not is_valid:
                    raise DataContractError(
                        f"OHLCV validation failed after loading CSV: {errors[0]}",
                        hint="Check CSV file for data quality issues",
                        context={
                            "errors": errors,
                            "shape": df.shape,
                            "filepath": filepath,
                        }
                    )
                logger.debug(f"Data contract validation passed for CSV: {filepath}")
        
        return df