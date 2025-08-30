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

# Custom CSS for modern styling
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Custom title styling */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #374151;
        margin: 2rem 0 1rem 0;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 0.5rem;
    }
    
    /* Card-like containers */
    .video-card {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.2s ease;
    }
    
    .video-card:hover {
        background: #f3f4f6;
        border-color: #d1d5db;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 6px;
        border: none;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 6px;
        border: 1px solid #d1d5db;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8fafc;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background-color: #3b82f6;
    }
    
    /* Video info styling */
    .video-info {
        display: flex;
        gap: 1rem;
        align-items: center;
        font-size: 0.9rem;
        color: #6b7280;
        margin-top: 0.5rem;
    }
    
    .video-title {
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

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
st.markdown('<h1 class="main-title">sixtyoneeighty - youtube to mp3 converter</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">(made for Wheeler)</p>', unsafe_allow_html=True)

# Sidebar for settings
with st.sidebar:
    st.markdown('<h3 class="section-header">Settings</h3>', unsafe_allow_html=True)
    save_as_mp4 = st.checkbox("Save as MP4/M4A", value=False, help="Save as MP4/M4A instead of MP3")
    use_itunes = st.checkbox("Fetch iTunes Metadata", value=True, help="Automatically fetch artist, album, and genre information")
    
    st.markdown('<h3 class="section-header">How to Use</h3>', unsafe_allow_html=True)
    st.markdown("""
    **1.** Enter a YouTube video or playlist URL  
    **2.** Click 'Load Videos' to fetch information  
    **3.** Optionally annotate with iTunes metadata  
    **4.** Select videos to download  
    **5.** Click 'Download Selected' to convert  
    """)

# URL input section
st.markdown('<h2 class="section-header">Enter YouTube URL</h2>', unsafe_allow_html=True)
col1, col2 = st.columns([4, 1])

with col1:
    url_input = st.text_input(
        "YouTube Video or Playlist URL",
        placeholder="https://www.youtube.com/watch?v=... or playlist URL",
        label_visibility="collapsed"
    )

with col2:
    load_button = st.button("Load Videos", type="primary", use_container_width=True)

# Load videos when button is clicked
if load_button and url_input:
    success, message = load_youtube_content(url_input)
    if success:
        st.success(message)
    else:
        st.error(message)

# Display videos table if videos are loaded
if st.session_state.videos_dict:
    st.markdown('<h2 class="section-header">Loaded Videos</h2>', unsafe_allow_html=True)
    
    # iTunes annotation button
    if use_itunes:
        if st.button("Annotate with iTunes Metadata", use_container_width=False):
            st.session_state.videos_dict = annotate_with_itunes(st.session_state.videos_dict)
            st.success("iTunes metadata added!")
    
    # Display videos with individual selection checkboxes
    for title, info in st.session_state.videos_dict.items():
        # Create a card-like container
        with st.container():
            col1, col2 = st.columns([0.08, 0.92])
            
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
                st.markdown(f'<div class="video-title">{title}</div>', unsafe_allow_html=True)
                
                # Video info in a clean layout
                info_col1, info_col2, info_col3, info_col4 = st.columns(4)
                with info_col1:
                    st.markdown(f"**Duration:** {format_duration(info.get('duration'))}")
                with info_col2:
                    st.markdown(f"**Artist:** {info.get('artist', 'Unknown')}")
                with info_col3:
                    st.markdown(f"**Album:** {info.get('album', 'Unknown')}")
                with info_col4:
                    st.markdown(f"**Genre:** {info.get('genre', 'Unknown')}")
        
        st.markdown("<br>", unsafe_allow_html=True)
    
    # Selection and download section
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        if st.button("Select All", use_container_width=True):
            st.session_state.selected_videos = set(st.session_state.videos_dict.keys())
            st.rerun()
    
    with col2:
        if st.button("Clear Selection", use_container_width=True):
            st.session_state.selected_videos = set()
            st.rerun()
    
    with col3:
        if not st.session_state.is_downloading:
            download_button = st.button("Download Selected", type="primary", use_container_width=True)
        else:
            st.button("Downloading...", disabled=True, use_container_width=True)
    
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
                st.markdown('<h2 class="section-header">Download Files</h2>', unsafe_allow_html=True)
                
                if len(downloaded_files) > 1:
                    # Create ZIP download for multiple files
                    zip_data = create_zip_download(downloaded_files)
                    st.download_button(
                        label="Download All as ZIP",
                        data=zip_data,
                        file_name="youtube_audio_files.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("**Individual Downloads**")
                    st.markdown("<br>", unsafe_allow_html=True)
                
                # Individual file downloads
                for filename, file_data in downloaded_files:
                    st.download_button(
                    label=filename,
                    data=file_data,
                    file_name=filename,
                    mime="audio/mpeg" if filename.endswith('.mp3') else "audio/mp4",
                    use_container_width=True
                )
            else:
                st.error("No files were successfully downloaded.")
        else:
            st.warning("Please select at least one video to download.")

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align: center; color: #9ca3af; font-size: 0.9rem; padding: 2rem 0; border-top: 1px solid #e5e7eb; margin-top: 3rem;'>"
    "sixtyoneeighty - youtube to mp3 converter (made for Wheeler) | "
    "<a href='https://github.com/irahorecka/YouTube2Mp3' target='_blank' style='color: #6366f1; text-decoration: none;'>View Source</a>"
    "</div>",
    unsafe_allow_html=True
)