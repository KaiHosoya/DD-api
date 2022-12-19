import tweepy
import pandas as pd
import numpy as np
import os
import statistics
from datetime import datetime
import time
from copy import copy
import csv

consumer_key = "RJNuO2FWM3vRxsuwIn7mTIcbt"
consumer_secret = "wt969qBSzA3kyB6Vseu9EeKbuFiAaMuy1tGL3qAelfiRpDz6ki"

bearer_token = "AAAAAAAAAAAAAAAAAAAAAKoXjAEAAAAA3gxtgb6mNWRCLD%2Bj7YzUEUC91Os%3DqUGPoufhYYGCPDEDnPfqZ90OyL2J5hhG6ZB3j7sbI8semswwLy"

access_token = "1584040621928755200-7k0khOASe4IfBvgcmS2kYkgQCyXosZ"
access_token_secret = "JF8tdykheDDYt4Vw5oKiLZ110Jz8BciYt82KO9chRxpWp"

client = tweepy.Client(bearer_token, consumer_key,
                       consumer_secret, access_token, access_token_secret)

num_of_followers = 6  # 何人とってくるか
day_period = 90  # 何日前までカウントするか
num_of_tweets = 100
# follower_df = get_df(user_id, num_of_followers, day_period, num_of_tweets)


class DD:
    """_summary_
       Tweepyで拾ってきた情報を入れて処理するクラス
    """

    def __init__(self, df):
        """
        Args:
            df (Pandas.DataFrame): Dataframe
        """
        self.df = df

    def transform(self):
        """_summary_
        datetimeからUNIX timestampに変えてdataframeの最後に最終更新時間の列をたす。
        """
        df_copy = copy(self.df)
        time_df = copy(
            df_copy.loc[:, ["最後にいいねした時間", "最後にretweetした時間", "最後にtweetした時間"]])
        time_df = time_df.applymap(lambda x: int(
            x.timestamp()))  # datetimeからtimestanpに変換
        self.now = int(time.time())
        jikansa = self.now - time_df
        latest = jikansa.min(axis=1)

        df_copy[["最後にいいねした時間", "最後にretweetした時間", "最後にtweetした時間"]] = time_df
        df_copy["最新のアクションした時間"] = self.now - latest

        return df_copy

    def dead(self, days=90):
        """_summary_
        最終更新が何日前のアカウントを表示

        Args:
            days (int, optional): 最終更新の閾値 Defaults to 30.
        """
        df = self.transform()
        # 30日以内に活動していないアカウントを抽出
        self.dead_ids = df.query(
            "最新のアクションした時間 < @self.now - 60*60*24 * @days")["Username"]

    def get_df(user_id, num_of_accounts, num_of_tweets, day_period=90, follower=True):
        """_summary_
        いいね、ツイート、リツイートの時間、回数をDataFrameで返す

        Args:
            user_id (str):　対象のユーザーネーム(@の後ろ)
            num_of_accounts (int): フォロワー、フォロイーの最大取得数
            num_of_tweets (int): いいねやタイムラインの最大取得数
            day_period (int): 何日前までの物をカウントするか
            follower (bool,optional) : Trueの時はフォロワー、Falseの時はフォロイーを取得。default;True

        Returns:
            df (DataFrame): 列名['Username', '最後にいいねした時間', 'いいねの回数', '最後にretweetした時間', 'retweetの回数', '最後にtweetした時間', 'tweetの回数']のデータフレーム
            各列の型は[str, datetime, int, datetime, int, datetime, int]
        """
    # フォロワー、フォロイー取得(tweepyobject)
        if follower == True:
            accounts_list = client.get_users_followers(
                user_id, max_results=num_of_followers).data

        else:
            accounts_list = client.get_users_following(
                user_id, max_results=num_of_accounts).data
        print(len(accounts_list))
        # print("account_list is" + accounts_list)

        # 空のDataFrame作成
        df = pd.DataFrame(columns=['Username', '最後にいいねした時間', 'いいねの回数', 'いいね間隔の標準偏差', '最後にretweetした時間',
                          'retweetの回数', 'retweet間隔の標準偏差', '最後にtweetした時間', 'tweetの回数', 'tweet間隔の標準偏差'])

        # アカウントごとに情報を引っ張ってきてdfにappend
        for user in accounts_list:
            id = user.id

            # いいね
            likes = client.get_liked_tweets(id, max_results=num_of_tweets, tweet_fields=[
                                            "created_at"])  # likeのtweetオブジェクトを取得

            if likes.data is None:
                like_count = 0
                last_like_time = datetime.fromisoformat(
                    "1970-01-01 00:00:00+00:00")

            else:
                second_period = 60*60*24*day_period  # timestanp化
                like_count = 0
                last_like_time = datetime.fromisoformat(
                    "1970-01-01 00:00:00+00:00")
                like_list = []
                # カウント
                for i in range(len(likes.data)):
                    if int(time.time()) - int(likes.data[i].created_at.timestamp()) < second_period:
                        like_count += 1
                        like_list.append(likes.data[i].created_at.timestamp())
                        if likes.data[i].created_at > last_like_time:
                            last_like_time = likes.data[i].created_at
                    else:
                        break
                like_list.sort()
                if len(np.array(like_list[1:]) - np.array(like_list[:-1])) == 0:
                    like_std = np.NaN
                else:
                    like_std = np.var(
                        np.array(like_list[1:]) - np.array(like_list[:-1]))
            # ツイート、リツイート、 返信
            timeline = client.get_users_tweets(
                id, max_results=num_of_tweets, tweet_fields=["created_at"])
            if timeline.data is None:
                tweet_count = 0
                last_tweet_time = datetime.fromisoformat(
                    "1970-01-01 00:00:00+00:00")

            else:
                second_period = 60*60*24*day_period  # timestanp化
                tweet_count = 0
                retweet_count = 0
                last_tweet_time = datetime.fromisoformat(
                    "1970-01-01 00:00:00+00:00")
                last_retweet_time = datetime.fromisoformat(
                    "1970-01-01 00:00:00+00:00")
                tweet_list = []
                retweet_list = []

                for i in range(len(timeline.data)):
                    # datetimeからtimestanpに変換
                    create_time = int(timeline.data[i].created_at.timestamp())
                    if int(time.time()) - create_time < second_period:
                        if timeline.data[i].text[:2] == "RT":
                            retweet_count += 1
                            retweet_list.append(
                                timeline.data[i].created_at.timestamp())
                            if timeline.data[i].created_at > last_retweet_time:
                                last_retweet_time = timeline.data[i].created_at
                        else:
                            tweet_count += 1
                            tweet_list.append(
                                timeline.data[i].created_at.timestamp())
                            if timeline.data[i].created_at > last_tweet_time:
                                last_tweet_time = timeline.data[i].created_at
                    else:
                        break
                tweet_list.sort()
                if len(np.array(tweet_list[1:]) - np.array(tweet_list[:-1])) == 0:
                    tweet_std = np.NaN
                else:
                    tweet_std = np.var(
                        np.array(tweet_list[1:]) - np.array(tweet_list[:-1]))

                retweet_list.sort()
                if len(np.array(retweet_list[1:]) - np.array(retweet_list[:-1])) == 0:
                    retweet_std = np.NaN
                else:
                    retweet_std = np.var(
                        np.array(retweet_list[1:]) - np.array(retweet_list[:-1]))

                data = [[user.username, last_like_time, like_count, like_std, last_retweet_time,
                         retweet_count, retweet_std, last_tweet_time, tweet_count, tweet_std]]
                append_df = pd.DataFrame(data, columns=['Username', '最後にいいねした時間', 'いいねの回数', 'いいね間隔の標準偏差',
                                         '最後にretweetした時間', 'retweetの回数', 'retweet間隔の標準偏差', '最後にtweetした時間', 'tweetの回数', 'tweet間隔の標準偏差'])
                df = pd.concat([df, append_df], axis=0)
        # with open('twitter.csv', 'w') as f:
        #     column = ['Username', '最後にいいねした時間', 'いいねの回数', 'いいね間隔の標準偏差', '最後にretweetした時間',
        #               'retweetの回数', 'retweet間隔の標準偏差', '最後にtweetした時間', 'tweetの回数', 'tweet間隔の標準偏差']
        #     writer = csv.writer(f)
        #     writer.writerow(column)
        #     writer.writerows(df)

        #     f.close()
        df.to_csv('basic_info.csv')
        print(df)
        return df

    # 対象のアカウント
    def get_user_id(name):
        id = client.get_user(username=name).data.id
        return id

    def judge(user_id):
        follower_df = DD.get_df(user_id, num_of_tweets, day_period)
        follower_model = DD(follower_df)
        follower_model.dead()
        print(f'取得したアカウント数{len(follower_df["Username"])}')
        if not len(follower_df["Username"]) == 0:
            print(f"死にアカウント数:{len(follower_model.dead_ids)}")
            print(
                f'死にアカウント割合:{int(len(follower_model.dead_ids)/len(follower_df["Username"])*100)}%')
