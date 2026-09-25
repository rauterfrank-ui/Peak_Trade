"""
Data Loader: CSV-Loader für verschiedene Datenquellen.
"""

import os
import pandas as pd


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
    ) -> None:
        """
        Args:
            delimiter: CSV-Trennzeichen (default: ",")
            decimal: Dezimalzeichen (default: ".")
            parse_dates: Automatisches Datum-Parsing (default: True)
        """
        self.delimiter = delimiter
        self.decimal = decimal
        self.parse_dates = parse_dates

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


class UnixSecondsOhlcCsvLoader(CsvLoader):
    """CSV loader for OHLC exports whose ``time`` column is unix seconds."""

    def __init__(self) -> None:
        super().__init__(delimiter=",", decimal=".", parse_dates=False)

    def load(self, filepath: str) -> pd.DataFrame:
        df = super().load(filepath)

        if "time" not in df.columns:
            raise ValueError(
                f"OHLC CSV must contain a 'time' column. Found columns: {list(df.columns)}"
            )

        df.index = pd.to_datetime(df["time"], unit="s", utc=True)
        df = df.drop(columns=["time"])
        return df
