import streamlit as st
import pandas as pd
import os
import tempfile
import zipfile
from io import BytesIO
import time
import threading
from concurrent.futures import ThreadPoolExecutor

# Import utility functions
from utils.query_youtube import get_youtube_content
from utils.download_youtube import thread_query_youtube
from utils.query_itunes import get_itunes_metadata, query_itunes

# Page configuration
st.set_page_config(
    page_title="YouTube to Audio Converter - for Wheeler",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'videos_dict' not in st.session_state:
    st.session_state.videos_dict = {}
if 'download_progress' not in st.session_state:
    st.session_state.download_progress = {}
if 'is_downloading' not in st.session_state:
    st.session_state.is_downloading = False
if 'downloaded_files' not in st.session_state:
    st.session_state.downloaded_files = []
if 'selected_videos' not in st.session_state:
    st.session_state.selected_videos = set()

def format_duration(seconds):
    """Convert seconds to MM:SS format."""
    if seconds is None:
        return "Unknown"
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def load_youtube_content(url, override_error=True):
    """Load YouTube content and update session state."""
    try:
        with st.spinner("Fetching video information..."):
            videos_dict = get_youtube_content(url, override_error)
            st.session_state.videos_dict = videos_dict
            return True, "Videos loaded successfully!"
    except Exception as e:
        return False, f"Error loading videos: {str(e)}"

def annotate_with_itunes(videos_dict):
    """Annotate videos with iTunes metadata."""
    try:
        with st.spinner("Fetching iTunes metadata..."):
            annotated_dict = {}
            for title, video_info in videos_dict.items():
                try:
                    # Use the video URL to get iTunes metadata
                    video_url = f"https://www.youtube.com/watch?v={video_info['id']}"
                    itunes_data = get_itunes_metadata(video_url)
                    if itunes_data:
                        annotated_dict[title] = {
                            **video_info,
                            'artist': itunes_data.get('artist_name', 'Unknown Artist'),
                            'album': itunes_data.get('album_name', 'Unknown Album'),
                            'genre': itunes_data.get('primary_genre_name', 'Unknown Genre'),
                            'artwork_url': itunes_data.get('artwork_url_fullres', '')
                        }
                    else:
                        annotated_dict[title] = {
                            **video_info,
                            'artist': 'Unknown Artist',
                            'album': 'Unknown Album',
                            'genre': 'Unknown Genre',
                            'artwork_url': ''
                        }
                except Exception as e:
                    print(f"Error getting iTunes data for {title}: {e}")
                    annotated_dict[title] = {
                        **video_info,
                        'artist': 'Unknown Artist',
                        'album': 'Unknown Album',
                        'genre': 'Unknown Genre',
                        'artwork_url': ''
                    }
            return annotated_dict
    except Exception as e:
        st.error(f"Error fetching iTunes metadata: {str(e)}")
        return videos_dict

def download_videos(videos_dict, save_as_mp4=False):
    """Download videos using threading."""
    st.session_state.is_downloading = True
    st.session_state.downloaded_files = []
    
    # Create temporary directory for downloads
    temp_dir = tempfile.mkdtemp()
    mp4_temp_dir = tempfile.mkdtemp()
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_videos = len(videos_dict)
    completed = 0
    
    def download_single_video(item):
        nonlocal completed
        try:
            title, video_info = item
            song_properties = {
                'song': title,
                'artist': video_info.get('artist', 'Unknown Artist'),
                'album': video_info.get('album', 'Unknown Album'),
                'genre': video_info.get('genre', 'Unknown Genre'),
                'artwork_url': video_info.get('artwork_url', '')
            }
            
            args = [
                (title, video_info),
                (temp_dir, mp4_temp_dir),
                song_properties,
                save_as_mp4
            ]
            
            result = thread_query_youtube(args)
            
            completed += 1
            progress = completed / total_videos
            progress_bar.progress(progress)
            status_text.text(f"Downloaded: {title} ({completed}/{total_videos})")
            
            return result
            
        except Exception as e:
            st.error(f"Error downloading {title}: {str(e)}")
            completed += 1
            return None
    
    # Download videos using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(download_single_video, videos_dict.items()))
    
    # Collect downloaded files
    downloaded_files = []
    for filename in os.listdir(temp_dir):
        if filename.endswith(('.mp3', '.m4a')):
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'rb') as f:
                downloaded_files.append((filename, f.read()))
    
    st.session_state.downloaded_files = downloaded_files
    st.session_state.is_downloading = False
    
    # Clean up temp directories
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    shutil.rmtree(mp4_temp_dir, ignore_errors=True)
    
    return downloaded_files

def create_zip_download(files):
    """Create a ZIP file containing all downloaded audio files."""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, file_data in files:
            zip_file.writestr(filename, file_data)
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

# Main UI
st.title("🎵 sixtyoneeighty YouTube to MP3 Converter - for Wheeler")
st.markdown("Convert YouTube videos and playlists to high-quality MP3 files")

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    save_as_mp4 = st.checkbox("Save as MP4/M4A", value=False, help="Save as MP4/M4A instead of MP3")
    use_itunes = st.checkbox("Fetch iTunes Metadata", value=True, help="Automatically fetch artist, album, and genre information")
    
    st.header("📖 Instructions")
    st.markdown("""
    1. Enter a YouTube video or playlist URL
    2. Click 'Load Videos' to fetch video information
    3. Optionally annotate with iTunes metadata
    4. Select videos to download
    5. Click 'Download Selected' to convert to MP3
    """)

# URL input section
st.header("🔗 Enter YouTube URL")
col1, col2 = st.columns([4, 1])

with col1:
    url_input = st.text_input(
        "YouTube Video or Playlist URL",
        placeholder="https://www.youtube.com/watch?v=..",
        label_visibility="collapsed"
    )

with col2:
    load_button = st.button("Load Videos", type="primary", width="stretch")

# Load videos when button is clicked
if load_button and url_input:
    success, message = load_youtube_content(url_input)
    if success:
        st.success(message)
    else:
        st.error(message)

# Display videos table if videos are loaded
if st.session_state.videos_dict:
    st.header("📹 Loaded Videos")
    
    # iTunes annotation button
    if use_itunes:
        if st.button("🎼 Annotate with iTunes Metadata"):
            st.session_state.videos_dict = annotate_with_itunes(st.session_state.videos_dict)
            st.success("iTunes metadata added!")
    
    # Display videos with individual selection checkboxes
    for title, info in st.session_state.videos_dict.items():
        col1, col2 = st.columns([0.1, 0.9])
        
        with col1:
            is_selected = st.checkbox(
                "",
                value=title in st.session_state.selected_videos,
                key=f"select_{title}",
                label_visibility="collapsed"
            )
            
            if is_selected and title not in st.session_state.selected_videos:
                st.session_state.selected_videos.add(title)
            elif not is_selected and title in st.session_state.selected_videos:
                st.session_state.selected_videos.remove(title)
        
        with col2:
            st.markdown(f"**{title}**")
            col_info1, col_info2, col_info3, col_info4 = st.columns(4)
            with col_info1:
                st.caption(f"⏱️ {format_duration(info.get('duration'))}")
            with col_info2:
                st.caption(f"🎤 {info.get('artist', 'Unknown')}")
            with col_info3:
                st.caption(f"💿 {info.get('album', 'Unknown')}")
            with col_info4:
                st.caption(f"🎵 {info.get('genre', 'Unknown')}")
        
        st.markdown("---")
    
    # Selection and download section
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        if st.button("Select All", width="stretch"):
            st.session_state.selected_videos = set(st.session_state.videos_dict.keys())
            st.rerun()
    
    with col2:
        if st.button("Clear Selection", width="stretch"):
            st.session_state.selected_videos = set()
            st.rerun()
    
    with col3:
        if not st.session_state.is_downloading:
            download_button = st.button("🎵 Download Selected", type="primary", width="stretch")
        else:
            st.button("⏳ Downloading...", disabled=True, width="stretch")
    
    # Download functionality
    if 'download_button' in locals() and download_button:
        if st.session_state.selected_videos:
            # Filter videos_dict to only include selected videos
            selected_videos_dict = {title: info for title, info in st.session_state.videos_dict.items() 
                                  if title in st.session_state.selected_videos}
            
            with st.spinner("Preparing downloads..."):
                downloaded_files = download_videos(selected_videos_dict, save_as_mp4)
            
            if downloaded_files:
                st.success(f"Successfully downloaded {len(downloaded_files)} audio files!")
                
                # Create download buttons for individual files
                st.header("📥 Download Files")
                
                if len(downloaded_files) > 1:
                    # Create ZIP download for multiple files
                    zip_data = create_zip_download(downloaded_files)
                    st.download_button(
                        label="📦 Download All as ZIP",
                        data=zip_data,
                        file_name="youtube_audio_files.zip",
                        mime="application/zip",
                        width="stretch"
                    )
                    
                    st.markdown("---")
                    st.subheader("Individual Downloads")
                
                # Individual file downloads
                for filename, file_data in downloaded_files:
                    st.download_button(
                    label=f"📄 {filename}",
                    data=file_data,
                    file_name=filename,
                    mime="audio/mpeg" if filename.endswith('.mp3') else "audio/mp4",
                    width="stretch"
                )
            else:
                st.error("No files were successfully downloaded.")
        else:
            st.warning("Please select at least one video to download.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>Made with ❤️ using Streamlit | "
    "<a href='https://github.com/irahorecka/YouTube2Mp3' target='_blank'>Source Code</a></div>",
    unsafe_allow_html=True
)