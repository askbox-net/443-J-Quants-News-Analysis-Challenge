# -*- coding: utf-8 -*-


import io
import pandas as pd
import numpy as np

def get_target_ticker(df, N=5, NW=6):
    codes = df['Local Code'].unique()

    rows = []
    ymds = []
    prices = []
    cols = [ 'w_%d' % n for n in range(NW) ]
    for code in codes:
        d = df[df['Local Code'] == code][-NW:].copy()
        ymds.append(d.index.max() + pd.Timedelta('1D'))
        #print('d.index.max:', d.index.max())
        d = d.T
        rows.append(d.loc['pct_change',:].values)

    odf = pd.DataFrame(rows, columns=cols)
    odf['date'] = pd.Series(ymds)

    odf['code'] = pd.Series(codes)
    #odf.to_csv('odf.csv', index=False)
    #print(ymds)

    target_df = odf[np.sum(odf.iloc[:,range(NW)] > 0, axis=1) == NW].drop('code', axis=1).copy()

    target_df = target_df.sum(axis=1).sort_values(ascending=False)
    obj = odf.iloc[target_df[:N].index].reset_index().copy()
    man = 10000
    #obj.loc[:, ['budget']] = pd.Series([30 * man, 25 * man, 20 * man, 15 * man, 10 * man])
    obj['budget'] = pd.Series([30 * man, 25 * man, 20 * man, 15 * man, 10 * man])
    obj.rename(columns={'code': 'Local Code'}, inplace=True)

    return obj[['date', 'Local Code', 'budget']]

class ScoringService(object):
    @classmethod
    def get_model(cls, model_path="../model"):
        return True

    @classmethod
    def predict(
        cls, inputs, start_dt=pd.Timestamp("2020-01-01"), strategy_id="reversal"):
        ####
        # データセットを読み込みます
        ####
        # 銘柄情報読み込み
        df_stock_list = pd.read_csv(inputs["stock_list"]) # 問題2のユニバース (投資対象銘柄群) 取得
        codes = df_stock_list.loc[
                    df_stock_list.loc[:, "universe_comp2"] == True, "Local Code"
                ].unique()

        # 価格情報読み込み、インデックス作成
        df_price = pd.read_csv(inputs["stock_price"]).set_index("EndOfDayQuote Date") # 日付型に変換
        df_price.index = pd.to_datetime(df_price.index, format="%Y-%m-%d")
        # 特徴量の生成に必要な日数をバッファとして設定 
        n = 30
        # データ絞り込み日付設定
        data_start_dt = start_dt - pd.offsets.BDay(n) # 日付で絞り込み
        filter_date = df_price.index >= data_start_dt
        # 銘柄をユニバースで絞り込み
        filter_universe = df_price.loc[:, "Local Code"].isin(codes) # 絞り込み実施
        df_price = df_price.loc[filter_date & filter_universe]

        ####
        # シンプルな特徴量を作成します
        ####
        # groupby を使用して処理するために並び替え
        df_price.sort_values(["Local Code", "EndOfDayQuote Date"], inplace=True) # 銘柄毎にグループにします。
        grouped_price = df_price.groupby("Local Code")[
                    "EndOfDayQuote ExchangeOfficialClose"
        ]
        # 銘柄毎に20営業日の変化率を作成してから、金曜日に必ずデータが存在するようにリサンプルしてフィル します
        df_feature = grouped_price.apply(
                    #lambda x: x.pct_change(20).resample("B").ffill().dropna()
                    lambda x: x.pct_change().resample("W").ffill().dropna()
                ).to_frame()

        # 上記が比較的時間のかかる処理なので、処理済みデータを残しておきます。 
        df_work = df_feature 
        # copyはランタイム実行時には不要なので削除しています
        # インデックスが銘柄コードと日付になっているため、日付のみに変更します。 
        df_work = df_work.reset_index(level=[0])
        # カラム名を変更します
        df_work.rename(
            columns={"EndOfDayQuote ExchangeOfficialClose": "pct_change"},
            inplace=True,
         )
        # データをstart_dt以降の日付に絞り込みます 
        df_work = df_work.loc[df_work.index >= start_dt]
        ####
        # ポートフォリオを組成します
        ####
        ## 金曜日のデータのみに絞り込みます
        #df_work = df_work.loc[df_work.index.dayofweek == 4]
        #df_work.to_csv('df_work_friday2.csv')
        obj = get_target_ticker(df_work)
        #print(obj)
        #return obj
        out = io.StringIO()
        obj.to_csv(out, index=False, header=True) # 出力を保存
        return out.getvalue()
        """
        # 日付毎に処理するためグループ化します
        grouped_work = df_work.groupby("EndOfDayQuote Date", as_index=False)
        # 選択する銘柄数を指定します 
        number_of_portfolio_stocks = 25
        # ポートフォリオの組成方法を戦略に応じて調整します 
        strategies = {
        # リターン・リバーサル戦略 
            "reversal": {"asc": True}, 
        # トレンドフォロー戦略 
            "trend": {"asc": False},
        }
        # 戦略に応じたポートフォリオを保存します 
        df_portfolios = {}
        # strategy_id が設定されていない場合は全ての戦略のポートフォリオを作成します 
        if "strategy_id" not in locals():
            strategy_id = None
        for i in [strategy_id] if strategy_id is not None else strategies.keys(): 
            # 日付毎に戦略に応じた上位25銘柄を選択します。
            df_portfolios[i] = grouped_work.apply(
                    lambda x: x.sort_values(
                        "pct_change", ascending=strategies[i]["asc"]
                    ).head(number_of_portfolio_stocks)
                )
        # budgetを指定
        order_qty = 100000
        # 戦略毎に処理
        for i in df_portfolios.keys():
            # 購入株式数を設定
            df_portfolios[i].loc[:, "budget"] = order_qty
            # インデックスを日付のみにします 
            df_portfolios[i].reset_index(level=[0], inplace=True)
            # 金曜日から月曜日日付に変更
            df_portfolios[i].index = df_portfolios[i].index + pd.Timedelta("3D")
        ####
        # 出力を調整します
        ####
        # 戦略毎に処理
        for i in df_portfolios.keys():
            # インデックス名を設定
            df_portfolios[i].index.name = "date"
            # 出力するカラムを絞り込みます
            df_portfolios[i] = df_portfolios[i].loc[:, ["Local Code", "budget"]]

         # 出力保存用
        outputs = {}
        # 戦略毎に処理
        for i in df_portfolios.keys():
            # 出力します
            out = io.StringIO()
            # CSV形式で出力 
            df_portfolios[i].to_csv(out, header=True) # 出力を保存
            outputs[i] = out.getvalue()
        return outputs[strategy_id]
        """
