# 🎥 YouTube Playlist Length 📊

Analyze YouTube playlists and videos with ease! Get detailed information about video durations and playlist lengths. It is hosted on [render.com](https://render.com/) and you can check it out [here](https://ytplaylist-len.sharats.dev/).

## 🌟 Features

- 📋 Analyze multiple playlists and individual videos
- ⏱️ Calculate total duration of playlists
- 🚀 Estimate playback times at different speeds (1.25x, 1.50x, 1.75x, 2.00x)
- 🔢 Support for custom playback speeds
- 📅 View average video length in playlists
- 🔍 Analyze specific video ranges within playlists
- 📈 Asynchronous requests and caching layer to speed up processing

## 🚧 Future additions (if I ever get around to it)
- [ ] Add more analytics related to the videos (like average views, likes, etc.)

## 🚀 Getting Started

1. Clone the repository:
   ```
   git clone https://github.com/sharatsachin/ytplaylist-len.git
   cd ytplaylist-len
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your YouTube API key:
   - Create a `.env` file in the project root
   - Add your API key(s):
     ```
     APIS=["YOUR_API_KEY"]
     ```

4. Run the application:
   ```
   fastapi dev .\app.py
   ```

5. Open your browser and navigate to `http://localhost:8000`

## 📝 Usage

1. Enter YouTube playlist or video URLs in the input box
2. (Optional) Specify a range of videos to analyze within playlists
3. (Optional) Enter a custom playback speed
4. Click "Analyze" to get detailed information about the playlists and videos

## 🤝 Contributing

I'm actually not looking for contributions to this repository, and I won't be actively watching it. However, feel free to fork the repository and make your own changes!

## 👏 Technologies Used

- [Python](https://www.python.org/)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Jinja2](https://jinja.palletsprojects.com/)
- [Render](https://render.com/)
- [Halfmoon](https://www.gethalfmoon.com/)

Made with ❤️ by [Sharat Sachin](https://github.com/sharatsachin)