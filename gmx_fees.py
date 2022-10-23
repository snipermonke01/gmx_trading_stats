#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 22 17:32:28 2022

@author: snipermonk01
"""
import pandas as pd

from utils import make_query, TelegramManager
import datetime
import pytz
import time


class GMXFees(TelegramManager):

    def __init__(self):

        super().__init__()

        self.daily_fees_subgraph_query = """{
          feeStats(first: 9
                             orderBy: id
                             orderDirection: desc) {
                            id
                            margin
                            swap
                            mint
                            burn
                            liquidation
                  }
                }
                """

    def run_fees_app(self):

        arbitrum_output, avax_output = self._get_fees_data()

        # Take the most recent entry in the dataframe as todays feees
        fees_today = arbitrum_output.iloc[1].sum() + avax_output.iloc[1].sum()

        # Get total fees from dataframe excluding today and liquidations
        previous_7days_total_fees = arbitrum_output.iloc[2:9, arbitrum_output.columns != 'liquidation'].sum(
        ) + avax_output.iloc[2:9, avax_output.columns != 'liquidation'].sum()

        # Get individual daily fees from dataframe excluding today and liquidations
        daily_total_fees = arbitrum_output.iloc[2:9, arbitrum_output.columns != 'liquidation'].sum(
            axis=1).values + avax_output.iloc[2:9, avax_output.columns != 'liquidation'].sum(axis=1).values

        # Get todays liquidation
        daily_liquidation = arbitrum_output['liquidation'].iloc[1]
        + avax_output['liquidation'].iloc[1]

        # Get liquidations not incl today
        total_liquidation = arbitrum_output['liquidation'].iloc[2:9].sum(
        ) + avax_output['liquidation'].iloc[2:9].sum()

        message = self._build_telegram_message(fees_today,
                                               previous_7days_total_fees,
                                               daily_total_fees,
                                               daily_liquidation,
                                               total_liquidation)
        print(message)
        self.telegram_bot_sendtext(message)

    def _get_fees_data(self):
        """
        Get fees data from arbitrum and avax

        """

        arbitrum_query_return = make_query(self.daily_fees_subgraph_query,
                                           is_arbritrum=True,
                                           is_avax=False)
        arbitrum_output = pd.DataFrame(
            arbitrum_query_return['data']['feeStats']
        ).set_index('id').astype(float)/1000000000000000000000000000000000000

        avax_query_return = make_query(self.daily_fees_subgraph_query,
                                       is_arbritrum=False,
                                       is_avax=True)
        avax_output = pd.DataFrame(avax_query_return['data']['feeStats']).set_index(
            'id').astype(float)/1000000000000000000000000000000000000

        return arbitrum_output, avax_output

    def _build_telegram_message(self,
                                fees_today,
                                last_7days_total_fees,
                                daily_total_fees,
                                daily_liquidation,
                                total_liquidation):

        header = "\U0001FAD0 GMX Fees Stats \U0001FAD0"

        diff_from_previous_7_days_avg = fees_today - daily_total_fees.mean()
        if diff_from_previous_7_days_avg > 0:
            sign = "+"
        elif diff_from_previous_7_days_avg < 0:
            sign = "-"

        daily = "Fees collected today*: ${:.2f}m ".format(fees_today)
        daily_liq = "(incl liquidation: ${:.2f}m)".format(
            fees_today + daily_liquidation)

        difference = "({}${:.2f}m vs 7-day avg)".format(sign,
                                                        abs(diff_from_previous_7_days_avg))

        previous_7_days = "Previous 7 days total fees: ${:.2f}m".format(
            daily_total_fees.sum())
        previous_7_days_liq = "(incl liquidation: ${:.2f}m)".format(
            daily_total_fees.sum() + total_liquidation)

        note_back = "*Today is from 00UTC on the same day"
        server_time_info = "Date: {}".format(
            datetime.datetime.now(pytz.utc).strftime("%d/%m/%Y, %H:%M:%S UTC"))

        output_message = "{}\n\n{}\n{}\n{}\n{}\n{}\n\n\n{}\n{}".format(header,
                                                                       daily,
                                                                       daily_liq,
                                                                       "",
                                                                       previous_7_days,
                                                                       previous_7_days_liq,
                                                                       note_back,
                                                                       server_time_info)

        return output_message


if __name__ == '__main__':
    pass
