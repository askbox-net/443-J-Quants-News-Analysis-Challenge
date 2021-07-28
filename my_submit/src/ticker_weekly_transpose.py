# -*- codking:utf-8 -*-

import numpy as np
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 1024)


def get_target_ticker(df, N=5, NW=4):
    codes = df['Local Code'].unique()

    rows = []
    cols = [ 'w_%d' % n for n in range(NW) ]
    for code in codes:
        d = df[df['Local Code'] == code][-NW:].T.copy()
        rows.append(d.loc['pct_change',:].values)

    odf = pd.DataFrame(rows, columns=cols)

    odf['code'] = pd.Series(codes)
    odf.to_csv('odf.csv', index=False)

    target_df = odf[np.sum(odf.iloc[:,range(NW)] > 0, axis=1) == NW].drop('code', axis=1).copy()

    target_df = target_df.sum(axis=1).sort_values(ascending=False)
    obj = odf.iloc[target_df[:N].index]

    for code in obj['code'].values:
        print('code:', code)
    print('df:', df.head())
    return obj


def get_target_ticker2(df, N=5, NW=3):
    print(df.head(2))

    #codes = df.groupby('Local Code')['Local Code'].unique()
    codes = df['Local Code'].unique()
    #codes = df[['Local Code']].unique()
    print(codes)

    no = 0
    rows = []
    cols = [ 'w_%d' % n for n in range(NW) ]
    for code in codes:
        d = df[df['Local Code'] == code][-NW:].T
        #print(d.head(6))
        #d = df[df['Local Code'] == code][-4:].T.loc['pct_change',:]
        rows.append(d.loc['pct_change',:].values)

    df = pd.DataFrame(rows, columns=cols)

    df['code'] = pd.Series(codes)
    df.to_csv('df.csv', index=False)
    print('df:')
    print(df.head())

    target_df = df[np.sum(df.iloc[:,range(NW)] > 0, axis=1) == NW].drop('code', axis=1).copy()

    print('target_df:')
    print(target_df.head())
    target_df = target_df.sum(axis=1).sort_values(ascending=False)
    print(target_df.head())
    obj = df.iloc[target_df[:N].index]

    return obj

df = pd.read_csv('./df_work_friday.csv')
o = get_target_ticker(df, 5, 7)
print(o)

