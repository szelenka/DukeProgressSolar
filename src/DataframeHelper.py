import datetime
import json
import pandas as pd


def merge_dataframes(df_mhe, df_pvw):
    df = df_mhe.merge(df_pvw, on='month_int', how='outer').sort_values('date').dropna().reset_index(drop=True)
    df['kwh_demand'] = df['avg_kwh_per_day'] / df['radiation_hours_per_day']
    
    return df


def avg_month(df: pd.core.frame.DataFrame, solar_system_kwh: float = 6.32):
    # Duke Progress resets the year on May-31, meaning any unused credits before then are removed from the account
    m = df.groupby('month_int').agg('mean').reindex([6,7,8,9,10,11,12,1,2,3,4,5])
    m['kwh_per_day_delta'] = m['avg_kwh_per_day'] - (m['radiation_hours_per_day'] * solar_system_kwh)
    m['kwh_per_month_delta'] = (m['avg_kwh_per_day'] - (m['radiation_hours_per_day'] * solar_system_kwh)) * m['days']
    
    return m


def annual_costs(df: pd.core.frame.DataFrame):
    def net_meter(series):
        credits = 0.
        expense = 0.
        for idx, s in enumerate(series):
            if s >= 0:
                if credits == 0:
                    expense += s
                else:
                    credits -= s
                    if credits < 0:
                        expense += -1 * credits
                        credits = 0
            else:
                credits += -1 * s

        return expense, credits

    annual_expense, annual_credits = net_meter(df['kwh_per_month_delta'] * df['avg_cost_per_kwh']) 
    annual_savings = df['dollars'].sum() - annual_expense
    return annual_expense, annual_credits, annual_savings