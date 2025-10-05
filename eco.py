import streamlit as st
import psutil
import time
import platform
from datetime import datetime


# Page configuration - MUST be the first Streamlit command
st.set_page_config(
    page_title="EcoSystem Monitor",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS for green eco theme with COMPACT LAYOUT
st.markdown("""
    <style>
    /* Main background with gradient */
    .stApp {
        background: linear-gradient(135deg, #1a4d2e 0%, #2d5a3d 50%, #1f3a29 100%);
    }
    
    /* COMPACT: Reduce all padding and margins */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }
    
    /* COMPACT: Reduce spacing between elements */
    .element-container {
        margin-bottom: 0.3rem !important;
    }
    
    div[data-testid="stVerticalBlock"] > div {
        padding: 0.3rem !important;
        margin-bottom: 0.2rem !important;
    }
    
    /* Metric containers - COMPACT */
    [data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
        color: #7FFF00;
        font-weight: bold;
    }
    
    [data-testid="stMetricLabel"] {
        color: #b8e6d5;
        font-size: 0.75rem !important;
    }
    
    /* COMPACT: Reduce metric padding */
    [data-testid="stMetric"] {
        padding: 0.2rem 0.5rem !important;
    }
    
    /* Headers - COMPACT */
    h1 {
        color: #a8e6cf !important;
        font-size: 1.8rem !important;
        margin: 0 !important;
        padding: 0.3rem 0 !important;
    }
    
    h2 {
        color: #a8e6cf !important;
        font-size: 1.2rem !important;
        margin: 0.3rem 0 !important;
        padding: 0.2rem 0 !important;
    }
    
    h3 {
        color: #a8e6cf !important;
        font-size: 1rem !important;
        margin: 0.2rem 0 !important;
        padding: 0.1rem 0 !important;
    }
    
    /* Progress bars - COMPACT */
    .stProgress {
        height: 0.4rem !important;
    }
    
    .stProgress > div > div > div {
        background-color: #7FFF00;
    }
    
    /* Sidebar - COMPACT */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f3a1f 0%, #1a4d2e 100%);
        padding: 0.5rem !important;
    }
    
    [data-testid="stSidebar"] .element-container {
        margin-bottom: 0.2rem !important;
    }
    
    /* Text - COMPACT */
    p, span, div {
        color: #d4f1e8;
        font-size: 0.85rem !important;
    }
    
    /* Info boxes - COMPACT */
    .stAlert {
        background-color: rgba(127, 255, 0, 0.1);
        border: 1px solid #7FFF00;
        padding: 0.3rem !important;
        font-size: 0.75rem !important;
    }
    
    /* Buttons - COMPACT */
    .stButton > button {
        background-color: #2d5a3d;
        color: #7FFF00;
        border: 2px solid #7FFF00;
        padding: 0.3rem 0.8rem !important;
        font-size: 0.8rem !important;
    }
    
    .stButton > button:hover {
        background-color: #7FFF00;
        color: #1a4d2e;
    }
    
    /* Horizontal rule - COMPACT */
    hr {
        margin: 0.3rem 0 !important;
    }
    
    /* Remove extra spacing from columns */
    [data-testid="column"] {
        padding: 0.2rem !important;
    }
    
    /* COMPACT: Smaller checkbox and slider */
    .stCheckbox, .stSlider {
        font-size: 0.8rem !important;
    }
    
    /* COMPACT: Hide scrollbar when content fits */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a4d2e;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #7FFF00;
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)


def get_cpu_info():
    """Get CPU usage and information"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_count = psutil.cpu_count(logical=False)
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        
        return {
            'percent': cpu_percent,
            'count': cpu_count if cpu_count else 0,
            'count_logical': cpu_count_logical if cpu_count_logical else 0,
            'freq_current': cpu_freq.current if cpu_freq else 0,
            'freq_max': cpu_freq.max if cpu_freq else 0
        }
    except Exception as e:
        return {
            'percent': 0,
            'count': 0,
            'count_logical': 0,
            'freq_current': 0,
            'freq_max': 0
        }


def get_memory_info():
    """Get RAM usage and information"""
    try:
        memory = psutil.virtual_memory()
        return {
            'total': memory.total / (1024**3),
            'available': memory.available / (1024**3),
            'used': memory.used / (1024**3),
            'percent': memory.percent
        }
    except Exception as e:
        return {
            'total': 0,
            'available': 0,
            'used': 0,
            'percent': 0
        }


def get_disk_info():
    """Get SSD/Disk usage information"""
    try:
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        return {
            'total': disk.total / (1024**3),
            'used': disk.used / (1024**3),
            'free': disk.free / (1024**3),
            'percent': disk.percent,
            'read_mb': disk_io.read_bytes / (1024**2) if disk_io else 0,
            'write_mb': disk_io.write_bytes / (1024**2) if disk_io else 0
        }
    except Exception as e:
        return {
            'total': 0,
            'used': 0,
            'free': 0,
            'percent': 0,
            'read_mb': 0,
            'write_mb': 0
        }


def estimate_power_consumption(cpu_percent, ram_percent, disk_percent):
    """Estimate power consumption in watts"""
    base_power = 30
    cpu_power = (cpu_percent / 100) * 65
    ram_power = (ram_percent / 100) * 8
    disk_power = (disk_percent / 100) * 5
    total_power = base_power + cpu_power + ram_power + disk_power
    return total_power


def calculate_eco_score(cpu_percent, ram_percent, disk_percent, power_watts):
    """Calculate eco carbon footprint score (1-10 scale)"""
    cpu_score = cpu_percent * 0.4
    ram_score = ram_percent * 0.25
    disk_score = disk_percent * 0.15
    power_score = min((power_watts / 150) * 100, 100) * 0.2
    total_score = cpu_score + ram_score + disk_score + power_score
    eco_score = min(max((total_score / 10), 1), 10)
    return round(eco_score, 1)


def get_eco_rating_message(score):
    """Get eco rating message based on score"""
    if score <= 3:
        return "🌟 Excellent", "#00FF00"
    elif score <= 5:
        return "🌿 Good", "#7FFF00"
    elif score <= 7:
        return "⚠️ Moderate", "#FFD700"
    elif score <= 8.5:
        return "🔶 High", "#FFA500"
    else:
        return "🔴 Critical", "#FF4500"


def estimate_carbon_emissions(power_watts, hours=1):
    """Estimate CO2 emissions"""
    energy_kwh = (power_watts / 1000) * hours
    co2_kg = energy_kwh * 0.475
    return co2_kg


# Main App
def main():
    # Compact Header
    st.markdown("# 🌱 EcoSystem Monitor")
    
    # Sidebar - COMPACT
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        auto_refresh = st.checkbox("🔄 Auto Refresh", value=True)
        refresh_interval = st.slider("Refresh (sec)", 1, 10, 2)
        st.markdown("---")
        st.markdown("### 📊 System")
        st.text(f"OS: {platform.system()}\nRelease: {platform.release()}")
        st.markdown("---")
        st.markdown("### 💡 Tips")
        st.info("💻 Close unused apps\n🔋 Power saving mode\n🌍 Lower brightness")
    
    # Create placeholder for dynamic updates
    placeholder = st.empty()
    
    # Main loop
    while True:
        with placeholder.container():
            # Get system information
            cpu_info = get_cpu_info()
            memory_info = get_memory_info()
            disk_info = get_disk_info()
            
            power_consumption = estimate_power_consumption(
                cpu_info['percent'], 
                memory_info['percent'], 
                disk_info['percent']
            )
            
            eco_score = calculate_eco_score(
                cpu_info['percent'],
                memory_info['percent'],
                disk_info['percent'],
                power_consumption
            )
            
            rating_msg, rating_color = get_eco_rating_message(eco_score)
            
            # COMPACT: Eco Score Row - Single Line
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
            
            with col1:
                st.markdown(f"<h2 style='color: {rating_color}; margin: 0;'>🌍 Eco Score: {eco_score}/10 {rating_msg}</h2>", unsafe_allow_html=True)
            
            with col2:
                st.metric("💡 Power", f"{power_consumption:.0f}W")
            
            with col3:
                co2_hour = estimate_carbon_emissions(power_consumption, 1)
                st.metric("☁️ CO₂/hr", f"{co2_hour*1000:.0f}g")
            
            with col4:
                co2_day = estimate_carbon_emissions(power_consumption, 24)
                st.metric("☁️ CO₂/day", f"{co2_day:.1f}kg")
            
            with col5:
                co2_year = estimate_carbon_emissions(power_consumption, 24*365)
                st.metric("☁️ CO₂/yr", f"{co2_year:.0f}kg")
            
            st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)
            
            # COMPACT: System Resources in 3 Columns
            col1, col2, col3 = st.columns(3)
            
            # CPU Section
            with col1:
                st.markdown("### 🔥 CPU")
                st.metric("Usage", f"{cpu_info['percent']:.0f}%")
                st.progress(cpu_info['percent'] / 100)
                
                cpu_col1, cpu_col2 = st.columns(2)
                with cpu_col1:
                    st.metric("Cores", f"{cpu_info['count']}")
                with cpu_col2:
                    st.metric("Logical", f"{cpu_info['count_logical']}")
                
                if cpu_info['freq_current'] > 0:
                    st.metric("Freq", f"{cpu_info['freq_current']:.0f}MHz")
            
            # RAM Section
            with col2:
                st.markdown("### 💾 RAM")
                st.metric("Usage", f"{memory_info['percent']:.0f}%")
                st.progress(memory_info['percent'] / 100)
                
                ram_col1, ram_col2 = st.columns(2)
                with ram_col1:
                    st.metric("Used", f"{memory_info['used']:.1f}GB")
                with ram_col2:
                    st.metric("Free", f"{memory_info['available']:.1f}GB")
                
                st.metric("Total", f"{memory_info['total']:.1f}GB")
            
            # Disk Section
            with col3:
                st.markdown("### 💿 Disk")
                st.metric("Usage", f"{disk_info['percent']:.0f}%")
                st.progress(disk_info['percent'] / 100)
                
                disk_col1, disk_col2 = st.columns(2)
                with disk_col1:
                    st.metric("Used", f"{disk_info['used']:.0f}GB")
                with disk_col2:
                    st.metric("Free", f"{disk_info['free']:.0f}GB")
                
                st.metric("Total", f"{disk_info['total']:.0f}GB")
            
            # COMPACT: Recommendations in single row
            st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)
            
            recommendations = []
            if cpu_info['percent'] > 70:
                recommendations.append("🔥 High CPU - Close apps")
            if memory_info['percent'] > 80:
                recommendations.append("💾 High RAM - Close tabs")
            if disk_info['percent'] > 85:
                recommendations.append("💿 Low disk space")
            if power_consumption > 100:
                recommendations.append("💡 High power - Enable saving mode")
            if eco_score > 7:
                recommendations.append("🌍 High footprint - Reduce usage")
            
            if recommendations:
                st.markdown(f"<p style='color: #FFD700; font-size: 0.85rem; margin: 0;'>⚠️ {' | '.join(recommendations)}</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='color: #7FFF00; font-size: 0.85rem; margin: 0;'>✅ System running efficiently!</p>", unsafe_allow_html=True)
            
            # Compact Timestamp
            st.markdown(f"<p style='text-align: center; color: #8db8a8; font-size: 0.7rem; margin-top: 0.3rem;'>Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>", unsafe_allow_html=True)
        
        if not auto_refresh:
            break
        
        time.sleep(refresh_interval)


if __name__ == "__main__":
    main()
