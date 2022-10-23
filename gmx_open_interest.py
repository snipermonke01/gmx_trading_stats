#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: snipermonke01
"""


import requests
import time
import os
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
from PIL import Image

from matplotlib.ticker import FormatStrFormatter

from datetime import datetime

from utils import make_query, TelegramManager
from asset_open_interest import AssetOpenInterest
from gmx_fees import GMXFees


class GMXOpenInterest(TelegramManager):

    def __init__(self):

        super().__init__()

        self.subgraph_query = """{
              tradingStat(id: "total") {
                id
                longOpenInterest
                shortOpenInterest
                timestamp
              }
            }
            """

    def run_app(self):

        # Try to find oi.csv to get previous open interest data, if not will set previous as 0
        try:
            oi_csv = pd.read_csv('oi.csv').set_index('timestamp')

            previous_long_oi = oi_csv['long_oi'].iloc[-1]
            previous_short_oi = oi_csv['short_oi'].iloc[-1]
            previous_arb_long_oi = oi_csv['arb_long_oi'].iloc[-1]
            previous_arb_short_oi = oi_csv['arb_short_oi'].iloc[-1]
            previous_avax_long_oi = oi_csv['avax_long_oi'].iloc[-1]
            previous_avax_short_oi = oi_csv['avax_short_oi'].iloc[-1]
        except FileNotFoundError:

            previous_long_oi = 0
            previous_short_oi = 0
            previous_arb_long_oi = 0
            previous_arb_short_oi = 0
            previous_avax_long_oi = 0
            previous_avax_short_oi = 0

        dt_now = datetime.now()
        arb_short_oi, arb_long_oi = self._get_open_interest(
            is_arbritrum=True)
        avax_short_oi, avax_long_oi = self._get_open_interest(is_avax=True)

        short_oi = arb_short_oi + avax_short_oi
        long_oi = arb_long_oi + avax_long_oi

        try:
            long_oi_change = (
                (long_oi - previous_long_oi)/previous_long_oi)*100
            short_oi_change = (
                (short_oi - previous_short_oi)/previous_short_oi)*100
        except ZeroDivisionError:
            long_oi_change = 0
            short_oi_change = 0

        if short_oi_change > 0:
            short_oi_change = "{:+.2f}% \U0001F4C8".format(
                short_oi_change)
        elif short_oi_change == 0:
            short_oi_change = 'No Change'
        else:
            short_oi_change = "{:.2f}% \U0001F4C9".format(
                short_oi_change)

        if long_oi_change > 0:
            long_oi_change = "{:+.2f}% \U0001F4C8".format(
                long_oi_change)
        elif long_oi_change == 0:
            long_oi_change = 'No Change'
        else:
            long_oi_change = "{:.2f}% \U0001F4C9".format(long_oi_change)

        long_arb_oi_change = arb_long_oi - previous_arb_long_oi
        if long_arb_oi_change > 0:
            long_arb_oi_change = "+${:.2f}m \U0001F4C8".format(
                long_arb_oi_change)
        elif long_arb_oi_change == 0:
            long_arb_oi_change = 'No Change'
        else:
            long_arb_oi_change = "-${:.2f}m \U0001F4C9".format(
                long_arb_oi_change*-1)

        short_arb_oi_change = arb_short_oi - previous_arb_short_oi
        if short_arb_oi_change > 0:
            short_arb_oi_change = "+${:.2f}m \U0001F4C8".format(
                short_arb_oi_change)
        elif short_arb_oi_change == 0:
            short_arb_oi_change = 'No Change'
        else:
            short_arb_oi_change = "-${:.2f}m \U0001F4C9".format(
                short_arb_oi_change*-1)

        long_avax_oi_change = avax_long_oi - previous_avax_long_oi
        if long_avax_oi_change > 0:
            long_avax_oi_change = "+${:.2f}m \U0001F4C8".format(
                long_avax_oi_change)
        elif long_avax_oi_change == 0:
            long_avax_oi_change = 'No Change'
        else:
            long_avax_oi_change = "-${:.2f}m \U0001F4C9".format(
                long_avax_oi_change*-1)

        short_avax_oi_change = avax_short_oi - previous_avax_short_oi
        if short_avax_oi_change > 0:
            short_avax_oi_change = "+${:.2f}m \U0001F4C8".format(
                short_avax_oi_change)
        elif short_avax_oi_change == 0:
            short_avax_oi_change = 'No Change'
        else:
            short_avax_oi_change = "-${:.2f}m \U0001F4C9".format(
                short_avax_oi_change*-1)

        total_oi = "Total Open Interest: ${:.2f}m".format(short_oi+long_oi)
        long_positions = "Total Long positions: ${:.2f}m ({} vs previous)".format(long_oi,
                                                                                  long_oi_change)
        short_positions = "Total Short positions: ${:.2f}m ({} vs previous)".format(short_oi,
                                                                                    short_oi_change)

        avax_descriptor = self._get_oi_descripter('avax',
                                                  avax_long_oi,
                                                  avax_short_oi)
        arbitrum_descriptor = self._get_oi_descripter('arbitrum',
                                                      arb_long_oi,
                                                      arb_short_oi)

        arb_positions_message = "Arbitrum Longs: ${:.2f}m \n({})\nArbitrum Shorts: ${:.2f}m \n({})\n".format(arb_long_oi,
                                                                                                             long_arb_oi_change,
                                                                                                             arb_short_oi,
                                                                                                             short_arb_oi_change)

        avax_positions_message = "Avax Longs: ${:.2f}m \n({})\nAvax Shorts: ${:.2f}m \n({})".format(avax_long_oi,
                                                                                                    long_avax_oi_change,
                                                                                                    avax_short_oi,
                                                                                                    short_avax_oi_change)

        message = "\U0001FAD0 GMX  Trading Stats \U0001FAD0\n\n{}\n{}\n{}\n\n{}\n{}\n\n{}\n{}".format(total_oi,
                                                                                                      long_positions,
                                                                                                      short_positions,
                                                                                                      arb_positions_message,
                                                                                                      avax_positions_message,
                                                                                                      arbitrum_descriptor,
                                                                                                      avax_descriptor)
        print(message)

        self.telegram_bot_sendtext(message)

        latest_stats_dict = {'timestamp': dt_now,
                             'short_oi': [short_oi],
                             'long_oi': [long_oi],
                             'arb_long_oi': [arb_long_oi],
                             'arb_short_oi': [arb_short_oi],
                             'avax_long_oi': [avax_long_oi],
                             'avax_short_oi': [avax_short_oi]}

        latest_stats_df = pd.DataFrame(latest_stats_dict).set_index('timestamp')

        # Append latest stats to csv file. If it doesnt exist make new one
        try:
            oi_csv = pd.concat([oi_csv, latest_stats_df])
        except UnboundLocalError:
            oi_csv = latest_stats_df

        plotting_data = oi_csv.tail(48)

        # Plot of rolling oi will only start producing after 24 hours
        if len(plotting_data) == 48:
            plotting_data = plotting_data.rename(columns={
                'long_oi': 'Long Positions', 'short_oi': 'Short Positions'})
            self._make_plot(plotting_data)
            files = self._prepare_plot()

            self.telegram_bot_image(files)

        oi_csv.to_csv('oi.csv')

    def _get_open_interest(self,
                           is_arbritrum: bool = False,
                           is_avax: bool = False):
        """
        Get short and long positions for a given chain

        Parameters
        ----------
            is_arbritrum: bool
                Pass True to get arbitrum short and long positions
            is_avax: bool
                Pass True to get avax short and long positions
        """

        # Query subgraph
        result = make_query(self.subgraph_query, is_arbritrum, is_avax)

        # divide number returned as its orders of magnitude too great
        long_oi = (int(result['data']['tradingStat']['longOpenInterest']) /
                   1000000000000000000000000000000000000)

        short_oi = (int(result['data']['tradingStat']['shortOpenInterest']) /
                    1000000000000000000000000000000000000)

        return short_oi, long_oi

    @staticmethod
    def _get_oi_descripter(chain: str, long_oi: float, short_oi: float):
        """
        Given a chain, long & short values make formatted message to send to telegram

        Parameters
        ----------
            chain: str
                arbitrum or avax
            long_oi: float
                Value of long positions
            short_oi: float
                Value of short positions
        """

        oi_difference = abs(long_oi-short_oi)
        total_oi = long_oi + short_oi
        diff_percent_of_oi = (oi_difference/total_oi)*100

        if long_oi > short_oi:
            direction = 'bullish'
            direction_emoji = '\U0001F402'
            oi_diff_description = '${:.2f}m more longs than shorts ({:.2f}% of {} oi)'.format(oi_difference,
                                                                                              diff_percent_of_oi,
                                                                                              chain)
        elif long_oi < short_oi:
            direction = 'bearish'
            direction_emoji = '\U0001F9F8'
            oi_diff_description = '${:.2f}m more shorts than longs ({:.2f}% of {} oi)'.format(oi_difference,
                                                                                              diff_percent_of_oi,
                                                                                              chain)
        print(diff_percent_of_oi)
        if diff_percent_of_oi <= 5:
            direction = 'neutral'
            descripter = ""
            direction_emoji = '\U0001F610'
        elif 5 < diff_percent_of_oi <= 10:
            descripter = 'slightly '
        elif 10 < diff_percent_of_oi <= 25:
            descripter = 'pretty '
        elif 25 < diff_percent_of_oi <= 40:
            descripter = 'very '
        elif diff_percent_of_oi > 40:
            descripter = 'giga '

        description = "{} {} is {}{} {}".format(direction_emoji,
                                                chain.title(),
                                                descripter,
                                                direction,
                                                direction_emoji)
        return "{}\n{}".format(description,
                               oi_diff_description)

    @staticmethod
    def _process_to_dataframe(raw_data):

        data = pd.DataFrame(raw_data)

        data['timestamp'] = pd.to_datetime(
            data['timestamp'], unit='s').dt.strftime(date_format="%H:%S")

        data = data.set_index('timestamp')

        return data

    @staticmethod
    def _make_plot(data):

        plt.style.use('dark_background')

        figure, figure_axes = plt.subplots(figsize=(4, 2), dpi=600)

        data[['Short Positions', 'Long Positions']].plot.bar(ax=figure_axes,
                                                             stacked=True,
                                                             color=['Red', 'Green'])

        figure_axes.set_xticks(ticks=np.arange(0, len(data), 1)[::4])

        data.index = pd.to_datetime(data.index)

        figure_axes.set_xticklabels(data.index.strftime('%H:%M')[::4])
        figure_axes.tick_params(labelrotation=45,
                                labelsize=6)
        figure_axes.set(xlabel=None)
        figure_axes.yaxis.set_major_formatter(FormatStrFormatter('$%3dm'))
        yticks = figure_axes.yaxis.get_major_ticks()

        yticks[0].label1.set_visible(False)
        plt.legend(bbox_to_anchor=(0.5, 1),
                   ncol=2,
                   loc="center",
                   prop={'size': 6})
        figure_axes.set_title("GMX Rolling 24hr Open Interest\n",
                              ha='left',
                              loc='left',
                              fontsize=8)
        plt.savefig('rolling_oi.png',
                    dpi=figure.dpi,
                    bbox_inches='tight')

        plt.close()

    @staticmethod
    def _prepare_plot():
        img = Image.open('rolling_oi.png')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return {"photo": img_bytes}


if __name__ == '__main__':

    GMXFees().run_fees_app()
    GMXOpenInterest().run_app()
    AssetOpenInterest().start_app()
