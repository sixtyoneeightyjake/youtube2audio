# sixtyoneeighty YouTube to MP3 Converter - Streamlit Version

🎵 A modern web-based application to convert YouTube videos and playlists to high-quality MP3 files using Streamlit.

## Features

- **Web-based Interface**: No more PyQt5 dependencies or OpenGL issues
- **YouTube Video & Playlist Support**: Convert individual videos or entire playlists
- **High-Quality MP3 Conversion**: Primary focus on MP3 format with optional MP4/M4A support
- **iTunes Metadata Integration**: Automatically fetch artist, album, and genre information
- **Batch Downloads**: Download multiple files and get them as a ZIP archive
- **Real-time Progress**: Live progress tracking during downloads
- **Cross-platform**: Works on any system with Python and a web browser

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd youtube2audio
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

1. **Start the Streamlit server**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Open your web browser**
   - The application will automatically open at `http://localhost:8501`
   - If it doesn't open automatically, navigate to the URL shown in the terminal

### Using the Application

1. **Enter a YouTube URL**
   - Paste a YouTube video URL (e.g., `https://www.youtube.com/watch?v=dQw4w9WgXcQ`)
   - Or paste a playlist URL (e.g., `https://www.youtube.com/playlist?list=PLrAXtmRdnEQy...`)

2. **Load Videos**
   - Click "Load Videos" to fetch video information
   - The app will display a table with video titles, durations, and metadata

3. **Optional: Fetch iTunes Metadata**
   - Enable "Fetch iTunes Metadata" in the sidebar
   - Click "🎼 Annotate with iTunes Metadata" to get artist, album, and genre info

4. **Configure Download Settings**
   - Choose between MP3 (default) or MP4/M4A format in the sidebar
   - Review the settings and instructions

5. **Download**
   - Click "🎵 Download All" to start the MP3 conversion process
   - Monitor the real-time progress
   - Download individual MP3 files or get all files as a ZIP archive

## Configuration Options

### Sidebar Settings

- **Save as MP4/M4A**: Toggle to save files in MP4/M4A format instead of MP3
- **Fetch iTunes Metadata**: Enable automatic metadata fetching from iTunes

### Advanced Configuration

You can modify the following in `streamlit_app.py`:

- **Download quality**: Modify the download functions to change audio quality
- **Concurrent downloads**: Adjust `max_workers` in the ThreadPoolExecutor
- **UI customization**: Modify the Streamlit interface elements

## Deployment

### Local Development

For development, simply run:
```bash
streamlit run streamlit_app.py --server.runOnSave true
```

### Production Deployment

#### Streamlit Cloud

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Deploy with one click

#### Docker Deployment

Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t sixtyoneeighty-youtube2mp3 .
docker run -p 8501:8501 sixtyoneeighty-youtube2mp3
```

#### Heroku Deployment

1. Create a `Procfile`:
   ```
   web: streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. Deploy to Heroku:
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

## Troubleshooting

### Common Issues

1. **"libGL.so.1: cannot open shared object file"**
   - This error is resolved by using the Streamlit version instead of PyQt5
   - No additional system packages needed

2. **"Command not found: streamlit"**
   - Make sure you've activated your virtual environment
   - Ensure Streamlit is installed: `pip install streamlit`

3. **Download failures**
   - Check your internet connection
   - Verify the YouTube URL is valid and accessible
   - Some videos may be region-restricted or have download limitations

4. **iTunes metadata not working**
   - This is optional and the app will work without it
   - Check your internet connection for iTunes API access

### Performance Tips

- **For large playlists**: Consider downloading in smaller batches
- **Memory usage**: Close the browser tab when not in use to free memory
- **Network**: Ensure stable internet connection for best results

## Migration from PyQt5 Version

If you're migrating from the original PyQt5 version:

1. **Backup your data**: Save any important downloads
2. **Update dependencies**: Use the new `requirements.txt`
3. **Run Streamlit version**: Use `streamlit_app.py` instead of `main.py`
4. **No GUI installation needed**: No need for PyQt5, QDarkStyle, or system GUI libraries

## Dependencies

Key dependencies include:
- `streamlit`: Web application framework
- `pytube` & `pytubefix`: YouTube video downloading
- `moviepy`: Video/audio processing
- `mutagen`: Audio metadata handling
- `itunespy`: iTunes metadata fetching
- `pandas`: Data handling for the video table
- `requests`: HTTP requests

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project maintains the same license as the original PyQt5 version.

## Support

If you encounter issues:
1. Check this README for troubleshooting tips
2. Review the terminal output for error messages
3. Open an issue on GitHub with detailed error information

---

**Note**: The sixtyoneeighty YouTube to MP3 Converter Streamlit version resolves the OpenGL library issues encountered in headless environments and provides a modern, web-based interface that works across all platforms without additional system dependencies.