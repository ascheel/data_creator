#!/usr/bin/python3

import sys
import os
import pandas as pd
import csv

def main():
    """
    ['ZipCode', 'City', 'State', 'County', 'AreaCode', 'CityType',
    'CityAliasAbbreviation', 'CityAliasName', 'Latitude', 'Longitude',
    'TimeZone', 'Elevation', 'CountyFIPS', 'DayLightSaving', 'PreferredLastLineKey',
    'ClassificationCode', 'MultiCounty', 'StateFIPS', 'CityStateKey',
    'CityAliasCode', 'PrimaryRecord', 'CityMixedCase', 'CityAliasMixedCase',
    'StateANSI', 'CountyANSI', 'FacilityCode', 'CityDeliveryIndicator',
    'CarrierRouteRateSortation', 'FinanceNumber', 'UniqueZIPName', 'CountyMixedCase']
    """
    data = pd.read_csv("data/zip-codes-database-STANDARD.csv", dtype=object, keep_default_na=False, na_values=["NaN"])
    data = data.replace({'None':None})

    with open("data/zip_small.csv", "w") as f_out:
        f_out.write("zipcode,city,state,county,citytype,timezone,dst,classificationcode\n")
        writer=csv.writer(f_out, lineterminator="\n")
        for index, row in data.iterrows():
            _tmp = (
                row["ZipCode"],
                row["City"],
                row["State"],
                row["County"],
                row["CityType"],
                row["TimeZone"],
                row["DayLightSaving"],
                row["ClassificationCode"],
            )
            # print(_tmp)
            for cell in _tmp:
                # print(cell)
                if '"' in cell:
                    print('got "')
                if "'" in cell:
                    print("got '")
                if "," in cell:
                    print("got ,")
            writer.writerow(_tmp)
            
        
            

if __name__ == "__main__":
    main()
