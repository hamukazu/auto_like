#!/usr/bin/env python

import tweepy
import boto3
import botocore
import toml
import time
import uuid
import random


class idstore:
    def __init__(
        self,
        aws_access_key_id,
        aws_secret_access_key,
        aws_s3_bucket,
        aws_s3_key,
        emulated=False,
    ):
        self._bucket = aws_s3_bucket
        self._key = aws_s3_key
        self._emurated = emulated
        if emulated:
            self._file = "idstore_emu.txt"
            self._s3_client = None
        else:
            sess = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )
            self._s3_client = sess.client("s3")
            self._file = None

    def get(self):
        if self._emurated:
            try:
                with open(self._file) as fp:
                    r = fp.readline().rstrip()
                return int(r)
            except:
                return None
        else:
            try:
                r = self._s3_client.get_object(Bucket=self._bucket, Key=self._key)
                body = r["Body"].read()
                return int(body.decode("utf-8"))
            except:
                return None

    def set(self, s):
        if self._emurated:
            with open(self._file, "w") as fp:
                print(s, file=fp)
        else:
            self._s3_client.put_object(
                Bucket=self._bucket, Key=self._key, Body=str(s).encode("utf-8")
            )


def botmain(configfile="config.toml"):
    config = toml.load(configfile)
    t = config["twitter"]

    client = tweepy.Client(
        bearer_token=t["bearer_token"],
        consumer_key=t["consumer_key"],
        consumer_secret=t["consumer_secret"],
        access_token=t["access_token"],
        access_token_secret=t["access_token_secret"],
    )
    aws = config["aws"]
    store = idstore(
        aws_access_key_id=aws["access_key_id"],
        aws_secret_access_key=aws["secret_access_key"],
        aws_s3_bucket=aws["s3_bucket"],
        aws_s3_key=aws["s3_key"],
    )
    since_id = store.get()
    tweets = client.get_users_tweets(
        id=t["target"], tweet_fields=["id"], since_id=since_id, exclude=["retweets"]
    )
    if tweets.data:
        for t in tweets.data:
            text = uuid.uuid4().hex
            if random.random() < 0.4:
                client.create_tweet(text=text, quote_tweet_id=t.id)
            client.like(t.id)

        store.set(tweets.meta["newest_id"])


if __name__ == "__main__":
    botmain()
