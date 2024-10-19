from datetime import timedelta

import isodate

from src.utils import parse


class Video:

    def __init__(self, video_id, video_data, custom_speed=None):
        self.video_id = video_id

        if video_id:
            self.update_video_details(video_data)
        else:
            self.video_id = video_data["video_id"]
            self.title = video_data["title"]
            self.channel = video_data["channel"]
            self.published = video_data["published"]
            self.duration = isodate.parse_duration(video_data["duration"])
            self.views = video_data["views"]
            self.likes = video_data["likes"]
            self.comments = video_data["comments"]
            self.considered = video_data["considered"]

        self.custom_speed = custom_speed

    def update_video_details(self, video_data: dict):
        self.title = video_data["snippet"]["title"]
        self.channel = video_data["snippet"]["channelTitle"]
        self.published = video_data["snippet"]["publishedAt"]
        self.duration = isodate.parse_duration(
            video_data["contentDetails"].get("duration", "PT0S")
        )
        self.views = video_data["statistics"].get("viewCount", 0)
        self.likes = video_data["statistics"].get("likeCount", 0)
        self.comments = video_data["statistics"].get("commentCount", 0)
        self.considered = True if self.duration.total_seconds() > 0 else False

    def to_dict(self) -> dict:
        return {
            "video_id": self.video_id,
            "title": self.title,
            "channel": self.channel,
            "published": self.published,
            "duration": isodate.duration_isoformat(
                self.duration
            ),  # Convert timedelta to ISO 8601 duration
            "views": self.views,
            "likes": self.likes,
            "comments": self.comments,
            "considered": self.considered,
        }

    def __repr__(self):
        return f"Video(video_id={self.video_id}, title={self.title}, duration={self.duration})"

    def get_output_string(self):
        output_string = [
            "Video : " + self.title,
            "ID : " + self.video_id,
            "Duration : " + parse(self.duration),
            "At 1.25x : " + parse(self.duration / 1.25),
            "At 1.50x : " + parse(self.duration / 1.5),
            "At 1.75x : " + parse(self.duration / 1.75),
            "At 2.00x : " + parse(self.duration / 2),
        ]

        if self.custom_speed:
            output_string.append(
                f"At {self.custom_speed:.2f}x : {parse(self.duration / self.custom_speed)}"
            )
        return output_string
